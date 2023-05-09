import os
import argparse
from copy import deepcopy

# FUNCT7
ADD_FUNCT7 = "0000000"
SUB_FUNCT7 = "0100000"
# SLL_FUNCT7 = "0000000"
# SLT_FUNCT7 = "0000000"
SLTU_FUNCT7 = "0000000"
XOR_FUNCT7 = "0000000"
# SRL_FUNCT7 = "0000000"
# SRA_FUNCT7 = "0100000"
OR_FUNCT7 = "0000000"
AND_FUNCT7 = "0000000"
SRLI_FUNCT7 = "0000000"

# FUNCT3
ADD_FUNCT3 = "000"
SUB_FUNCT3 = "000"
# SLL_FUNCT3 = "001"
# SLT_FUNCT3 = "001"
SLTU_FUNCT3 = "011"
XOR_FUNCT3 = "100"
# SRL_FUNCT3 = "101"
# SRA_FUNCT3 = "101"
OR_FUNCT3 = "110"
AND_FUNCT3 = "111"
SRLI_FUNCT3 = "111"
SW_FUNCT3 = "010"
BEQ_FUNCT3 = "000"
BNE_FUNCT3 = "001"
LW_FUNCT3 = "000"
ADDI_FUNCT3 = "000"
SLTI_FUNCT3 = "010"
SLTIU_FUNCT3 = "011"
XORI_FUNCT3 = "100"
ORI_FUNCT3 = "110"
ANDI_FUNCT3 = "111"
SLLI_FUNCT3 = "001"

# OP
JAL_OP = "1101111"
SW_OP = "0100011"
BEQ_OP = "1100011"
BNE_OP = "1100011"
LW_OP = "0000011"
I_TYPE_OP = "0010011"
R_TYPE_OP = "0110011"
B_TYPE_OP = "1100011"
HALT_OP = "1111111"

MemSize = 1000  # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.


def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    res = (value & (sign_bit - 1)) - (value & sign_bit)
    if res >= 2 ** 31:
        res -= 2 ** 32
    return res


def complementTovalue(value):
    return (value & ((1 << 31) - 1)) - (value & (1 << 31))


class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name

        with open(ioDir + "/imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def readInstr(self, ReadAddress):
        return self.IMem[ReadAddress] + self.IMem[ReadAddress + 1] + self.IMem[ReadAddress + 2] + self.IMem[
            ReadAddress + 3]


class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(ioDir + "/dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]
        while len(self.DMem) < MemSize:
            self.DMem.append("00000000")

    def readInstr(self, ReadAddress):
        # read data memory
        # return 32 bit hex val
        rawVal = self.DMem[ReadAddress] + self.DMem[ReadAddress + 1] + self.DMem[ReadAddress + 2] + self.DMem[
            ReadAddress + 3]
        return int(rawVal, 2)

    def writeDataMem(self, Address, WriteData):
        b_str = "{:032b}".format(WriteData)
        self.DMem[Address] = b_str[:8]
        self.DMem[Address + 1] = b_str[8:16]
        self.DMem[Address + 2] = b_str[16:24]
        self.DMem[Address + 3] = b_str[24:32]

    def outputDataMem(self):
        resPath = self.ioDir + "/" + self.id + "_DMEMResult.txt"
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])


class RegisterFile(object):
    def __init__(self, ioDir):
        self.outputFile = ioDir + "RFResult.txt"
        self.Registers = [0x0 for i in range(32)]

    def readRF(self, Reg_addr):
        return self.Registers[Reg_addr]

    def writeRF(self, Reg_addr, Wrt_reg_data):
        # Write Integer to registers (Signed ).
        self.Registers[Reg_addr] = Wrt_reg_data

    def outputRF(self, cycle):
        op = ["-" * 70 + "\n", "State of RF after executing cycle:" + str(cycle) + "\n"]
        op.extend(["{:032b}".format(val) + "\n"[-32:] for val in self.Registers])
        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)


class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0}
        self.ID = {"nop": False, "Instr": "00000000000000000000000000000000"}
        self.EX = {"nop": False, "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0,
                   "is_I_type": False, "rd_mem": 0,
                   "wrt_mem": 0, "alu_op": "ADD", "wrt_enable": 0}
        self.MEM = {"nop": False, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "rd_mem": 0,
                    "wrt_mem": 0, "wrt_enable": 0}
        self.WB = {"nop": False, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}


class Core(object):
    def __init__(self, ioDir, imem, dmem):
        self.myRF = RegisterFile(ioDir)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem
        self.cntInstr = 0


class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir + "/SS_", imem, dmem)
        self.opFilePath = ioDir + "/StateResult_SS.txt"

    def step(self):
        # Your implementation
        common_PC = True
        self.cntInstr += 1
        if (self.state.IF["nop"] == 1):
            instr = ""
            common_PC = False
        else:
            instr = self.ext_imem.readInstr(self.state.IF["PC"])
            op = instr[25:32]
            rd = instr[20:25]

            rs2 = instr[7:12]
            rs1 = instr[12:17]

            funct7 = instr[0:7]
            funct3 = instr[17:20]

            imm = instr[0:12]

            rs1Val = self.myRF.readRF(int(rs1, 2))
            rs2Val = self.myRF.readRF(int(rs2, 2))
            rdVal = int(rd, 2)
            immVal = sign_extend(int(imm, 2), 12)
            concat_immVal = sign_extend(int(funct7 + rd, 2), 12)

            # HALT
            if op == HALT_OP:
                self.nextState.IF["nop"] = 1
                common_PC = False

            elif op == R_TYPE_OP:
                # ADD
                if funct7 == ADD_FUNCT7 and funct3 == ADD_FUNCT3:
                    res = (rs1Val + rs2Val) & 0xffffffff  # Ignore Overflow


                # SUB
                elif funct7 == SUB_FUNCT7 and funct3 == SUB_FUNCT3:
                    res = (rs1Val - rs2Val) & 0xffffffff  # Ignore Overflow

                # # SLL
                # elif funct7 == SLL_FUNCT7 and funct3 == SLL_FUNCT3:
                #     res = (rs1Val << rs2Val) & 0xffffffff

                # # SLT
                # elif funct7 == SLT_FUNCT7 and funct3 == SLT_FUNCT3:
                #     # 2's complement -> Decimal?
                #     res = (complementTovalue(rs1Val) < complementTovalue(rs2Val))

                # # SLTU
                # elif funct7 == "0000000" and funct3 == "011":
                #     res = (rs1Val < rs2Val)

                # XOR
                elif funct7 == XOR_FUNCT7 and funct3 == XOR_FUNCT3:
                    res = (rs1Val ^ rs2Val) & 0xffffffff

                # # SRL
                # elif funct7 == "0000000" and funct3 == "101":
                #     res = rs1Val >> rs2Val

                # # SRA
                # elif funct7 == "0100000" and funct3 == "101":
                #     res = (complementTovalue(rs1Val) >> rs2Val) & 0xffffffff

                # OR
                elif funct7 == OR_FUNCT7 and funct3 == OR_FUNCT3:
                    res = (rs1Val | rs2Val) & 0xffffffff

                # AND
                elif funct7 == AND_FUNCT7 and funct3 == AND_FUNCT3:
                    res = (rs1Val & rs2Val) & 0xffffffff

                # # SRLI
                # elif funct7 == "0000000" and funct3 == "111":
                #     res = rs1Val >> immVal

                else:
                    res = 0
                if rdVal != 0:
                    self.myRF.writeRF(rdVal, res)
            # JAL
            elif op == JAL_OP:
                offset = instr[:-12]
                offset = sign_extend(int(offset[0] + offset[-8:] + offset[-9] + offset[-19:-9] + "0", 2), 21)
                if (rdVal != 0):
                    self.myRF.writeRF(rdVal, (self.state.IF["PC"] + 4) & 0xffffffff)
                # # Throw Error if PC + offset is not 4-byte aligned
                # if ((self.state.IF["PC"] + offset) % 4 != 0):
                #     print("PC + offset is not 4-byte aligned")
                #     exit(1)
                # # Throw Error if PC out of range
                # if ((self.state.IF["PC"] + offset) > len(self.ext_imem.IMem)):
                #     print("PC out of range")
                #     exit(1)
                self.nextState.IF["PC"] = self.state.IF["PC"] + offset  # Decimal?
                common_PC = False
            # SW
            elif op == SW_OP and funct3 == SW_FUNCT3:
                self.ext_dmem.writeDataMem(rs1Val + concat_immVal, rs2Val & 0xffffffff)
            # BEQ
            elif op == BEQ_OP and funct3 == BEQ_FUNCT3:
                if (rs1Val == rs2Val):
                    offset = sign_extend(int(instr[0] + instr[-8] + instr[1:7] + instr[-12:-8] + "0", 2), 13)
                    self.nextState.IF["PC"] += offset
                    common_PC = False
            # BNE
            elif op == BNE_OP and funct3 == BNE_FUNCT3:
                if (rs1Val != rs2Val):
                    offset = sign_extend(int(instr[0] + instr[-8] + instr[1:7] + instr[-12:-8] + "0", 2), 13)
                    # offset = sign_extend(int(instr[0] + instr[-8] + instr[1:6] + instr[-12:-8] + "0", 2), 12)
                    self.nextState.IF["PC"] += offset
                    common_PC = False
            elif (rdVal != 0):
                # LW
                if op == LW_OP and funct3 == LW_FUNCT3:
                    val = self.ext_dmem.readInstr(rs1Val + immVal)
                    self.myRF.writeRF(rdVal, val)

                # The following ins'op = 0010011
                # ADDI
                elif funct3 == ADDI_FUNCT3:
                    res = (rs1Val + immVal) & 0xffffffff  # Ignore Overflow
                    self.myRF.writeRF(rdVal, res)

                # SLTI
                # elif funct3 == "010":
                #     # Signed
                #     res = complementTovalue(rs1Val) < complementTovalue(immVal)
                #     self.myRF.writeRF(rdVal, res)
                #
                # # SLTIU
                # elif funct3 == "011":
                #     # Unsigned
                #     res = rs1Val < immVal
                #     self.myRF.writeRF(rdVal, res)

                # XORI
                elif funct3 == XORI_FUNCT3:
                    res = (rs1Val ^ immVal) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)

                # ORI
                elif funct3 == ORI_FUNCT3:
                    res = (rs1Val | immVal) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)

                # ANDI
                elif funct3 == ANDI_FUNCT3:
                    res = (rs1Val & immVal) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)

                # # SLLI
                # elif funct3 == "001":
                #     res = (rs1Val << immVal) & 0xffffffff
                #     self.myRF.writeRF(rdVal, res)

        if common_PC:
            self.nextState.IF["PC"] += 4
        if self.state.IF["nop"]:
            self.halted = True

        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ...

        self.state.IF["PC"] = self.nextState.IF[
            "PC"]  # The end of the cycle and updates the current state with the values calculated in this cycle
        self.state.IF["nop"] = self.nextState.IF[
            "nop"]  # The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-" * 70 + "\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")

        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir + "/FS_", imem, dmem)
        self.opFilePath = ioDir + "/StateResult_FS.txt"
        self.cntInstr = 0
        self.END = False

    # EX stage
    def get_alu_op(self, opcode, funct3, funct7=None):
        self.nextState.EX["is_I_type"] = False

        if opcode == HALT_OP:
            return "HALT"
        if opcode == R_TYPE_OP:  # R-type instructions
            if funct3 == ADD_FUNCT3:
                return "ADD" if funct7 == ADD_FUNCT7 else "SUB"
            # elif funct3 == SLL_FUNCT3:
            # return "SLL"
            # elif funct3 == SLT_FUNCT3:
            # return "SLT"
            elif funct3 == SLTU_FUNCT3:
                return "SLTU"
            elif funct3 == XOR_FUNCT3:
                return "XOR"
            # elif funct3 == SRL_FUNCT3:
            # return "SRL" if funct7 == SRL_FUNCT7 else "SRA"
            elif funct3 == OR_FUNCT3:
                return "OR"
            elif funct3 == AND_FUNCT3:
                return "AND"
        elif opcode == JAL_OP:  # I-type instructions
            return "JAL"
        elif opcode == SW_OP and funct3 == SW_FUNCT3:
            return "SW"
        elif opcode == BEQ_OP and funct3 == BEQ_FUNCT3:
            return "BEQ"
        elif opcode == BNE_OP and funct3 == BNE_FUNCT3:
            return "BNE"
        elif opcode == LW_OP and funct3 == LW_FUNCT3:
            return "LW"
        else:
            self.nextState.EX["is_I_type"] = True
            if funct3 == ADDI_FUNCT3 and opcode == I_TYPE_OP:
                return "ADDI"
            elif funct3 == SLTI_FUNCT3:
                return "SLTI"
            elif funct3 == SLTIU_FUNCT3:
                return "SLTIU"
            elif funct3 == XORI_FUNCT3:
                return "XORI"
            elif funct3 == ORI_FUNCT3:
                return "ORI"
            elif funct3 == ANDI_FUNCT3:
                return "ANDI"
            elif funct3 == SLLI_FUNCT3:
                return "SLLI"

    def EX_compute(self, aluop, rs1Val, rs2Val, immVal):
        # print("[debug][EX-stage] ALUop:", aluop)
        if aluop == "ADD":
            return (rs1Val + rs2Val) & 0xffffffff
        elif aluop == "SUB":
            return (rs1Val - rs2Val) & 0xffffffff
        elif aluop == "SLL":
            return (rs1Val << rs2Val) & 0xffffffff
        elif aluop == "SLT":
            return (complementTovalue(rs1Val) < complementTovalue(rs2Val)) & 0xffffffff
        elif aluop == "SLTU":
            return (rs1Val < rs2Val) & 0xffffffff
        elif aluop == "XOR":
            return (rs1Val ^ rs2Val) & 0xffffffff
        elif aluop == "SRL":
            return (rs1Val >> rs2Val) & 0xffffffff
        elif aluop == "SRA":
            return (complementTovalue(rs1Val) >> rs2Val)
        elif aluop == "OR":
            return (rs1Val | rs2Val) & 0xffffffff
        elif aluop == "AND":
            return (rs1Val & rs2Val) & 0xffffffff
        elif aluop == "SRLI":
            return (rs1Val >> immVal) & 0xffffffff
        elif aluop == "JAL":
            self.nextState.MEM["wrt_enable"] = 1
            return (rs1Val + rs2Val) & 0xffffffff
        elif aluop == "SW":
            self.nextState.MEM["wrt_mem"] = 1
            return (rs1Val + immVal) & 0xffffffff
        elif aluop == "BEQ":
            return (rs1Val - rs2Val) & 0xffffffff
        elif aluop == "BNE":
            return (rs1Val - rs2Val) & 0xffffffff
        elif aluop == "LW":
            self.nextState.MEM["rd_mem"] = 1
            return (rs1Val + immVal) & 0xffffffff
        elif aluop == "ADDI":
            return (rs1Val + immVal) & 0xffffffff
        elif aluop == "SLTI":
            return (complementTovalue(rs1Val) < complementTovalue(immVal))
        elif aluop == "SLTIU":
            return (rs1Val < immVal) & 0xffffffff
        elif aluop == "XORI":
            return (rs1Val ^ immVal) & 0xffffffff
        elif aluop == "ORI":
            return (rs1Val | immVal) & 0xffffffff
        elif aluop == "ANDI":
            return (rs1Val & immVal) & 0xffffffff
        elif aluop == "SLLI":
            return (rs1Val << immVal) & 0xffffffff
        return 0

    def step(self):
        self.cntInstr += 1
        # Your implementation
        BUBBLE = False
        # PC selection MUX
        PCSrc = 0
        # --------------------- WB stage ---------------------
        # WB for the write-back stage, with the drawing showing the register file being written

        if not BUBBLE and self.state.WB["nop"] == False:
            if self.state.WB["wrt_enable"] == 1 and self.state.WB["Wrt_reg_addr"] != 0:  # not write to zero
                self.myRF.writeRF(self.state.WB["Wrt_reg_addr"], self.state.WB["Wrt_data"])

        # --------------------- MEM stage --------------------
        # MEM for the memory access stage, with the box representing data memory
        if (not BUBBLE and self.state.MEM["nop"] == False):
            #  -- WRITE data into mem, if wrt_mem flag is set
            if self.state.MEM["wrt_mem"] == 1:
                # If data is overwrote in WB, get data directly from WB stage
                if (self.state.MEM["Rt"] == self.state.WB["Wrt_reg_addr"]):
                    self.ext_dmem.writeDataMem(self.state.MEM["ALUresult"], self.state.WB["Wrt_data"])
                else:
                    self.ext_dmem.writeDataMem(self.state.MEM["ALUresult"], self.state.MEM["Store_data"])

            # -- READ data from mem, WB's wrt_data is read from mem in MEM, ALUresult is the address
            self.nextState.WB["Wrt_data"] = self.ext_dmem.readInstr(self.state.MEM["ALUresult"]) if self.state.MEM[
                                                                                                        "rd_mem"] == 1 else \
                self.state.MEM["ALUresult"]
            self.nextState.WB["Rs"] = self.state.MEM["Rs"]
            self.nextState.WB["Rt"] = self.state.MEM["Rt"]
            self.nextState.WB["Wrt_reg_addr"] = self.state.MEM["Wrt_reg_addr"]
            self.nextState.WB["wrt_enable"] = self.state.MEM["wrt_enable"]

        self.nextState.WB["nop"] = self.state.MEM["nop"]

        # --------------------- EX stage ---------------------
        if (not BUBBLE and self.state.EX["nop"] == False):

            self.nextState.MEM["ALUresult"] = self.EX_compute(self.state.EX["alu_op"], self.state.EX["Read_data1"],
                                                              self.state.EX["Read_data2"], self.state.EX["Imm"])
            # SW MUX
            if (self.state.EX["wrt_mem"]):
                self.nextState.MEM["Store_data"] = self.state.EX["Read_data2"]
            self.nextState.MEM["Rs"] = self.state.EX["Rs"]
            self.nextState.MEM["Rt"] = self.state.EX["Rt"]
            self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
            self.nextState.MEM["rd_mem"] = self.state.EX["rd_mem"]
            self.nextState.MEM["wrt_mem"] = self.state.EX["wrt_mem"]
            self.nextState.MEM["wrt_enable"] = self.state.EX["wrt_enable"]

        self.nextState.MEM["nop"] = self.state.EX["nop"]
        # --------------------- ID stage ---------------------
        instr = self.state.ID["Instr"]
        hazardFlag = False
        ALUop = "UNSET"
        BRANCH_PC = -1

        if not BUBBLE and self.state.ID["nop"] == False:
            op = instr[25:32]
            rdRaw = instr[20:25]
            rd = int(instr[20:25], 2)

            rs2 = int(instr[7:12], 2)
            rs1 = int(instr[12:17], 2)

            funct7 = instr[0:7]
            funct3 = instr[17:20]

            imm = instr[0:12]  # I-type imm
            immVal = sign_extend(int(imm, 2), 12)
            concat_immVal_S = sign_extend(int(funct7 + rdRaw, 2), 12)  # S-type imm
            concat_immVal_B = sign_extend(int(instr[0] + instr[-8] + instr[1:7] + instr[-12:-8] + "0", 2),
                                          13)  # B-type imm
            concat_immVal_J = sign_extend(int(instr[0] + instr[-20:-12] + instr[-21] + instr[-31:-21] + "0", 2), 21)

            rs1Val = self.myRF.readRF(rs1)
            rs2Val = self.myRF.readRF(rs2)

            ALUop = self.get_alu_op(op, funct3, funct7)
            self.nextState.EX["Read_data1"] = rs1Val
            self.nextState.EX["Read_data2"] = rs2Val

            # Forwarding
            if (self.state.EX["wrt_enable"] == 1 and self.state.EX["Wrt_reg_addr"] != 0 and self.state.EX[
                "Wrt_reg_addr"] == rs1):
                # If lw, ALU result represents address and need to be read from memo
                # Thus need to halt
                if not self.state.EX["nop"] and self.state.EX["rd_mem"]:
                    hazardFlag = True
                    BUBBLE = True
                    self.nextState.EX["nop"] = True
                # If current stage is already halted, get value from MEM stage
                elif self.state.EX["nop"]:
                    self.nextState.EX["Read_data1"] = self.nextState.WB["Wrt_data"]
                # Else forward ALU result directly
                else:
                    self.nextState.EX["Read_data1"] = self.nextState.MEM["ALUresult"]
            elif self.state.MEM["wrt_enable"] == 1 and self.state.MEM["Wrt_reg_addr"] != 0 and self.state.MEM[
                "Wrt_reg_addr"] == rs1:
                self.nextState.EX["Read_data1"] = self.nextState.WB["Wrt_data"]

            if (self.state.EX["wrt_enable"] == 1 and self.state.EX["Wrt_reg_addr"] != 0 and self.state.EX[
                "Wrt_reg_addr"] == rs2):
                if not self.state.EX["nop"] and self.state.EX["rd_mem"]:
                    hazardFlag = True
                    BUBBLE = True
                    self.nextState.EX["nop"] = True
                elif self.state.EX["nop"]:
                    self.nextState.EX["Read_data2"] = self.nextState.WB["Wrt_data"]
                else:
                    self.nextState.EX["Read_data2"] = self.nextState.MEM["ALUresult"]
            elif self.state.MEM["wrt_enable"] == 1 and self.state.MEM["Wrt_reg_addr"] != 0 and rs2 == self.state.MEM[
                "Wrt_reg_addr"]:
                self.nextState.EX["Read_data2"] = self.nextState.WB["Wrt_data"]

            if (not hazardFlag):
                self.nextState.EX["Imm"] = immVal
                if (ALUop == "SW"):
                    self.nextState.EX["Imm"] = concat_immVal_S
                #### Hazard Detection Unit
                elif (ALUop == "BEQ" or ALUop == "BNE"):
                    # If branch, all stages after that should halt
                    self.nextState.EX["nop"] = True
                    if ((ALUop == "BEQ" and self.nextState.EX["Read_data1"] == self.nextState.EX["Read_data2"]) or (
                            ALUop == "BNE" and self.nextState.EX["Read_data1"] != self.nextState.EX["Read_data2"])):
                        PCSrc = 1
                        BUBBLE = True
                        BRANCH_PC = self.state.IF["PC"] - 4 + concat_immVal_B

                elif (ALUop == "JAL"):
                    PCSrc = 1
                    self.nextState.EX["Read_data1"] = 4
                    self.nextState.EX["Read_data2"] = self.state.IF["PC"] - 4
                    BUBBLE = True
                    BRANCH_PC = self.state.IF["PC"] - 4 + concat_immVal_J

                self.nextState.EX["Rs"] = rs1
                self.nextState.EX["Rt"] = rs2
                self.nextState.EX["Wrt_reg_addr"] = rd
                self.nextState.EX["rd_mem"] = 1 if ALUop == "LW" else 0
                self.nextState.EX["wrt_mem"] = 1 if ALUop == "SW" else 0
                self.nextState.EX["alu_op"] = ALUop
                if (op == R_TYPE_OP or op == JAL_OP or op == LW_OP or self.nextState.EX["is_I_type"]):
                    self.nextState.EX["wrt_enable"] = 1  # wrt_enable for reg
                else:
                    self.nextState.EX["wrt_enable"] = 0

        # If branch away, should not pass
        if (not BUBBLE and not (ALUop == "BEQ" or ALUop == "BNE")):
            self.nextState.EX["nop"] = self.state.ID["nop"]

        # --------------------- IF stage ---------------------
        # print("============= Cycle ==============:", self.cycle)
        # PC selection MUX
        if PCSrc == 1:
            self.nextState.IF["PC"] = BRANCH_PC
            self.nextState.ID["nop"] = True

        if not BUBBLE and self.state.IF["nop"] == False:
            instr = self.ext_imem.readInstr(self.state.IF["PC"])

            self.nextState.ID["Instr"] = instr

            if (instr == "11111111111111111111111111111111"):
                self.state.IF["nop"] = True
                self.nextState.IF["nop"] = True
                self.END = True

            else:
                self.nextState.ID["Instr"] = instr

        if not BUBBLE and PCSrc == 0:
            self.nextState.ID["nop"] = self.state.IF["nop"]
            self.nextState.IF["PC"] += 4

        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and \
                self.state.WB["nop"]:
            self.halted = True

        #### LOG
        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ...

        self.state = deepcopy(
            self.nextState)  # The end of the cycle and updates the current state with the values calculated in this cycle
        if self.END == False:
            self.nextState = State()
            self.nextState.IF["PC"] = self.state.IF["PC"]
            self.nextState.IF["nop"] = self.state.IF["nop"]
            self.nextState.ID["Instr"] = self.state.ID["Instr"]
        if (BUBBLE or self.state.IF["nop"]): self.cntInstr -= 1
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-" * 70 + "\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
        printstate.append("\n")
        printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
        printstate.append("\n")
        for key, val in state.EX.items():
            if key == "Read_data1" or key == "Read_data2" or key == "Imm" or key == "Wrt_reg_addr":
                printstate.extend(["EX." + key + ": " + "{:032b}".format(val) + "\n"])

        printstate.append("\n")
        printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
        printstate.append("\n")
        printstate.extend(["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()])

        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


if __name__ == "__main__":

    # parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    ioDir = os.path.abspath(args.iodir)
    print("IO Directory:", ioDir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)

    ssCore = SingleStageCore(ioDir, imem, dmem_ss)
    fsCore = FiveStageCore(ioDir, imem, dmem_fs)
    cntInstr = len(fsCore.ext_imem.IMem) / 4

    while (True):
        if not ssCore.halted:
            ssCore.step()

        if not fsCore.halted:
            fsCore.step()

        if ssCore.halted and fsCore.halted:
            break
    print("Performance Metric:")
    print("[Single Stage]")
    print("Instruction count:")
    print("CPI =", ssCore.cycle / cntInstr)
    print("Total execution cycles =", ssCore.cycle)
    print("Instructions per cycle =", cntInstr / ssCore.cycle)
    print("[Five Stage]")
    print("Instruction count:")
    print("CPI =", fsCore.cycle / cntInstr)
    print("Total execution cycles =", fsCore.cycle)
    print("Instructions per cycle =", cntInstr / fsCore.cycle)
    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()
