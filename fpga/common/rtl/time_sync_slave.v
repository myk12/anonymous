`resetall
`timescale 1ns / 1ps
`default_nettype none

/*
 * Time synchronization slave module
 */
module time_sync_slave #
(
    parameter SYNC_TS_WIDTH = 16,
    parameter IDENTIFIER_WIDTH = 16,

    parameter AXIS_DATA_WIDTH = 64,
    parameter AXIS_KEEP_WIDTH = (AXIS_DATA_WIDTH/8),
    parameter AXIS_RX_ID_WIDTH = 8,
    parameter AXIS_RX_DEST_WIDTH = 8,
    parameter AXIS_RX_USER_WIDTH = 1,

    parameter SELF_ID = 123456
)
(
    input wire                              clk,
    input wire                              rst,

    // RX AXIS interface
    input wire [AXIS_DATA_WIDTH-1:0]        s_axis_sync_rx_data,
    input wire [AXIS_KEEP_WIDTH-1:0]        s_axis_sync_rx_keep,
    input wire                              s_axis_sync_rx_valid,
    output wire                             s_axis_sync_rx_ready,
    input wire                              s_axis_sync_rx_last,
    input wire [AXIS_RX_ID_WIDTH-1:0]       s_axis_sync_rx_id,
    input wire [AXIS_RX_DEST_WIDTH-1:0]     s_axis_sync_rx_dest,
    input wire [AXIS_RX_USER_WIDTH-1:0]     s_axis_sync_rx_user,

    // Enable PTP clock write
    output wire                             time_sync_wr_en,
    output wire [95:0]                      time_sync_wr_ts
);

// define the state machine
parameter STATE_IDLE = 0;
parameter STATE_RECV_DATA = 1;
parameter STATE_WRITE_TS = 2;
reg [2:0] state, next_state;

// Get the data from the AXIS interface
reg [AXIS_DATA_WIDTH-1:0]   sync_packet_data_reg;
reg [AXIS_KEEP_WIDTH-1:0]   sync_packet_keep_reg;
reg                         sync_packet_ready_reg;

reg [95:0]                  sync_time_stamp_reg;
reg [IDENTIFIER_WIDTH-1:0]  sync_dst_reg;
reg [IDENTIFIER_WIDTH-1:0]  sync_src_reg;
reg                         sync_valid;

reg                         time_sync_wr_en_reg;
reg [95:0]                  time_sync_wr_ts_reg;

assign s_axis_sync_rx_ready = sync_packet_ready_reg;
assign time_sync_wr_en      = time_sync_wr_en_reg;
assign time_sync_wr_ts      = time_sync_wr_ts_reg;

// state machine
always @(*) begin
    case (state)
        STATE_IDLE: begin
            // usually for AXIS interface, we need to check tlast signal
            // to determine the end of the packet, however, in this case
            // our packet only need one data, so we can ignore tlast signal
            if (s_axis_sync_rx_valid) begin
                next_state = STATE_RECV_DATA;
            end
            else begin
                next_state = STATE_IDLE;
            end
        end
        STATE_RECV_DATA: begin
            next_state = STATE_WRITE_TS;
        end
        STATE_WRITE_TS: begin
            next_state = STATE_IDLE;
        end
    endcase
end

// Get the data from the AXIS interface
always @(posedge clk) begin
    if (rst) begin
        state <= STATE_IDLE;

        sync_packet_data_reg    <= 0;
        sync_packet_keep_reg    <= 0;
        sync_packet_ready_reg   <= 1;

        sync_time_stamp_reg <= 0;
        sync_dst_reg        <= 0;
        sync_src_reg        <= 0;
        sync_valid          <= 0;

        time_sync_wr_en_reg <= 0;
        time_sync_wr_ts_reg <= 0;
    end
    else begin
        case (state)
            STATE_IDLE: begin
                sync_packet_data_reg <= s_axis_sync_rx_data;
                sync_packet_keep_reg <= s_axis_sync_rx_keep;
                sync_packet_ready_reg <= 1;

                sync_valid <= 0;

                sync_dst_reg <= 0;
                sync_src_reg <= 0;

                sync_time_stamp_reg <= 0;
                time_sync_wr_en_reg <= 0;
                time_sync_wr_ts_reg <= 0;
            end
            STATE_RECV_DATA: begin
                // check if the data is valid
                // format:
                // [15:0]: magic number
                // [31:16]: destination ID
                // [47:32]: source ID
                // [143:48]: timestamp
                sync_packet_ready_reg <= 0;
                if (sync_packet_data_reg[15:0] == 16'h77f8) begin
                    sync_valid      <= 1;
                    sync_dst_reg    <= sync_packet_data_reg[31:16];
                    sync_src_reg    <= sync_packet_data_reg[47:32];
                    sync_time_stamp_reg <= sync_packet_data_reg[143:48];
                end else begin
                    sync_valid      <= 0;

                    sync_dst_reg    <= 0;
                    sync_src_reg    <= 0;
                    sync_time_stamp_reg <= 0;
                end
            end
            STATE_WRITE_TS: begin
                if (sync_valid) begin
                    time_sync_wr_en_reg <= 1;
                    time_sync_wr_ts_reg <= sync_time_stamp_reg;
                end else begin
                    time_sync_wr_en_reg <= 0;
                    time_sync_wr_ts_reg <= 0;
                end
            end
            default: begin
                sync_packet_ready_reg <= 1;
            end
        endcase

        state <= next_state;
    end
end

endmodule
