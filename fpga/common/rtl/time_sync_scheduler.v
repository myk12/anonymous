`resetall
`timescale 1ns / 1ps
`default_nettype none

/*
 * @brief: Time synchronization scheduler
 *
 * @detail: This is a time synchronization scheduler module that schedules time synchronization signals
 *          to the time synchronization master module. It receives the timestamp from the PTP and matches
 *          it with the sync table to generate the sync_enable_out, sync_dest_id, and sync_dest_port signals.
 *
*/

module time_sync_scheduler #
(
    // NIC parameters
    parameter IF_COUNT = 2,

    // sync table: time, dest, port
    parameter SYNC_TABLE_SIZE = 512,
    parameter SYNC_TS_WIDTH = 32,
    parameter IDENTIFIER_WIDTH = 16,
    parameter PORT_ID_WIDTH = 4,
    
    // sync period
    parameter SYNC_START = 60000, // 60us
    parameter SYNC_PERIOD = 1000000 // 1ms
)
(
    input wire                                      clk,
    input wire                                      rst,

    // time stamp input
    input wire [95:0]                               ptp_ts_tod,

    // master sync output
    output reg [IF_COUNT-1:0]                       sync_enable_out,
    output reg [IF_COUNT*IDENTIFIER_WIDTH-1:0]      sync_dest_id

    // TODO: sync table read/write interface
);

//***************************************************************************************
//              Define the Sync table
//***************************************************************************************

// The key data structure in this module is the sync table that contains the timestamp, destination and port:
// - timestamp: 16-bit timestamp, the time when the synchronization signal should be sent
// - destination: 16-bit destination ID, the ID of the destination that should receive the synchronization signal
// - port: 4-bit port ID, the ID of the port (interface) that should send the synchronization signal

reg [SYNC_TS_WIDTH-1:0]         sync_table_ts [0:SYNC_TABLE_SIZE-1];
reg [IDENTIFIER_WIDTH-1:0]      sync_table_dest_id [0:SYNC_TABLE_SIZE-1];
reg [PORT_ID_WIDTH-1:0]         sync_table_port [0:SYNC_TABLE_SIZE-1];

// Initialize the sync table
// TODO: In the future, this should be done by the software running on the host
// For now, we will initialize the sync table with some default values
integer i;
always @(posedge rst) begin
    if (rst) begin
        // Initialize sync_table_ts with values from 60000ns increasing by 1000ns
        for (i = 0; i < SYNC_TABLE_SIZE; i = i + 1) begin
            sync_table_ts[i]        <= SYNC_START + i * SYNC_PERIOD;
            sync_table_dest_id[i]   <= 16'h1176; // TODO: Since we only have one device, we will use a fixed destination ID, which is ourself.
            sync_table_port[i]      <= 4'h0; // TODO: Since we only have one port, we will use a fixed port ID.
        end
    end
    else
    begin
        // Matinain the sync table
        for (i = 0; i < SYNC_TABLE_SIZE; i = i + 1) begin
            sync_table_ts[i]        <= sync_table_ts[i];
            sync_table_dest_id[i]   <= sync_table_dest_id[i];
            sync_table_port[i]      <= sync_table_port[i];
        end
    end
end

// Calculate clog2 manually for sync table pointer width
function integer clog2;
    input integer value;
    integer i;
    begin
        clog2 = 0;
        for (i = value - 1; i > 0; i = i >> 1)
            clog2 = clog2 + 1;
    end
endfunction

parameter SYNC_TABLE_PTR_WIDTH = clog2(SYNC_TABLE_SIZE);
reg [SYNC_TABLE_PTR_WIDTH-1:0] sync_table_ptr;

//***************************************************************************************
//              Time synchronization scheduler
//***************************************************************************************

// The time synchronization scheduler schedules the synchronization signals to the time synchronization master module.
// It receives the timestamp from the PTP and matches it with the sync table to generate the sync_enable_out, sync_dest_id signals.
// The format of the ToD timestamp is 96-bit, where the lower 16 bits are the fractional part , the next 32 bits are the nanoseconds part, 
// the next 48 bits are the seconds part.
// 
// PTP cur fns: ptp_ts_tod[15:0]
// PTP cur ns: ptp_ts_tod[47:16]
// PTP cur sec l: ptp_ts_tod[79:48]
// PTP cur sec h: ptp_ts_tod[95:80]
//
// Here we only use the nanoseconds part to compare with the sync table timestamp.

always @(posedge clk or posedge rst) begin
    if (rst) begin
        sync_enable_out <= 0;
        sync_dest_id <= 0;
        sync_table_ptr <= 0;
    end else begin
        // Check if the current timestamp matches the timestamp in the sync table
        // TODO: I am not sure if there is a better way to compare the timestamps
        // or if this is the correct way to do it without logic errors.
        if (ptp_ts_tod[47:16] >= sync_table_ts[sync_table_ptr]) begin
            // Set the sync_enable_out, sync_dest_id, and sync_dest_port signals
            // according to the destination port
            sync_enable_out[sync_table_port[sync_table_ptr]] <= 1;
            sync_dest_id[sync_table_port[sync_table_ptr]*IDENTIFIER_WIDTH +: IDENTIFIER_WIDTH] <= sync_table_dest_id[sync_table_ptr];
        end else begin
            sync_enable_out <= 0;
            sync_dest_id <= 0;
        end
        
        // Increment the sync table pointer
        if (sync_table_ptr == SYNC_TABLE_SIZE-1) begin
            sync_table_ptr <= 0;
        end else begin
            sync_table_ptr <= sync_table_ptr + 1;
        end

    end
end

endmodule