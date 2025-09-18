import logging
import os
import sys
import time

from decimal import Decimal, getcontext

import cocotb_test.simulator
import pytest

import cocotb
from cocotb.log import SimLog
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, Event, ReadOnly

#import cocotb binary
from cocotb.binary import BinaryValue

class TB(object):
    def __init__(self, dut) -> None:
        self.dut = dut
        
        self.log = SimLog("cocotb.tb")
        self.log.setLevel(logging.DEBUG)
        
        self.log.info("Initializing testbench")

    async def init(self):
        # start system clock 250 MHz
        cocotb.start_soon(Clock(self.dut.clk, 4, units="ns").start())

        # start ptp clock
        cocotb.start_soon(Clock(self.dut.ptp_clk, 6.206, units="ns").start())
        
        # start ptp sample clock
        cocotb.start_soon(Clock(self.dut.ptp_sample_clk, 8, units="ns").start())
        
        # reset the DUT
        self.dut.rst.setimmediatevalue(1)
        self.dut.ptp_rst.setimmediatevalue(1)
        await Timer(100, units="ns")
        self.dut.rst.setimmediatevalue(0)
        self.dut.ptp_rst.setimmediatevalue(0)

        await Timer(100, units="ns")

def tod_to_ns(binary_value):
    if not isinstance(binary_value, BinaryValue) or len(binary_value.binstr) != 96:
        raise ValueError("The input must be a BinaryValue object with a 96-bit long binary string")
    #print(binary_value)
    ptp_sync_ts_tod = binary_value.binstr
    print(ptp_sync_ts_tod)
    fns_bin = ptp_sync_ts_tod[80:96]
    ns_bin = ptp_sync_ts_tod[48:80]
    sec_bin = ptp_sync_ts_tod[0:48]
    
    # 将二进制字符串转换为整数
    fns = int(fns_bin, 2)
    ns = int(ns_bin, 2)
    sec = int(sec_bin, 2)
    print("fns: %d" % fns)
    print("ns: %d" % ns)
    print("sec: %d" % sec)
    
    ctx = getcontext()
    ctx.prec = 10
    
    nanoseconds = Decimal(fns) / Decimal(2**16)
    nanoseconds = ctx.add(nanoseconds, Decimal(ns))
    nanoseconds = ctx.add(nanoseconds, Decimal(sec).scaleb(9))

    return nanoseconds

@cocotb.test()
async def run_test_ptp(dut):
    tb = TB(dut)
    
    await tb.init()
    
    tb.log.info("Testbench initialized")
    
    #await Timer(10000, units="ns")
    
    # smaple the ptp tod ts
    async def sample_tod():
        while True:
            await RisingEdge(dut.ptp_clk)
            print(f"tod: {dut.ptp_sync_ts_tod.value}")
    
    async def sample_ts_rel():
        while True:
            await RisingEdge(dut.ptp_clk)
            print(f"ts_rel: {dut.ptp_sync_ts_rel.value}")
            
    async def sample_register():
        counter = 0
        while True:
            await RisingEdge(dut.ptp_clk)
            print(f"td_update_reg[%d]: {dut.mqnic_ptp_inst.ptp_clock_inst.ptp_td_phc_inst.td_update_reg.value}" % counter)
            print(f"ts_tod_ns_reg[%d]: {dut.mqnic_ptp_inst.ptp_clock_inst.ptp_td_phc_inst.ts_tod_ns_reg.value}" % counter)
            counter += 1
    
    #cocotb.start_soon(sample_tod())
    #cocotb.start_soon(sample_ts_rel())
    #cocotb.start_soon(sample_register())
    for i in range(10):
        # wait for 256 ptp_clk cycles
        for i in range(256):
            await RisingEdge(dut.ptp_clk)
        tb.log.info("Triggering PTP sync")
        # print ts tod
        #print(f"ptp tod         : %s" % tod_to_ns(dut.ptp_sync_ts_tod.value))
        print(f"time sync tod   : %s" % tod_to_ns(dut.time_sync_ts_tod.value))
    
    print("Setting time sync tod")
    # set the time sync tod
    dut.ts_tod_wr_en.setimmediatevalue(1)
    dut.ts_tod_wr_ts.setimmediatevalue(0x0000000100000001)

    # wait until ack is set
    if not dut.ts_tod_wr_ack.value:
        await RisingEdge(dut.ptp_clk)
    
    print("Clearing time sync tod")
    
    # clear the write enable
    dut.ts_tod_wr_en.setimmediatevalue(0)
    
    # wait for 256 ptp_clk cycles
    for i in range(10):
        # wait for 256 ptp_clk cycles
        for i in range(256):
            await RisingEdge(dut.ptp_clk)
        tb.log.info("Triggering PTP sync")
        # print ts tod
        #print(f"ptp tod         : %s" % tod_to_ns(dut.ptp_sync_ts_tod.value))
        print(f"time sync tod   : %s" % tod_to_ns(dut.time_sync_ts_tod.value))
    
    tb.log.info("Testbench finished")


test_dir = os.path.dirname(__file__)
rtl_dir = os.path.abspath(os.path.join(test_dir, os.pardir, os.pardir, "rtl"))
lib_dir = os.path.abspath(os.path.join(test_dir, os.pardir, os.pardir, "lib"))
eth_rtl_dir = os.path.abspath(os.path.join(lib_dir, "eth", "rtl"))

@pytest.mark.parametrize(("if_cnt", "ports_per_if", "sched_per_if"), [
    (1, 1, 1)
])

def test_time_sync(request, if_cnt, ports_per_if, sched_per_if):
    dut = "time_sync"
    module = os.path.splitext(os.path.basename(__file__))[0]
    toplevel = f"test_{dut}"

    verilog_sources = [
        os.path.join(test_dir, f"{toplevel}.v"),
        os.path.join(rtl_dir, f"{dut}.v"),
        os.path.join(rtl_dir, "common", "mqnic_ptp.v"),
        os.path.join(rtl_dir, "common", "mqnic_ptp_clock.v"),
        os.path.join(rtl_dir, "common", "mqnic_ptp_perout.v"),
        os.path.join(eth_rtl_dir, "ptp_td_phc.v"),
        os.path.join(eth_rtl_dir, "ptp_td_leaf.v"),
        os.path.join(eth_rtl_dir, "ptp_perout.v")
    ]
    
    parameters = {}

    # Structural parameters
    parameters['IF_COUNT'] = if_cnt
    parameters['PORTS_PER_IF'] = ports_per_if
    parameters['SCHED_PER_IF'] = sched_per_if
    
    # Clock configuration
    #parameters['CLK_PERIOD_NS_NUM'] = 4
    #parameters['CLK_PERIOD_NS_DEN'] = 1
    
    # PTP configuration
    parameters['PTP_CLK_PERIOD_NS_NUM'] = 1024
    parameters['PTP_CLK_PERIOD_NS_DENOM'] = 165
    parameters['PTP_CLOCK_PIPELINE'] = 0
    parameters['PTP_CLOCK_CDC_PIPELINE'] = 0
    parameters['PTP_PORT_CDC_PIPELINE'] = 0
    #parameters['PTP_PEROUT_ENABLE'] = 0
    #parameters['PTP_PEROUT_COUNT'] = 1
    
    # AXI lite interface configuration (control)
    parameters['AXIL_CTRL_DATA_WIDTH'] = 32
    parameters['AXIL_CTRL_ADDR_WIDTH'] = 24
    
    extra_env = {f"PARAM_{k}": str(v) for k, v in parameters.items()}
    
    sim_build = os.path.join(test_dir, "sim_build",
        request.node.name.replace('[', '-').replace(']', ''))
    
    cocotb_test.simulator.run(
        python_search=[test_dir],
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        parameters=parameters,
        sim_build=sim_build,
        extra_env=extra_env,
    )