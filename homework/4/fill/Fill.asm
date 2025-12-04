// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

//// Replace this comment with your code.

// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/fill/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Screen memory map: RAM[16384] - RAM[24575] (8K registers, 256 rows * 512 pixels / 16)
// Keyboard memory map: RAM[24576]

(MAIN_LOOP)
    @KBD           // Load keyboard memory address (24576)
    D=M            // D = RAM[24576] (keyboard input)
    
    @SET_BLACK     // If key is pressed (D != 0), go to SET_BLACK
    D;JNE
    
    @SET_WHITE     // If no key is pressed (D == 0), go to SET_WHITE
    0;JMP

(SET_BLACK)
    @color         // Set color variable to -1 (all bits 1 = black)
    M=-1
    @FILL_SCREEN   // Jump to fill screen routine
    0;JMP

(SET_WHITE)
    @color         // Set color variable to 0 (all bits 0 = white)
    M=0
    @FILL_SCREEN   // Jump to fill screen routine
    0;JMP

(FILL_SCREEN)
    @SCREEN        // Start address of screen memory map
    D=A
    @address       // Initialize address pointer
    M=D
    
    @8192          // Number of 16-bit registers in screen (512*256/16)
    D=A
    @counter       // Initialize counter
    M=D

(FILL_LOOP)
    @counter       // Check if counter reached 0
    D=M
    @MAIN_LOOP     // If counter = 0, return to main loop
    D;JEQ
    
    @color         // Load color value
    D=M
    @address       // Load current address
    A=M
    M=D            // Set screen register to color value
    
    @address       // Increment address pointer
    M=M+1
    
    @counter       // Decrement counter
    M=M-1
    
    @FILL_LOOP     // Continue filling
    0;JMP