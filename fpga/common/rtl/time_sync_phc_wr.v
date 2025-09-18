
module time_sync_phc_wr #(
    parameter IF_COUNT = 2
)
(
    input wire                                      clk,
    input wire                                      rst,
    /*
     * Write enable signal from Slave
     */
    input wire [IF_COUNT-1:0]                       sync_wr_en,
    input wire [IF_COUNT*96-1:0]                    sync_wr_ts,

    /*
    * Register interface
    */
    output wire                                     time_sync_wr_en,
    output wire [29:0]                              time_sync_wr_ns,
    output wire [47:0]                              time_sync_wr_s,
    input wire                                      time_sync_wr_ack
);

parameter STATE_IDLE = 0;
parameter STATE_WRITE_TS = 1;
parameter STATE_WAIT_ACK = 2;

reg [2:0] state, next_state;

reg [IF_COUNT-1:0]      sync_wr_en_reg;
reg [IF_COUNT*96-1:0]   sync_wr_ts_reg;
reg [95:0]              sync_wr_ts_single_reg;

reg time_sync_wr_en_reg;
reg [29:0] time_sync_wr_ns_reg;
reg [47:0] time_sync_wr_s_reg;

assign time_sync_wr_en = time_sync_wr_en_reg;
assign time_sync_wr_ns = time_sync_wr_ns_reg;
assign time_sync_wr_s = time_sync_wr_s_reg;

always @(*) begin
    case (state)
        STATE_IDLE: begin
            if (sync_wr_en != 0) begin
                next_state = STATE_WRITE_TS;
            end
            else begin
                next_state = STATE_IDLE;
            end
        end
        STATE_WRITE_TS: begin
            next_state = STATE_WAIT_ACK;
        end
        STATE_WAIT_ACK: begin
            if (time_sync_wr_ack != 0) begin
                next_state = STATE_IDLE;
            end
            else begin
                next_state = STATE_WAIT_ACK;
            end
        end
        default: begin
            next_state = STATE_IDLE;
        end
    endcase
end

always @(posedge clk or posedge rst) begin
    if (rst) begin
        state <= STATE_IDLE;
        sync_wr_en_reg <= 0;
        sync_wr_ts_reg <= 0;
        time_sync_wr_en_reg <= 0;
        time_sync_wr_ns_reg <= 0;
        time_sync_wr_s_reg <= 0;
    end
    else begin
        case (state)
            STATE_IDLE: begin
                sync_wr_en_reg <= sync_wr_en;
                sync_wr_ts_reg <= sync_wr_ts;
                time_sync_wr_en_reg <= 0;
                time_sync_wr_ns_reg <= 0;
                time_sync_wr_s_reg  <= 0;
            end
            STATE_WRITE_TS: begin
                time_sync_wr_en_reg <= 1;
                if (sync_wr_en_reg[0] == 1) begin
                    // SYNC signal from interface 0
                    time_sync_wr_ns_reg <= sync_wr_ts_reg[45:16]; // 30 bits from IF0 which is nano seconds
                    time_sync_wr_s_reg  <= sync_wr_ts_reg[95:48]; // 48 bits from IF0 which is seconds
                end else if (sync_wr_en_reg[1] == 1) begin
                    // SYNC signal from interface 1
                    time_sync_wr_ns_reg <= sync_wr_ts_reg[141:112]; // 30 bits from IF1 which is nano seconds
                    time_sync_wr_s_reg  <= sync_wr_ts_reg[191:144]; // 48 bits from IF1 which is seconds
                end else begin
                    // do nothing
                    time_sync_wr_ns_reg <= {30{1'b1}};
                    time_sync_wr_s_reg  <= {48{1'b1}};
                end
            end
            STATE_WAIT_ACK: begin
                // do nothing
            end
            default: begin
                // do nothing
            end
        endcase
        state <= next_state;
    end
end

endmodule
