TOPLEVEL_LANG = verilog

SIM ?= icarus
WAVES ?= 1

COCOTB_HDL_TIMEUNIT = 1us
COCOTB_HDL_TIMEPRECISION = 1ps

DUT 		= time_sync
TOPLEVEL 	= test_$(DUT)
MODULE 		= test_$(DUT)
VERILOG_SOURCES += $(TOPLEVEL).v
VERILOG_SOURCES += ../../rtl/common/$(DUT).v
VERILOG_SOURCES += ../../rtl/common/mqnic_ptp.v
VERILOG_SOURCES += ../../rtl/common/mqnic_ptp_clock.v
VERILOG_SOURCES += ../../rtl/common/mqnic_ptp_perout.v
VERILOG_SOURCES += ../../rtl/common/time_sync_slave.v
VERILOG_SOURCES += ../../lib/eth/rtl/ptp_td_phc.v
VERILOG_SOURCES += ../../lib/eth/rtl/ptp_td_leaf.v
VERILOG_SOURCES += ../../lib/eth/rtl/ptp_perout.v

# module parameters

# Clock configuration
#export PARAM_CLK_PERIOD_NS_NUM := 4
#export PARAM_CLK_PERIOD_NS_DENOM := 1

# PTP configuration
#export PARAM_PTP_PERIOD_NS_NUM := 1024
#export PARAM_PTP_PERIOD_NS_DENOM := 165
export PARAM_PTP_CLOCK_PIPELINE := 0
export PARAM_PTP_CLOCK_CDC_PIPELINE := 0
export PARAM_PTP_PORT_CDC_PIPELINE := 0
export PARAM_PTP_PEROUT_ENABLE := 0
export PARAM_PTP_PEROUT_COUNT := 1


# AXI lite interface configuration (control)
export PARAM_AXIL_CTRL_DATA_WIDTH := 32
export PARAM_AXIL_CTRL_ADDR_WIDTH := 24

ifeq ($(SIM), icarus)
	PLUSARGS += -fst

	COMPILE_ARGS += $(foreach v,$(filter PARAM_%,$(.VARIABLES)),-P $(TOPLEVEL).$(subst PARAM_,,$(v))=$($(v)))

	ifeq ($(WAVES), 1)
		VERILOG_SOURCES += iverilog_dump.v
		COMPILE_ARGS += -s iverilog_dump
	endif
else ifeq ($(SIM), verilator)
	COMPILE_ARGS += -Wno-SELRANGE -Wno-WIDTH

	COMPILE_ARGS += $(foreach v,$(filter PARAM_%,$(.VARIABLES)),-G$(subst PARAM_,,$(v))=$($(v)))

	ifeq ($(WAVES), 1)
		COMPILE_ARGS += --trace-fst
	endif
endif

include $(shell cocotb-config --makefiles)/Makefile.sim

iverilog_dump.v:
	echo 'module iverilog_dump();' > $@
	echo 'initial begin' >> $@
	echo '    $$dumpfile("$(TOPLEVEL).fst");' >> $@
	echo '    $$dumpvars(0, $(TOPLEVEL));' >> $@
	echo 'end' >> $@
	echo 'endmodule' >> $@	

clean::
	@rm -rf __pycache__ *.vcd *.fst iverilog_dump.v
