import os
import argparse

MemSize = 1000  # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.

# FUNCT7
ADD_FUNCT7 = "0000000"
SUB_FUNCT7 = "0100000"
SLL_FUNCT7 = "0000000"
SLT_FUNCT7 = "0000000"
SLTU_FUNCT7 = "0000000"
XOR_FUNCT7 = "0000000"
SRL_FUNCT7 = "0000000"
SRA_FUNCT7 = "0100000"
OR_FUNCT7 = "0000000"
AND_FUNCT7 = "0000000"
SRLI_FUNCT7 = "0000000"

# FUNCT3
ADD_FUNCT3 = "000"
SUB_FUNCT3 = "000"
# SLL_FUNCT3 = "001"
# SLT_FUNCT3 = "010"  # 010
# SLTU_FUNCT3 = "011"
XOR_FUNCT3 = "100"
# SRL_FUNCT3 = "101"
# SRA_FUNCT3 = "101"
OR_FUNCT3 = "110"
AND_FUNCT3 = "111"
# SRLI_FUNCT3 = "101"  # 101
SW_FUNCT3 = "010"
BEQ_FUNCT3 = "000"
BNE_FUNCT3 = "001"
LW_FUNCT3 = "000"
ADDI_FUNCT3 = "000"
# SLTI_FUNCT3 = "010"
# SLTIU_FUNCT3 = "011"
XORI_FUNCT3 = "100"
ORI_FUNCT3 = "110"
ANDI_FUNCT3 = "111"
# SLLI_FUNCT3 = "001"

# OP
JAL_OP = "1101111"
SW_OP = "0100011"
BEQ_OP = "1100011"
BNE_OP = "1100011"
LW_OP = "0000011"
I_TYPE_OP = "0010011"
R_TYPE_OP = "0110011"
HALT_OP = "1111111"


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
        # read instruction memory
        # return 32 bit hex val
        return self.IMem[ReadAddress] + self.IMem[ReadAddress + 1] + self.IMem[ReadAddress + 2] + self.IMem[
            ReadAddress + 3]


class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(ioDir + "/dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]
        self.DMem = self.DMem[:len(self.DMem)] + ["00000000"] * (1000 - len(self.DMem))

    def readInstr(self, ReadAddress):
        # read data memory
        # return 32 bit hex val
        rawVal = self.DMem[ReadAddress] + self.DMem[ReadAddress + 1] + self.DMem[ReadAddress + 2] + self.DMem[
            ReadAddress + 3]
        return int(rawVal, 2)

    def writeDataMem(self, Address, WriteData):
        # write data into byte addressable memory
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
        # op.extend([str(val)+"\n" for val in self.Registers])
        op.extend(["{:032b}".format(val) + "\n"[-32:] for val in self.Registers])  # Can't support overflow
        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)


class State(object):
    def __init__(self):
        self.IF = {"nop": 0, "PC": 0}
        self.ID = {"nop": 0, "Instr": ""}
        self.EX = {"nop": 0, "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0,
                   "is_I_type": 0, "rd_mem": 0,
                   "wrt_mem": 0, "alu_op": 0, "wrt_enable": 0, "Halt": 0}
        self.MEM = {"nop": 0, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "rd_mem": 0,
                    "wrt_mem": 0, "wrt_enable": 0}
        self.WB = {"nop": 0, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}

    def update(self, other):
        for attr in ("IF", "ID", "EX", "MEM", "WB"):
            self_attr = getattr(self, attr)
            other_attr = getattr(other, attr)
            for key in other_attr:
                self_attr[key] = other_attr[key]


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


class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):

        super(SingleStageCore, self).__init__(ioDir + "/SS_", imem, dmem)
        self.opFilePath = ioDir + "/StateResult_SS.txt"
        self.cntInstr = 0

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
        self.PCWrite = True
        self.IFIDWrite = True

    def decode(self, instr):
        print("[debug]decode inst:", instr)
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
        concat_immVal_B = sign_extend(int(instr[0] + instr[-8] + instr[1:7] + instr[-12:-8] + "0", 2), 13)  # B-type imm
        concat_immVal_J = sign_extend(int(instr[0] + instr[12:20] + instr[11] + instr[1:11] + "0", 2), 21)  # J-type imm
        print("[debug]decode opcode:", op)
        print("[debug]decode funct3:", funct3)
        print("[debug]decode funct7:", funct7)
        print("[debug]decode rs1:", rs1)
        print("[debug]decode rs2:", rs2)
        print("[debug]decode rd:", rd)
        print("[debug]decode imm:", imm)
        self.nextState.EX["Rs"] = rs1
        self.nextState.EX["Rt"] = rs2
        self.nextState.EX["Read_data1"] = self.myRF.readRF(rs1)
        self.nextState.EX["Read_data2"] = self.myRF.readRF(rs2)
        self.nextState.EX["Wrt_reg_addr"] = rd
        self.nextState.EX["Imm"] = imm
        self.nextState.EX["alu_op"] = self.get_alu_op(op, funct3, funct7)
        self.nextState.EX["rd_mem"] = 1 if op == LW_OP else 0
        self.nextState.EX["wrt_mem"] = 1 if op == SW_OP else 0
        self.nextState.EX["is_I_type"] = 1 if op == I_TYPE_OP else 0
        if op == R_TYPE_OP or op == JAL_OP or op == LW_OP or self.nextState.EX["is_I_type"]:
            # print("[debug][ID-stage] ALUOP is", ALUop, "is_I_type is", self.nextState.EX["is_I_type"],
            # "and nextState.EX[wrt_enable] is set to 1")
            self.nextState.EX["wrt_enable"] = 1  # wrt_enable for reg\
        else:
            self.nextState.EX["wrt_enable"] = 0
        return concat_immVal_S, concat_immVal_B, concat_immVal_J, op

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
            # elif funct3 == SLTU_FUNCT3:
            #     return "SLTU"
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
            # elif funct3 == SLTI_FUNCT3:
            #     return "SLTI"
            # elif funct3 == SLTIU_FUNCT3:
            #     return "SLTIU"
            elif funct3 == XORI_FUNCT3:
                return "XORI"
            elif funct3 == ORI_FUNCT3:
                return "ORI"
            elif funct3 == ANDI_FUNCT3:
                return "ANDI"
            # elif funct3 == SLLI_FUNCT3:
            #     return "SLLI"

    def EX_compute(self, aluop, rs1Val, rs2Val, immVal):
        print("[debug]EX_compute ALUOP", aluop)
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
            self.nextState.MEM["wrt_enable"] = True
            return (rs1Val + rs2Val) & 0xffffffff
        elif aluop == "SW":
            self.nextState.MEM["wrt_mem"] = 1
            return (rs1Val + immVal) & 0xffffffff
        elif aluop == "BEQ":
            return (rs1Val - rs2Val) & 0xffffffff
        elif aluop == "BNE":
            print("[debug][EX-stage] BNE!!! rs1Val | rs2Val:", rs1Val, "|", rs2Val, "|", (rs1Val - rs2Val))
            return (rs1Val - rs2Val) & 0xffffffff
        elif aluop == "LW":
            self.nextState.MEM["rd_mem"] = 1
            return (rs1Val + immVal) & 0xffffffff
        elif aluop == "ADDI":
            return (rs1Val + immVal) & 0xffffffff
        elif aluop == "SLTI":
            return complementTovalue(rs1Val) < complementTovalue(immVal)
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
        print("[debug] The aluop is not recorded:", aluop)
        return 0

    def step(self):
        # Your implementation
        # PC selection MUX
        BRANCH_PC = -1
        PCSrc = 0

        # --------------------- WB stage ---------------------
        if not self.state.WB["nop"]:
            if self.state.WB["wrt_enable"] == 1 and self.state.WB["Wrt_reg_addr"] != 0:  # not write to zero
                self.myRF.writeRF(self.state.WB["Wrt_reg_addr"], self.state.WB["Wrt_data"])

        # --------------------- MEM stage --------------------
        if not self.state.MEM["nop"]:
            #  -- WRITE data into mem, if wrt_mem flag is set
            if self.state.MEM["wrt_mem"] == 1:
                self.ext_dmem.writeDataMem(self.state.MEM["ALUresult"], self.state.MEM["Store_data"])
                # # If data is overwritten in WB, get data directly from WB stage
                # if (self.state.MEM["Rt"] == self.state.WB["Wrt_reg_addr"]):
                #     self.ext_dmem.writeDataMem(self.state.MEM["ALUresult"], self.state.WB["Wrt_data"])
            # -- READ data from mem, WB's wrt_data is read from mem in MEM, ALUresult is the address
            self.nextState.WB["Wrt_data"] = self.ext_dmem.readInstr(self.state.MEM["ALUresult"]) if self.state.MEM[
                                                                                                        "rd_mem"] == 1 else \
                self.state.MEM["ALUresult"]
            self.nextState.WB["Rs"] = self.state.MEM["Rs"]
            self.nextState.WB["Rt"] = self.state.MEM["Rt"]
            self.nextState.WB["Wrt_reg_addr"] = self.state.MEM["Wrt_reg_addr"]
            self.nextState.WB["wrt_enable"] = self.state.MEM["wrt_enable"]

        # --------------------- EX stage ---------------------
        PCSrc = 0
        if not self.state.EX["nop"]:
            if self.state.EX["Halt"] == 1:
                self.nextState.EX = self.state.EX
                self.state.EX["Halt"] = 0
            else:
                # Check Data Hazard --- Forwarding
                if self.state.WB["Wrt_reg_addr"] != 0:
                    if self.state.WB["Wrt_reg_addr"] == self.state.EX["Rs"]:
                        self.state.EX["Read_data1"] = self.state.WB["Wrt_data"]
                    if self.state.WB["Wrt_reg_addr"] == self.state.EX["Rt"]:
                        self.state.EX["Read_data2"] = self.state.WB["Wrt_data"]
                    # Avoid Double Data Hazard by Overwrite
                    if self.state.MEM["Wrt_reg_addr"] == self.state.EX["Rs"]:
                        self.state.EX["Read_data1"] = self.state.MEM["ALUresult"]
                    if self.state.MEM["Wrt_reg_addr"] == self.state.EX["Rt"]:
                        self.state.EX["Read_data2"] = self.state.MEM["ALUresult"]

                self.nextState.MEM["ALUresult"] = self.EX_compute(self.state.EX["alu_op"], self.state.EX["Read_data1"],
                                                                  self.state.EX["Read_data2"], self.state.EX["Imm"])
                # SW MUX
                if self.state.EX["wrt_mem"]:
                    self.nextState.MEM["Store_data"] = self.state.EX["Read_data2"]
                self.nextState.MEM["Rs"] = self.state.EX["Rs"]
                self.nextState.MEM["Rt"] = self.state.EX["Rt"]
                self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
                self.nextState.MEM["rd_mem"] = self.state.EX["rd_mem"]
                self.nextState.MEM["wrt_mem"] = self.state.EX["wrt_mem"]
                self.nextState.MEM["wrt_enable"] = self.state.EX["wrt_enable"]

        self.nextState.MEM["nop"] = self.state.EX["nop"]
        # --------------------- ID stage ---------------------
        if not self.state.ID["nop"]:
            # decode
            concat_immVal_S, concat_immVal_B, concat_immVal_J, op = self.decode(self.state.ID["Instr"])  # Save the decoded data in nextState.EX
            # Deal with SW
            if op == SW_OP:
                self.nextState.EX["Imm"] = concat_immVal_S
            # check Load-Use Hazard
            if self.state.EX["wrt_enable"] == 1 and self.state.EX["wrt_mem"] != 0:
                if op == R_TYPE_OP or op == SW_OP:
                    if self.state.EX["Wrt_reg_addr"] == self.nextState.EX["Rs"] or self.state.EX["Wrt_reg_addr"] == \
                            self.nextState.EX["Rt"]:
                        # Stall the pipeline --- NOP in ID/EX
                        self.nextState.EX["Halt"] = 1
                        # Stop updating IF/ID and PC
                        self.PCWrite = False
                        self.IFIDWrite = False
                elif op == I_TYPE_OP:
                    if self.state.EX["Wrt_reg_addr"] == self.nextState.EX["Rs"]:
                        # Stall the pipeline --- NOP in ID/EX
                        self.nextState.EX["Halt"] = 1
                        # Stop updating IF/ID and PC
                        self.PCWrite = False
                        self.IFIDWrite = False
            # Branch Hazard
            if (op == BEQ_OP and self.nextState.EX["Rs"] == self.nextState.EX["Rt"]) or (
                    op == BNE_OP and self.nextState.EX["Rs"] != self.nextState.EX["Rt"]):
                self.PCSrc = 1
                BRANCH_PC = concat_immVal_B
                self.nextState.EX["nop"] = 1
                self.nextState.ID["nop"] = 1
            elif op == JAL_OP:
                self.PCSrc = 1
                BRANCH_PC = concat_immVal_J
                self.nextState.ID["nop"] = 1
                self.nextState.EX["Read_data1"] = self.state.ID["PC"] + 4
                self.nextState.EX["Read_data2"] = 0
                self.nextState.EX["Rs"] = 0
                self.nextState.EX["Rt"] = 0
                self.nextState.EX["alu_op"] = "ADD"

        # --------------------- IF stage ---------------------
        if not self.state.IF["nop"]:
            # Update IF/ID Register
            # Deal with Load-Use Hazard
            if not self.IFIDWrite:
                self.IFIDWrite = True
                # Keep the original instruction in IF/ID
                self.nextState.ID["Instr"] = self.state.ID["Instr"]
                self.nextState.ID["nop"] = self.state.ID["nop"]
            else:
                instr = self.ext_imem.readInstr(self.state.IF["PC"])
                self.nextState.ID["Instr"] = instr
                self.nextState.ID["nop"] = self.state.IF["nop"]
                if instr == "11111111111111111111111111111111":
                    print("HALT INSTR ENCOUNTERED")
                    self.nextState.IF["nop"] = True
                    self.nextState.ID["nop"] = True
                    self.halted = True
            # Update PC
            # Deal with Load-Use Hazard
            if not self.PCWrite:
                self.PCWrite = True
                self.nextState.IF["PC"] = self.state.IF["PC"]
            else:
                if PCSrc == 0:
                    self.nextState.IF["PC"] += 4
                else:
                    print("[debug][IF-stage] PC:", self.state.IF["PC"])
                    self.nextState.IF["PC"] = BRANCH_PC

        # --------------------- Dump & Update ---------------------
        # Update State
        self.state.update(self.nextState)
        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ...
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-" * 70 + "\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
        printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
        printstate.extend(["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()])
        printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
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

    while (True):
        if not ssCore.halted:
            ssCore.step()

        if not fsCore.halted:
            fsCore.step()

        if ssCore.halted and fsCore.halted:
            break
    print("Performance Metric:")
    print("[Single Stage]")
    print("CPI =", ssCore.cycle / ssCore.cntInstr)
    print("Total execution cycles =", ssCore.cycle)
    print("Instructions per cycle =", ssCore.cntInstr / ssCore.cycle)

    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()
