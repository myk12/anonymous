module cocotb_iverilog_dump();
initial begin
    $dumpfile("sim_build/test_fpga_core.fst");
    $dumpvars(0, test_fpga_core);
end
endmodule
