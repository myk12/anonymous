`resetall
`timescale 1ns / 1ps
`default_nettype none

/*
 * Time synchronization module
 */
module time_sync #
(
    parameter PTP_CLOCK_CDC_PIPELINE = 1,
    parameter AXIL_CSR_ADDR_WIDTH = 16,
    parameter AXIL_CTRL_DATA_WIDTH = 32,
    parameter AXIL_CTRL_STRB_WIDTH = 4,

    // time sync scheduler parameters
    parameter SYNC_TABLE_SIZE = 512,
    parameter SYNC_TS_WIDTH = 32,
    parameter IDENTIFIER_WIDTH = 16,
    parameter PORT_ID_WIDTH = 4,

    parameter SYNC_START_TIME = 60000, // 60us
    parameter SYNC_PERIOD = 1000000, // 1ms

    parameter REG_ADDR_WIDTH = 7,
    parameter CLK_RB_BASE_ADDR = 0,

    // interface parameters
    parameter IF_COUNT = 2,
    parameter PORTS_PER_IF = 1, // TODO: now only 1 port per interface
    parameter AXIS_DATA_WIDTH = 64,
    parameter AXIS_KEEP_WIDTH = (AXIS_DATA_WIDTH/8),
    parameter AXIS_TX_ID_WIDTH = 8,
    parameter AXIS_TX_DEST_WIDTH = 8,
    parameter AXIS_TX_USER_WIDTH = 1,

    parameter AXIS_RX_ID_WIDTH = 8,
    parameter AXIS_RX_DEST_WIDTH = 8,
    parameter AXIS_RX_USER_WIDTH = 1,

    // Self ID
    parameter SELF_ID = 123456
)
(
    input wire                                      clk,
    input wire                                      rst,
    
    /*
     * PTP clock
     */
    input wire                                      ptp_clk,
    input wire                                      ptp_rst,
    input wire                                      ptp_sample_clk,
    input wire                                      ptp_td_sd,

    /*
     * Write new timestamp
     */
    input wire [95:0]                               ts_tod_wr_ts,
    input wire                                      ts_tod_wr_en,
    output wire                                     ts_tod_wr_ack,

    /*
     * PTP Clock write interface
     */
    output wire                                     time_sync_wr_en,
    output wire [29:0]                              time_sync_wr_ns,
    output wire [47:0]                              time_sync_wr_s,
    input wire                                      time_sync_wr_ack,

    /*
     * Master TX Data
     */
    output wire [IF_COUNT*AXIS_DATA_WIDTH-1:0]      m_axis_time_sync_data,
    output wire [IF_COUNT*AXIS_KEEP_WIDTH-1:0]      m_axis_time_sync_keep,
    output wire [IF_COUNT:0]                        m_axis_time_sync_valid,
    input  wire [IF_COUNT:0]                        m_axis_time_sync_ready,
    output wire [IF_COUNT:0]                        m_axis_time_sync_last,
    output wire [IF_COUNT*AXIS_TX_ID_WIDTH-1:0]     m_axis_time_sync_id,
    output wire [IF_COUNT*AXIS_TX_DEST_WIDTH-1:0]   m_axis_time_sync_dest,
    output wire [IF_COUNT*AXIS_TX_USER_WIDTH-1:0]   m_axis_time_sync_user,

    /*
     * Master TX Checksum Command
     */
    output wire [IF_COUNT:0]                        time_sync_tx_csum_cmd_csum_enable,
    output wire [IF_COUNT*8-1:0]                    time_sync_tx_csum_cmd_csum_start,
    output wire [IF_COUNT*8-1:0]                    time_sync_tx_csum_cmd_csum_offset,
    output wire [IF_COUNT:0]                        time_sync_tx_csum_cmd_valid,
    input  wire [IF_COUNT:0]                        time_sync_tx_csum_cmd_ready,

    /*
     * Slave RX Data
     */
    input wire [IF_COUNT*AXIS_DATA_WIDTH-1:0]       s_axis_time_sync_data,
    input wire [IF_COUNT*AXIS_KEEP_WIDTH-1:0]       s_axis_time_sync_keep,
    input wire [IF_COUNT:0]                         s_axis_time_sync_valid,
    output wire [IF_COUNT:0]                        s_axis_time_sync_ready,
    input wire [IF_COUNT:0]                         s_axis_time_sync_last,
    input wire [IF_COUNT*AXIS_TX_ID_WIDTH-1:0]      s_axis_time_sync_id,
    input wire [IF_COUNT*AXIS_TX_DEST_WIDTH-1:0]    s_axis_time_sync_dest,
    input wire [IF_COUNT*AXIS_TX_USER_WIDTH-1:0]    s_axis_time_sync_user
);

localparam RBB = CLK_RB_BASE_ADDR & {REG_ADDR_WIDTH{1'b1}};

// get timestamp from ptp td leaf
// ptp td leaf instance
// sync to core clock domain
wire [63:0] ptp_ts_rel;
wire        ptp_ts_rel_step;
wire [95:0] ptp_ts_tod;
wire        ptp_locked;
wire        ptp_pps;
wire        ptp_pps_str;

ptp_td_leaf #(
    .TS_REL_EN(1),
    .TS_TOD_EN(1),
    .TS_FNS_W(16),
    .TS_REL_NS_W(48),
    .TS_TOD_S_W(48),
    .TS_REL_W(64),
    .TS_TOD_W(96),
    .TD_SDI_PIPELINE(PTP_CLOCK_CDC_PIPELINE)
)
ptp_td_leaf_inst (
    .clk(clk),
    .rst(rst),
    .sample_clk(ptp_sample_clk),

    /*
     * PTP clock interface
     */
    .ptp_clk(ptp_clk),
    .ptp_rst(ptp_rst),
    .ptp_td_sdi(ptp_td_sd),

    /*
     * Timestamp output
     */
    .output_ts_rel(ptp_ts_rel),
    .output_ts_rel_step(ptp_ts_rel_step),
    .output_ts_tod(ptp_ts_tod),
    .output_ts_tod_step(ptp_ts_rel_step),

    /*
     * PPS output (ToD format only)
     */
    .output_pps(ptp_pps),
    .output_pps_str(ptp_pps_str),

    /*
     * Status
     */
    .locked(ptp_locked)
);

/***********************************************************************
 *                       Scheduler Module                              *
 ***********************************************************************/
// time sync scheduler signals
wire [IF_COUNT-1:0]                     sync_master_enable;
wire [IF_COUNT*IDENTIFIER_WIDTH-1:0]    sync_dest_id;

// instantiate time sync scheduler
time_sync_scheduler #(
    .SYNC_TABLE_SIZE(SYNC_TABLE_SIZE),
    .SYNC_TS_WIDTH(SYNC_TS_WIDTH),
    .IDENTIFIER_WIDTH(IDENTIFIER_WIDTH),
    .PORT_ID_WIDTH(PORT_ID_WIDTH),

    // sync period
    .SYNC_START(SYNC_START_TIME),
    .SYNC_PERIOD(SYNC_PERIOD)
)
time_sync_scheduler_inst(
    .clk(clk),
    .rst(rst),

    .ptp_ts_tod(ptp_ts_tod),

    .sync_enable_out(sync_master_enable),
    .sync_dest_id(sync_dest_id)
);

/***********************************************************************
 *                       Time Sync Master/Slave                        *
 ***********************************************************************/
// For each interface, instantiate time sync master and slave
genvar i;
generate
for (i = 0; i < IF_COUNT; i = i + 1) begin : time_sync_gen

    // instantiate time sync master
    time_sync_master #
    (
        .SYNC_TS_WIDTH(SYNC_TS_WIDTH),
        .IDENTIFIER_WIDTH(IDENTIFIER_WIDTH),

        .SELF_ID(SELF_ID),

        .AXIS_DATA_WIDTH(AXIS_DATA_WIDTH),
        .AXIS_KEEP_WIDTH(AXIS_KEEP_WIDTH),
        .AXIS_TX_ID_WIDTH(AXIS_TX_ID_WIDTH),
        .AXIS_TX_DEST_WIDTH(AXIS_TX_DEST_WIDTH),
        .AXIS_TX_USER_WIDTH(AXIS_TX_USER_WIDTH)
    )
    time_sync_master_inst(
        .clk(clk),
        .rst(rst),

        .ptp_ts_tod(ptp_ts_tod),

        .sync_enable(sync_master_enable[i]),
        .sync_dest_id(sync_dest_id[i*IDENTIFIER_WIDTH +: IDENTIFIER_WIDTH]),

        .m_axis_sync_tx_data(m_axis_time_sync_data[i*AXIS_DATA_WIDTH +: AXIS_DATA_WIDTH]),
        .m_axis_sync_tx_keep(m_axis_time_sync_keep[i*AXIS_KEEP_WIDTH +: AXIS_KEEP_WIDTH]),
        .m_axis_sync_tx_valid(m_axis_time_sync_valid[i]),
        .m_axis_sync_tx_ready(m_axis_time_sync_ready[i]),
        .m_axis_sync_tx_last(m_axis_time_sync_last[i]),
        .m_axis_sync_tx_id(m_axis_time_sync_id[i*AXIS_TX_ID_WIDTH +: AXIS_TX_ID_WIDTH]),
        .m_axis_sync_tx_dest(m_axis_time_sync_dest[i*AXIS_TX_DEST_WIDTH +: AXIS_TX_DEST_WIDTH]),
        .m_axis_sync_tx_user(m_axis_time_sync_user[i*AXIS_TX_USER_WIDTH +: AXIS_TX_USER_WIDTH]),

        .sync_tx_csum_cmd_csum_enable(time_sync_tx_csum_cmd_csum_enable[i]),
        .sync_tx_csum_cmd_csum_start(time_sync_tx_csum_cmd_csum_start[i*8 +: 8]),
        .sync_tx_csum_cmd_csum_offset(time_sync_tx_csum_cmd_csum_offset[i*8 +: 8]),
        .sync_tx_csum_cmd_valid(time_sync_tx_csum_cmd_valid[i]),
        .sync_tx_csum_cmd_ready(time_sync_tx_csum_cmd_ready[i])
    );

    // TimeSYNC Slave instance
    time_sync_slave #(
        .SYNC_TS_WIDTH(SYNC_TS_WIDTH),
        .IDENTIFIER_WIDTH(IDENTIFIER_WIDTH),

        .AXIS_DATA_WIDTH(AXIS_DATA_WIDTH),
        .AXIS_KEEP_WIDTH(AXIS_KEEP_WIDTH),
        .AXIS_RX_ID_WIDTH(AXIS_RX_ID_WIDTH),
        .AXIS_RX_DEST_WIDTH(AXIS_RX_DEST_WIDTH),
        .AXIS_RX_USER_WIDTH(AXIS_RX_USER_WIDTH),

        .SELF_ID(SELF_ID)
    )
    time_sync_slave_inst(
        .clk(clk),
        .rst(rst),

        // RX AXIS interface
        .s_axis_sync_rx_data(s_axis_time_sync_data[i*AXIS_DATA_WIDTH +: AXIS_DATA_WIDTH]),
        .s_axis_sync_rx_keep(s_axis_time_sync_keep[i*AXIS_KEEP_WIDTH +: AXIS_KEEP_WIDTH]),
        .s_axis_sync_rx_valid(s_axis_time_sync_valid[i]),
        .s_axis_sync_rx_ready(s_axis_time_sync_ready[i]),
        .s_axis_sync_rx_last(s_axis_time_sync_last[i]),
        .s_axis_sync_rx_id(s_axis_time_sync_id[i*AXIS_TX_ID_WIDTH +: AXIS_TX_ID_WIDTH]),
        .s_axis_sync_rx_dest(s_axis_time_sync_dest[i*AXIS_TX_DEST_WIDTH +: AXIS_TX_DEST_WIDTH]),
        .s_axis_sync_rx_user(s_axis_time_sync_user[i*AXIS_TX_USER_WIDTH +: AXIS_TX_USER_WIDTH]),

        // Enable PTP clock write
        .time_sync_wr_en(slave_sync_wr_en[i]),
        .time_sync_wr_ts(slave_sync_wr_ts[i*96 +: 96])
    );

end
endgenerate

/***********************************************************************
 *                       PTP Clock write interface                     *
 ***********************************************************************/
wire [IF_COUNT-1:0]         slave_sync_wr_en;
wire [IF_COUNT*96-1:0]      slave_sync_wr_ts;

// time sync phc rw instance

 time_sync_phc_wr #(
    .IF_COUNT(IF_COUNT)
)
time_sync_phc_wr_inst (
    .clk(clk),
    .rst(rst),

    /*
     * Write enable
     */
    .sync_wr_en(slave_sync_wr_en),
    .sync_wr_ts(slave_sync_wr_ts),

    /*
     * Register interface
     */
    .time_sync_wr_en(time_sync_wr_en),
    .time_sync_wr_ns(time_sync_wr_ns),
    .time_sync_wr_s(time_sync_wr_s),
    .time_sync_wr_ack(time_sync_wr_ack)
);


endmodule