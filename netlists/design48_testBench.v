`timescale 1ns / 1ps

module top_tb;

    // Inputs
    reg n0, n1, n2;
    reg [13:0] n3;
    reg [12:0] n4;
    reg [7:0] n5, n6, n7;
    reg [5:0] n8;
    reg [9:0] n9;

    // Output
    wire [12:0] n10;

    // Instantiate Unit Under Test (UUT)
    top uut (
        .n0(n0),
        .n1(n1),
        .n2(n2),
        .n3(n3),
        .n4(n4),
        .n5(n5),
        .n6(n6),
        .n7(n7),
        .n8(n8),
        .n9(n9),
        .n10(n10)
    );

    // Clock generation: 10 ns period
    always #5 n0 = ~n0;

    // Test stimulus
    initial begin
        // Initialize inputs
        n0 = 0;
        n1 = 0;
        n2 = 0;
        n3 = 0;
        n4 = 0;
        n5 = 0;
        n6 = 0;
        n7 = 0;
        n8 = 0;
        n9 = 0;

        // Apply 100 random test vectors
        repeat (100) begin
            @(negedge n0);

            n1 = $random;
            n2 = $random;
            n3 = $random;
            n4 = $random;
            n5 = $random;
            n6 = $random;
            n7 = $random;
            n8 = $random;
            n9 = $random;
        end

        // End simulation
        #20;
        $finish;
    end

    // Monitor input and output values
    initial begin
        $monitor("Time=%0t | n0=%b n1=%b n2=%b n3=%h n4=%h n5=%h n6=%h n7=%h n8=%h n9=%h | n10=%h",
                 $time, n0, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10);
    end

endmodule