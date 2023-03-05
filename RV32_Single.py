import os
import argparse

MemSize = 1000 # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.
def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    res = (value & (sign_bit - 1)) - (value & sign_bit)
    # ？
    if res >= 2**31:
        res -= 2**32
    return res

class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name

        with open(ioDir + "/imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def readInstr(self, ReadAddress):
        #read instruction memory
        #return 32 bit hex val?
        return self.IMem[ReadAddress]+self.IMem[ReadAddress+1]+self.IMem[ReadAddress+2]+self.IMem[ReadAddress+3]


class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(ioDir + "/dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]

    def readDataMem(self, ReadAddress):
        #read data memory
        #return 32 bit hex val?
        rawVal = self.DMem[ReadAddress]+self.DMem[ReadAddress+1]+self.DMem[ReadAddress+2]+self.DMem[ReadAddress+3]
        return int(rawVal, 2)

    def writeDataMem(self, Address, WriteData):
        # write data into byte addressable memory
        self.DMem[Address] = bin(WriteData)[2:] #-> to string of bin? bin(WriteData)[2:]

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
        self.Registers[Reg_addr] = Wrt_reg_data

    def outputRF(self, cycle):
        op = ["-"*70+"\n", "State of RF after executing cycle:" + str(cycle) + "\n"]
        #op.extend([str(val)+"\n" for val in self.Registers])
        op.extend(["{:032b}".format(val)+"\n" for val in self.Registers])
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)

class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0}
        self.ID = {"nop": False, "Instr": 0}
        self.EX = {"nop": False, "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "is_I_type": False, "rd_mem": 0, 
                   "wrt_mem": 0, "alu_op": 0, "wrt_enable": 0}
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

class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir + "/SS_", imem, dmem)
        self.opFilePath = ioDir + "/StateResult_SS.txt"


    def step(self):
        # Your implementation
        if (self.state.IF["nop"] == True):
            # instr = ""
            self.halted = True

        else:
            instr = self.ext_imem.readInstr(self.state.IF["PC"])
            op = instr[-7:]

            rs2 = instr[-25:-20]
            rs1 = instr[-20:-15]
            rd = instr[-12:-7]

            funct7 = instr[0:7]
            funct3 = instr[-15:-12]

            imm = instr[0:12]

            rs1Val = self.myRF.readRF(int(rs1, 2))
            rs2Val = self.myRF.readRF(int(rs2, 2))
            rdVal = int(rd, 2)
            immVal = sign_extend(int(imm, 2),12)
            
            # HALT
            if (op == "1111111"):
                self.nextState.IF["nop"] = True

            elif (rdVal != 0 and op == "0110011"):
                # ADD
                if (funct7 == "0000000" and funct3 == "000"):
                    res = (rs1Val + rs2Val) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)


                # SUB
                elif (funct7 == "0100000" and funct3 == "000"):
                    res = (rs1Val - rs2Val) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)

                # SLL
                elif (funct7 == "0000000" and funct3 == "001"):
                    res = (rs1Val << rs2Val) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)

                # SLT
                elif (funct7 == "0000000" and funct3 == "001"):
                    res = (rs1Val < rs2Val)
                    self.myRF.writeRF(rdVal, res)

                # SLTU
                elif (funct7 == "0000000" and funct3 == "011"):
                    res = (rs1Val < rs2Val)
                    self.myRF.writeRF(rdVal, res)

                # XOR
                elif (funct7 == "0000000" and funct3 == "100"):
                    res = (rs1Val ^ rs2Val) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)

                # SRL
                elif (funct7 == "0000000" and funct3 == "101"):
                    res = self.myRF.readRF(rs1) >> self.myRF.readRF(rs2)
                    self.myRF.writeRF(rdVal, res)

                # SRA
                elif (funct7 == "0100000" and funct3 == "101"):
                    res = self.myRF.readRF(rs1) >> self.myRF.readRF(rs2)
                    self.myRF.writeRF(rdVal, res)

                # OR
                elif (funct7 == "0000000" and funct3 == "110"):
                    res = (rs1Val | rs2Val) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)

                # AND
                elif (funct7 == "0000000" and funct3 == "111"):
                    res = (rs1Val & rs2Val) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)

                # SRLI
                elif (funct7 == "0000000" and funct3 == "111"):
                    res = rs1Val >> immVal
                    self.myRF.writeRF(rdVal, res)


            elif (rdVal != 0):

                # LW
                if (op == "0000011" and funct3 == "000"):
                    immVal = sign_extend((immVal), 12)
                    val = self.ext_dmem.readInstr(rs1Val+immVal)
                    self.myRF.writeRF(rdVal, val)

                # SW
                elif (op == "0100011" and funct3 == "010"):
                    self.ext_dmem.writeDataMem(rs1Val+immVal, rs2Val)

                # JAL
                elif (op == "1101111"):
                    offset = sign_extend(int(instr[0]+instr[-20:-12]+instr[11]+instr[1:11]+"0", 2), 21)
                    self.myRF.writeRF(rdVal, self.state.IF["PC"]+4)
                    self.state.IF["PC"] += offset
                    if self.state.IF["nop"]:
                        self.halted = True

                    self.myRF.outputRF(self.cycle) # dump RF
                    self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 

                    self.state = self.nextState #The end of the cycle and updates the current state with the values calculated in this cycle
                    self.cycle += 1
                    return

                # BEQ
                elif (op == "1100011" and funct3 == "000"):
                    offset = sign_extend(int(instr[0]+instr[-8]+instr[1:6]+instr[-12:-8]+"0", 2), 12)
                    if (rs1Val == rs2Val):
                        self.state.IF["PC"] += offset
                        if self.state.IF["nop"]:
                            self.halted = True

                        self.myRF.outputRF(self.cycle) # dump RF
                        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 

                        self.state = self.nextState #The end of the cycle and updates the current state with the values calculated in this cycle
                        self.cycle += 1
                        return

                # BNQ
                elif (op == "1100011" and funct3 == "001"):
                    offset = sign_extend(int(instr[0]+instr[-8]+instr[1:6]+instr[-12:-8]+"0", 2), 12)
                    if (rs1Val != rs2Val):
                        self.state.IF["PC"] += offset
                        if self.state.IF["nop"]:
                            self.halted = True
                        
                        self.myRF.outputRF(self.cycle) # dump RF
                        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
                            
                        self.state = self.nextState #The end of the cycle and updates the current state with the values calculated in this cycle
                        self.cycle += 1
                        return

                # ADDI
                elif (funct3 == "000"):
                    res = (rs1Val + immVal) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)

                # SLTI
                elif (funct3 == "010"):
                    res = rs1Val < immVal
                    self.myRF.writeRF(rdVal, res)

                # SLTIU
                elif (funct3 == "011"):
                    res = rs1Val < immVal
                    self.myRF.writeRF(rdVal, res)

                # XORI
                elif (funct3 == "100"):
                    res = (rs1Val ^ immVal) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)

                # ORI
                elif (funct3 == "110"):
                    res = (rs1Val | immVal) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)
                    if (self.cycle == 32):
                        print("here:",imm)

                # ANDI
                elif (funct3 == "111"):
                    res = (rs1Val & immVal) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)

                # SLLI
                elif (funct3 == "111"):
                    res = (rs1Val << immVal) & 0xffffffff
                    self.myRF.writeRF(rdVal, res)

        self.nextState.IF["PC"] += 4
        # if self.state.IF["nop"]:
        #     self.halted = True

        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
            
        self.state.IF["PC"] = self.nextState.IF["PC"] #The end of the cycle and updates the current state with the values calculated in this cycle
        self.state.IF["nop"] = self.nextState.IF["nop"] #The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")
        
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir + "/FS_", imem, dmem)
        self.opFilePath = ioDir + "/StateResult_FS.txt"

    def step(self):
        # Your implementation
        # --------------------- WB stage ---------------------
        
        
        # --------------------- MEM stage --------------------
        
        
        
        # --------------------- EX stage ---------------------
        
        
        
        # --------------------- ID stage ---------------------
        
        
        
        # --------------------- IF stage ---------------------
        
        self.halted = True
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True
        
        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
        
        self.state = self.nextState #The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
        printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
        printstate.extend(["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()])
        printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
        printstate.extend(["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()])

        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

if __name__ == "__main__":
     
    #parse arguments for input file location
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

    while(True):
        if not ssCore.halted:
            ssCore.step()
        
        if not fsCore.halted:
            fsCore.step()

        if ssCore.halted and fsCore.halted:
            break
    
    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()