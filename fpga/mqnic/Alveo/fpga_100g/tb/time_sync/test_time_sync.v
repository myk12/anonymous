`resetall
`timescale 1ns / 1ps
`default_nettype none

module test_time_sync #(

    /*
     * Structural configuration
     */
    parameter IF_COUNT = 1,
    parameter PORTS_PER_IF = 1,
    parameter SCHED_PER_IF = PORTS_PER_IF,

    /*
     * PTP configuration
     */
    parameter PTP_CLK_PERIOD_NS_NUM = 4,
    parameter PTP_CLK_PERIOD_NS_DENOM = 1,
    parameter PTP_CLOCK_PIPELINE = 0,
    parameter PTP_CLOCK_CDC_PIPELINE = 0,
    parameter PTP_SEPARATE_TX_CLOCK = 0,
    parameter PTP_SEPARATE_RX_CLOCK = 0,
    parameter PTP_PORT_CDC_PIPELINE = 0,
    parameter PTP_PEROUT_ENABLE = 0,
    parameter PTP_PEROUT_COUNT = 1,

    // AXI lite interface configuration parameters
    parameter AXIL_CTRL_DATA_WIDTH = 32,
    parameter AXIL_CTRL_ADDR_WIDTH = 16,
    parameter AXIL_CTRL_STRB_WIDTH = (AXIL_CTRL_DATA_WIDTH/8),
    parameter AXIL_IF_CTRL_ADDR_WIDTH = AXIL_CTRL_ADDR_WIDTH - $clog2(IF_COUNT),
    parameter AXIL_CSR_ADDR_WIDTH = AXIL_IF_CTRL_ADDR_WIDTH - 5 - $clog2((SCHED_PER_IF+4+7)/8),
    parameter AXIL_CSR_PASSTHROUGH_ENABLE = 0,
    parameter RB_NEXT_PTR = 0
)
(
    input wire                       clk,
    input wire                       rst,

    /*
     * PTP clock
     */
    input wire                          ptp_clk,
    input wire                          ptp_rst,
    input wire                          ptp_sample_clk,
    output wire                         ptp_td_sd,
    output wire                         ptp_pps,
    output wire                         ptp_pps_str,
    output wire                         ptp_sync_locked,
    output wire [63:0]                  ptp_sync_ts_rel,
    output wire                         ptp_sync_ts_rel_step,
    output wire [96:0]                  ptp_sync_ts_tod,
    output wire                         ptp_sync_ts_tod_step,
    output wire                         ptp_sync_pps,
    output wire                         ptp_sync_pps_str,
    output wire [PTP_PEROUT_COUNT-1:0]  ptp_perout_locked,
    output wire [PTP_PEROUT_COUNT-1:0]  ptp_perout_error,
    output wire [PTP_PEROUT_COUNT-1:0]  ptp_perout_pulse
);

localparam PHC_RB_BASE_ADDR = 32'h100;
localparam CLK_RB_BASE_ADDR = PHC_RB_BASE_ADDR + 32'h100;

/*********************** Net table **************************/
// time sync
wire [63:0]                             time_sync_ts_rel;
wire                                    time_sync_ts_rel_step;
wire [95:0]                             time_sync_ts_tod;
wire                                    time_sync_ts_tod_step;

wire                                    time_sync_pps;
wire                                    time_sync_pps_str;
wire                                    time_sync_locked;

wire [AXIL_CSR_ADDR_WIDTH-1:0]          time_sync_ptp_reg_wr_addr;
wire [AXIL_CTRL_DATA_WIDTH-1:0]         time_sync_ptp_reg_wr_data;
wire [AXIL_CTRL_STRB_WIDTH-1:0]         time_sync_ptp_reg_wr_strb;
wire                                    time_sync_ptp_reg_wr_en;
wire                                    time_sync_ptp_reg_wr_wait;
wire                                    time_sync_ptp_reg_wr_ack;

// ptp clock
// ctrl write interface
wire [AXIL_CSR_ADDR_WIDTH-1:0]          ptp_reg_wr_addr;
wire [AXIL_CTRL_DATA_WIDTH-1:0]         ptp_reg_wr_data;
wire [AXIL_CTRL_STRB_WIDTH-1:0]         ptp_reg_wr_strb;
wire                                    ptp_reg_wr_en;
wire                                    ptp_reg_wr_wait;
wire                                    ptp_reg_wr_ack;

// ctrl read interface
wire [AXIL_CSR_ADDR_WIDTH-1:0]          ptp_reg_rd_addr;
wire                                    ptp_reg_rd_en;
wire [AXIL_CTRL_DATA_WIDTH-1:0]         ptp_reg_rd_data;
wire                                    ptp_reg_rd_wait;
wire                                    ptp_reg_rd_ack;

wire                        ts_tod_wr_en;
wire [95:0]                 ts_tod_wr_ts;
wire                        ts_tod_wr_ack;

time_sync #(
    .PTP_CLOCK_CDC_PIPELINE(PTP_CLOCK_CDC_PIPELINE),
    .AXIL_CSR_ADDR_WIDTH(AXIL_CSR_ADDR_WIDTH),
    .AXIL_CTRL_DATA_WIDTH(AXIL_CTRL_DATA_WIDTH),
    .AXIL_CTRL_STRB_WIDTH(AXIL_CTRL_STRB_WIDTH),

    .REG_ADDR_WIDTH(AXIL_CTRL_ADDR_WIDTH),
    .CLK_RB_BASE_ADDR(CLK_RB_BASE_ADDR)
)
time_sync_inst(
    .clk(clk),
    .rst(rst),

    /*
     * PTP clock
     */
    .ptp_clk(ptp_clk),
    .ptp_rst(ptp_rst),
    .ptp_sample_clk(ptp_sample_clk),
    .ptp_td_sd(ptp_td_sd),

    .ts_tod_wr_en(ts_tod_wr_en),
    .ts_tod_wr_ts(ts_tod_wr_ts),
    .ts_tod_wr_ack(ts_tod_wr_ack),

    /*
     * Register write interface
     */
    .ptp_reg_wr_addr(time_sync_ptp_reg_wr_addr),
    .ptp_reg_wr_data(time_sync_ptp_reg_wr_data),
    .ptp_reg_wr_strb(time_sync_ptp_reg_wr_strb),
    .ptp_reg_wr_en(time_sync_ptp_reg_wr_en),
    .ptp_reg_wr_wait(time_sync_ptp_reg_wr_wait),
    .ptp_reg_wr_ack(time_sync_ptp_reg_wr_ack),

    /*
     * Timestamp output
     */
    .ptp_sync_ts_rel(time_sync_ts_rel),
    .ptp_sync_ts_rel_step(time_sync_ts_rel_step),
    .ptp_sync_ts_tod(time_sync_ts_tod),
    .ptp_sync_ts_tod_step(time_sync_ts_tod_step),
    
    /*
     * PPS output
     */
    .ptp_sync_pps(time_sync_pps),
    .ptp_sync_pps_str(time_sync_pps_str),

    /*
     * Lock output
     */
    .ptp_sync_locked(time_sync_locked)
);

mqnic_ptp #(
    .PTP_CLK_PERIOD_NS_NUM(PTP_CLK_PERIOD_NS_NUM),
    .PTP_CLK_PERIOD_NS_DENOM(PTP_CLK_PERIOD_NS_DENOM),
    .PTP_CLOCK_CDC_PIPELINE(PTP_CLOCK_CDC_PIPELINE),
    .PTP_PEROUT_ENABLE(PTP_PEROUT_ENABLE),
    .PTP_PEROUT_COUNT(PTP_PEROUT_COUNT),
    .REG_ADDR_WIDTH(AXIL_CTRL_ADDR_WIDTH),
    .REG_DATA_WIDTH(AXIL_CTRL_DATA_WIDTH),
    .REG_STRB_WIDTH(AXIL_CTRL_STRB_WIDTH),
    .RB_BASE_ADDR(CLK_RB_BASE_ADDR),
    .RB_NEXT_PTR(RB_NEXT_PTR)
)
mqnic_ptp_inst(
    .clk(clk),
    .rst(rst),

    /*
     * Register interface
     */
    .reg_wr_addr(ptp_reg_wr_addr),
    .reg_wr_data(ptp_reg_wr_data),
    .reg_wr_strb(ptp_reg_wr_strb),
    .reg_wr_en(ptp_reg_wr_en),
    .reg_wr_wait(ptp_reg_wr_wait),
    .reg_wr_ack(ptp_reg_wr_ack),
    .reg_rd_addr(ptp_reg_rd_addr),
    .reg_rd_en(ptp_reg_rd_en),
    .reg_rd_data(ptp_reg_rd_data),
    .reg_rd_wait(ptp_reg_rd_wait),
    .reg_rd_ack(ptp_reg_rd_ack),

    /*
     * Register write
     */
    .reg_wr_addr_1(time_sync_ptp_reg_wr_addr),
    .reg_wr_data_1(time_sync_ptp_reg_wr_data),
    .reg_wr_strb_1(time_sync_ptp_reg_wr_strb),
    .reg_wr_en_1(time_sync_ptp_reg_wr_en),
    .reg_wr_wait_1(time_sync_ptp_reg_wr_wait),
    .reg_wr_ack_1(time_sync_ptp_reg_wr_ack),
    
    /*
     * PTP clock
     */
    .ptp_clk(ptp_clk),
    .ptp_rst(ptp_rst),
    .ptp_sample_clk(ptp_sample_clk),
    .ptp_td_sd(ptp_td_sd),
    .ptp_pps(ptp_pps),
    .ptp_pps_str(ptp_pps_str),
    .ptp_sync_locked(ptp_sync_locked),
    .ptp_sync_ts_rel(ptp_sync_ts_rel),
    .ptp_sync_ts_rel_step(ptp_sync_ts_rel_step),
    .ptp_sync_ts_tod(ptp_sync_ts_tod),
    .ptp_sync_ts_tod_step(ptp_sync_ts_tod_step),
    .ptp_sync_pps(ptp_sync_pps),
    .ptp_sync_pps_str(ptp_sync_pps_str),
    .ptp_perout_locked(ptp_perout_locked),
    .ptp_perout_error(ptp_perout_error),
    .ptp_perout_pulse(ptp_perout_pulse)
);



endmodule

`resetall