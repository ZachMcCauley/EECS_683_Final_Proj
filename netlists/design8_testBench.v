`timescale 1ns / 1ps

module top_tb;

    // Inputs
    reg n0, n1, n2, n3;
    reg [1:0] n4, n5;

    // Outputs
    wire n6, n7;
    wire [6:0] n8, n9;
    wire [3:0] n10, n11, n12;

    // Instantiate the Unit Under Test (UUT)
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
        .n10(n10),
        .n11(n11),
        .n12(n12)
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
        n4 = 2'b00;
        n5 = 2'b00;

        // Apply 100 random test vectors
        repeat (100) begin
            @(negedge n0);

            n1 = $random;
            n2 = $random;
            n3 = $random;
            n4 = $random;
            n5 = $random;
        end

        // End simulation
        #20;
        $finish;
    end

    // Monitor inputs and outputs
    initial begin
        $monitor("Time=%0t | n1=%b n2=%b n3=%b n4=%b n5=%b | n6=%b n7=%b n8=%b n9=%b n10=%b n11=%b n12=%b",
                 $time, n1, n2, n3, n4, n5,
                 n6, n7, n8, n9, n10, n11, n12);
    end

endmodule