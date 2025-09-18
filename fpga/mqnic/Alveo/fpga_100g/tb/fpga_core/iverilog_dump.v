module iverilog_dump();
initial begin
    $dumpfile("test_fpga_core.fst");
    $dumpvars(0, test_fpga_core);
end
endmodule
