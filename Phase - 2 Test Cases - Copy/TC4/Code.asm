/* Implements the following pseudo code.
accum = 0
for i in range(6):
    accum += i
    if accum == 12:
        store(i)

def store(val):
    store val R1
*/

/*

R2 相当于 range(R2)
R3 相当于 accum = R3
R4 相当于 i
R5 相当于 accum


*/

0:      LW R2, R0, #4    // 0x00400103 - Load from Mem[R0 + 4] into R2 - Val 5 
4:      LW R3, R0, #8    // 0x00800183 - Load from Mem[R0 + 8] into R3 - Val 10
8:  B1: ADDI R4, R4, #1  // 0x00120213 - Increment R4 by 1
12:     ADD R5, R4, R5   // 0x005202B3 - R5 = R4 + R5
16:     BNE R5, R3, #8   // 0x00519463 - If R3 != R5 branch to B2
20:     JAL R10, #12     // 0x00C0056F - Jump to FN and store PC + 4 in R10
    B2 是用来判断循环结束没有的 R4 是 i，R2 是 6
24: B2: BNE R4, R2, #-16 // 0xFE4118E3 - If R4 != R2 branch to B1
28:     HALT             // 0xFFFFFFFF - Halt
32: FN: SW R4, R0, #16   // 0x00402823 - Store R4 in Mem[R0 + 16]
36:     SW R10, R0, #20  // 0x00A02A23 - Store R10 in Mem[R0 + 20]
40:     BEQ R0, R0, #-16 // 0xFE0008E3 - If R0 == R0 branch to B2


/* In Binary
00000000010000000000000100000011 - 0x00400103 - LW
00000000100000000000000110000011 - 0x00800183 - LW


00000000000100100000001000010011 - 0x00120213 - ADDI
00000000010100100000001010110011 - 0x005202B3 - ADD
00000000010100011001010001100011 - 0x00519463 - BNE: PC + 8
00000000110000000000010101101111 - 0x00C0056F - JAL:
11111110010000010001100011100011 - 0xFE4118E3 - BNE: PC - 16
11111111111111111111111111111111 - 0xFFFFFFFF - HALT
00000000010000000010100000100011 - 0x00402823 - SW
00000000101000000010101000100011 - 0x00A02A23 - SW
11111110000000000000100011100011 - 0xFE0008E3 - BEQ: PC - 16
*/

BNE
0  000000 00101 00011  001  0100 0   1100011

000000000100


JAL
0  0000000110  0  00000000   01010   1101111

00000000000000000110 + 0


