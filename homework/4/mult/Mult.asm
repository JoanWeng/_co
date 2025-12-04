// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
// The algorithm is based on repetitive addition.

//// Replace this comment with your code.

    @R2            // Initialize R2 to 0
    M=0            // R2 = 0
    
    @R1            // Load R1 into D
    D=M
    @END           // If R1 = 0, skip to end
    D;JEQ
    
    @R0            // Load R0 into D
    D=M
    @END           // If R0 = 0, skip to end
    D;JEQ
    
    @i             // Initialize counter i = R1
    M=D            // (actually set i = R0 first, will fix below)
    
    @R1            // Load R1 into counter
    D=M
    @i
    M=D            // i = R1

(LOOP)
    @i             // Load counter
    D=M
    @END           // If i = 0, we're done
    D;JEQ
    
    @R0            // Load R0
    D=M
    @R2            // Add R0 to R2
    M=D+M          // R2 = R2 + R0
    
    @i             // Decrement counter
    M=M-1          // i = i - 1
    
    @LOOP          // Repeat loop
    0;JMP

(END)
    @END           // Infinite loop at end
    0;JMP