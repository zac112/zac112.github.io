import operator
import random

class NBitInt:
    def __init__(self, bits, num=0, unsigned=False):
        self.value = num
        self.bits = bits
        self.bitmask = 2**bits-1
        self.unsigned = unsigned

        if num < 0:
            self.value = abs(num)
            self.value = NBitInt.__complement_impl(self.bits, self.value)

    def __signBit(self):
        if not self.unsigned:
            return (self.value >> (self.bits-1)) & 1
        return 0 # treat first bit as data bit

    def isSigned(self):
        return self.__signBit() != 0

    def isZero(self):
        return self.value == 0

    def splitToArray(self, *args):
        if sum(args) != self.bits:
            raise ValueError("Invalid params: " + repr(args))
        result = []
        mask = self.bitmask

        cumulBits = 0
        for bits in args:
            num = (self.value << cumulBits) & self.bitmask #discard high order bits
            num = num >> (self.bits - bits)
            cumulBits += bits
            result.append(num)

        return result

    def copy(self):
        return NBitInt(self.bits,int(self),self.unsigned)

#OPERATORS
#ARITHMETIC
    @staticmethod
    def __add_impl(x, y, bitmask):
        return (x+y) & bitmask

    def __add__(self, other):
        other = int(other)
        return NBitInt(self.bits,
                       NBitInt.add_impl(self.value, other.value, self.bitmask),
                       unsigned=self.unsigned)

    def __iadd__(self, other):
        other = int(other)
        self.value = NBitInt.__add_impl(self.value, other, self.bitmask)
        return self

    @staticmethod
    def __subtract_impl(lhs, rhs):
        rhs = -rhs
        result = lhs + rhs
        return result

    def __sub__(self, other):
        return NBitInt.subtract_impl(self, other)

    def __isub__(self, other):
        other = -other
        self += other
        return self

    @staticmethod
    def __multiply_impl(bitmask, x, y):
        return (x*y) & bitmask

    def __mul__(self, other):
        other = int(other)
        return NBitInt(self.bits,
                       NBitInt.multiply_impl(self.bitmask, self.value, other),
                       unsigned=self.unsigned)

    def __imul__(self, other):
        other = int(other)
        self.value = NBitInt.__multiply_impl(self.bitmask, self.value, other)
        return self

    @staticmethod
    def __complement_impl(bits, y):
        return 2**bits - y


    def __neg__(self):
        value = NBitInt.__complement_impl(self.bits, self.value)
        return NBitInt(self.bits, value, unsigned=self.unsigned)

    @staticmethod
    def __divide_impl(x, y):
        # print("%i,%i" % (x,y))
        # print("%i", x.isSigned())
        x,y = map(int, map(str, (x,y)))
        result = x//y
        return result

    def __floordiv__(self, other):
        value = NBitInt.divide_impl(self.value, other)
        return NBitInt(self.bits, value, unsigned=self.unsigned)

    def __ifloordiv__(self, other):

        value = NBitInt.__divide_impl(self, other)

        if value < 0:
            value = NBitInt.__complement_impl(self.bits, abs(value))
        self.value = value
        return self

#END ARITHMETIC OPERATORS

#SHIFT OPERATORS

    def __lshift_impl(self, num):
        return (self.value << num) & self.bitmask

    def __lshift__(self, num):
        return NBitInt(self.bits, self.__lshift_impl(num), unsigned=self.unsigned)

    def __ilshift__(self, num):
        self.value = self.__lshift_impl(num)
        return self

    def __rshift__(self, num):
        return NBitInt(self.bits, self.value >> num, unsigned=self.unsigned)

    def __irshift__(self, num):
        self.value >>= num
        return self

    #If one of the operands is unsigned, the result will also be. The result has as many bits as the largest operand
    @staticmethod
    def binop_impl(num1, num2, oper):
        isNbit = [isinstance(x, NBitInt) for x in [num1, num2]]
        bits = 16
        unsigned = True
        val1 = val2 = 0
        if all(isNbit):
            bits = max(num1.bits, num2.bits)
            unsigned = num1.unsigned | num2.unsigned
            val1, val2 = num1.value, num2.value
        elif any(isNbit):
            if isNbit[1]:
                num1,num2 = num2,num1 #swap
            val1, val2 = num1.value, num2
            bits = num1.bits
            unsigned = num1.unsigned
        val = oper(val1, val2)
        return NBitInt(bits, num=val, unsigned=unsigned)

    def __and__(self, other):
        return NBitInt.binop_impl(self, other, operator.__and__)

    def __iand__(self, other):
        self.value = NBitInt.binop_impl(self, other, operator.__and__).value
        return self

    def __or__(self, other):
        return NBitInt.binop_impl(self, other, operator.__or__)

    def __ior__(self, other):
        self.value = NBitInt.binop_impl(self, other, operator.__or__).value
        return self

    def __xor__(self, other):
        return NBitInt.binop_impl(self, other, operator.__xor__)

    def __ixor__(self, other):
        self.value = NBitInt.binop_impl(self, other, operator.__ixor__).value
        return self

#Unary operators
    def __invert__(self):
        return NBitInt(self.bits, num=(self.bitmask - self.value), unsigned=self.unsigned)

    def __pos__(self):
        return self.copy()
#End unary operators

#Built-in functions
    def __abs__(self):
        return NBitInt(self.bits, num=abs(self.value))

    def __int__(self):
        if self.isSigned():
            return -NBitInt.__complement_impl(self.bits, self.value)
        return self.value

    def __oct__(self):
        return oct(self.value)

    def __hex__(self):
        return hex(self.value)

    #Not actually built-in, but it fits here
    def bin(self):
        return bin(self.value)

    def __str__(self):
        return str(int(self))#encoding: utf-8

import re

class MachineException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class MachineSim:
    debug = False
    DATA_BITS = 16
    OP_BITS = 4
    VALUE_BITS = 12
    MIN_ADDRESS = 0
    MAX_ADDRESS = 4095

    def __init__(self, extended=True):
        self.resetRegisters()
        self.resetRam()
        self.extensionsAllowed = extended

    def _getOperationFunc(self, oper):
        try:
            return [func for operation, (bits, func) in MachineSim.OPERATIONS_DEF.items()|MachineSim.OPERATIONS_EXTENDED.items() if int(bits)==int(oper)][0]
        except:
            return self.opr_NOP
    
    def resetRegisters(self):
        self.ACC = NBitInt(self.DATA_BITS, 0)
        self.PC = 0
        self.IR = NBitInt(self.PC)

    def resetRam(self):
        self.MM = [NBitInt(self.DATA_BITS,0) for x in range(self.MIN_ADDRESS, self.MAX_ADDRESS+1)]

    def __updateIR(self):
        self.IR = self.MM[self.PC]

    def loadProgram(self, machineProgram):
        self.currentProgram = machineProgram
        self.PC = machineProgram.getStartAddress()
        self.__copyProgram()
        self.__updateIR()

    def setMemory(self, address, value):
        self.MM[address] = NBitInt(self.DATA_BITS, value)

    def __copyProgram(self):
        for line,ins in self.currentProgram.getProgramBinary().items():
            self.MM[line] = ins.copy()

    def executeNext(self):
        rawOp, rawValue = self.IR.splitToArray(self.OP_BITS, self.VALUE_BITS)
        op = self._getOperationFunc(rawOp)
        value = NBitInt(self.VALUE_BITS, rawValue)
        valueAtAddress=None
        if self.MIN_ADDRESS <= int(value) <= self.MAX_ADDRESS:
            valueAtAddress = self.MM[int(value)].copy()
        op(self, value, valueAtAddress)
        self.__updateIR()

    def incr_PC(self):
        self.PC = self.PC+1

    def opr_NOP(self, address, valueAtAddress):
        if self.debug:
            print (self.oprDebugString("NOP", address))
        self.incr_PC()

    def opr_LOAD(self, address, valueAtAddress):
        if self.debug:
            print (self.oprDebugString("LOAD", address, valueAtAddress))
        self.ACC = valueAtAddress
        self.incr_PC()

    def opr_STORE(self, address, valueAtAddress):
        if self.debug:
            print (self.oprDebugString("STORE", address))
        self.MM[int(address)] = self.ACC.copy()
        self.incr_PC()

    def opr_ADD(self, address, valueAtAddress):
        if self.debug:
            print (self.oprDebugString("ADD", address, valueAtAddress) + " to ACC=" + str(self.ACC))
        self.ACC += valueAtAddress
        self.incr_PC()

    def opr_SUBTRACT(self, address, valueAtAddress):
        if self.debug:
            print (self.oprDebugString("SUBTRACT", address, valueAtAddress) + " from ACC=" + str(self.ACC))
        self.ACC -=valueAtAddress
        self.incr_PC()

    def opr_MULTIPLY(self, address, valueAtAddress):
        if self.debug:
            print (self.oprDebugString("MULTIPLY", address, valueAtAddress) + " with ACC=" + str(self.ACC))
        self.ACC *= valueAtAddress
        self.incr_PC()

    def opr_DIVIDE(self, address, valueAtAddress):
        if self.debug:
            print (self.oprDebugString("DIVIDE", address, valueAtAddress) + " with ACC=" + str(self.ACC))
        self.ACC //= valueAtAddress
        self.incr_PC()

    def opr_JUMP(self, address, valueAtAddress):
        if self.debug:
            print (self.oprDebugString("JUMP", address))
        self.PC = int(address)

    def opr_JUMPZERO(self, address, valueAtAddress):
        if self.debug:
            print (self.oprDebugString("JUMPZERO", address))
        if self.ACC.isZero():
            self.PC = int(address)
        else:
            self.incr_PC()

    def opr_JUMPNEG(self, address, valueAtAddress):
        if self.debug:
            print (self.oprDebugString("JUMPNEG", address))
        if self.ACC.isSigned():
            self.PC = int(address)
        else:
            self.incr_PC()

    def opr_JUMPSUB(self, address, valueAtAddress):
        if self.debug:
            print (self.oprDebugString("JUMPSUB", address))
        self.MM[int(address)] = NBitInt(self.DATA_BITS, self.PC + 1)
        self.PC = int(address)+1

    def opr_RETURN(self, address, valueAtAddress):
        if self.debug:
            print (self.oprDebugString("RETURN", address, valueAtAddress))
        self.PC = int(valueAtAddress)

    def opr_LOADI(self, value, notUsed=None):
        if not self.extensionsAllowed:
            raise MachineException(f"Laajennetut komennot {','.join(MachineSim.OPERATIONS_EXTENDED.keys())} eivät ole käytössä")
        if self.debug:
            print (self.oprDebugString("LOADI", value))
        self.ACC = value
        self.incr_PC()

    def opr_LOADID(self, address, valueAtAddress):
        if not self.extensionsAllowed:
            raise MachineException(f"Laajennetut komennot {','.join(MachineSim.OPERATIONS_EXTENDED.keys())} eivät ole käytössä")
        if self.debug:
            print (self.oprDebugString("LOADID", address, valueAtAddress))
        self.ACC = self.MM[int(valueAtAddress)]
        self.incr_PC()

    def oprDebugString(self, operation, address, valueAtAddress=None):
        s = str(self.PC) + " " + operation + " "
        if valueAtAddress != None:
            s += "("
        s += str(address)

        if valueAtAddress != None:
            s += ")"
            s += "=" + str(valueAtAddress)
            s += "=" + valueAtAddress.bin()
        else:
            s += " ACC=" + str(self.ACC)
        return s

    def run(self, reload=False):
        if reload:
            self.resetRam()
            self.resetRegisters()
            self.loadProgram(self.currentProgram)
        lastIns = None
        while not self.IR.isZero():
            lastIns = self.PC
            try:
                self.executeNext()
            except MachineException as e:
                print("Virhe tietokoneen suorituksen aikana:",e)
                break

    FI_OPER =  {
        "LATAA": "LOAD",
        "TALLENNA": "STORE",
        "LISÄÄ": "ADD",
        "VÄHENNÄ": "SUBTRACT",
        "KERRO": "MULTIPLY",
        "JAA": "DIVIDE",
        "HYPPY": "JUMP",
        "NOLLAHYPPY": "JUMPZERO",
        "MIINUSHYPPY": "JUMPNEG",
        "OHJELMA": "JUMPSUB",
        "PALAA": "RETURN"
    }
    OPERATIONS_EXTENDED = {
        "LOADI":      (0b1100, opr_LOADI),
        "LOADID":     (0b1101, opr_LOADID)
    }
    OPERATIONS_DEF =  {
        "NOP":        (0b0000, opr_NOP),
        "LOAD":       (0b0001, opr_LOAD),
        "STORE":      (0b0010, opr_STORE),
        "ADD":        (0b0011, opr_ADD),
        "SUBTRACT":   (0b0100, opr_SUBTRACT),
        "MULTIPLY":   (0b0101, opr_MULTIPLY),
        "DIVIDE":     (0b0110, opr_DIVIDE),
        "JUMP":       (0b0111, opr_JUMP),
        "JUMPZERO":   (0b1000, opr_JUMPZERO),
        "JUMPNEG":    (0b1001, opr_JUMPNEG),
        "JUMPSUB":    (0b1010, opr_JUMPSUB),
        "RETURN":     (0b1011, opr_RETURN)              
    }

    OPERATIONS = {keyword : value for keyword, (value,func) in OPERATIONS_DEF.items()|OPERATIONS_EXTENDED.items()}
    
    def disableExtensions(self):
        del self.OPERATIONS_FUNC[self.OPERATIONS_DEF["LOADID"][0]]

    def printState(self, memory=[],ACC=False, IR=False, PC=False):
        s = ""
        if ACC:
            s += "[ACC:"+ str(self.ACC)+ "]"
        if IR:
            s += "[IR:"+ str(self.IR.bin())+ "]"
        if PC:
            s += "<PC:"+ str(self.PC)+ ">"
        if len(memory) > 0:
            for address in memory:
                s += "[M" + str(address) + ":" + str(self.MM[address]) + "]"
        return s

    def readMemory(self, address):
        return int(self.MM[address])

class MachineProgram:
    MIN_ADDRESS = 0 # -1 used only internally, line never executed
    MAX_ADDRESS = 4095
    OPERATOR_ALIGN = 12

    def __init__(self, input):
        self.rawInput = input

        self.valueRegex = re.compile(r"\s*(?P<address>[0-9]+)\s+(?P<value>[0-9]+)(?P<comment>.*)")
        operatorStr = "|".join(MachineSim.OPERATIONS.keys()) +"|"+ "|".join(MachineSim.FI_OPER.keys())
        operatorSyntax = r"\s*(?P<address>[0-9]+)\s+(?P<operator>%s)\s+(?P<value>[0-9]+)?(?P<comment>.*)" % operatorStr
        shorthandSyntax = r"(?P<operator>%s)\s+(?P<value>[0-9]+)?(?P<comment>.*)" % operatorStr
        self.operatorRegex = re.compile(operatorSyntax)
        self.nopRegex = re.compile(r"\s*(?P<address>[0-9]+)\s+(NOP)(?P<comment>.*)")
        self.commentRegex = re.compile(r"\s*#(?P<comment>.*)")
        self.program = self.parse(input)
        self.shorthandRegex = re.compile(shorthandSyntax)

        self.makeBinary()

        self.start = 0
        self.last_address = -1

    def makeBinary(self):
        self.programBinary = dict()
        for line in self.program:
            if len(line) == 2:
                self.programBinary[line[0]] = NBitInt(16, line[1])
            else:
                
                numValue = (line[1] << self.OPERATOR_ALIGN) | line[2]
                self.programBinary[line[0]] = NBitInt(16, numValue, unsigned=True)

    def getProgramArray(self):
        return self.program

    def getProgramBinary(self):
        return self.programBinary

    def getStartAddress(self):
        return self.start

    def setStartAddress(self, start):
        self.start = start

    def getLineStr(self, index):
        return "line " + str(index) + ": \"" + self.rawInput[index] + "\""

    def checkSpecialInstruction(self, instruction):
        instruction = instruction.strip().upper()
        if instruction == "DEBUG":
            MachineSim.debug = True
        elif instruction == "HELP":
            print (repr(MachineSim.OPERATIONS.keys()))
        else:
            return False
        return True


    def parseLine(self, input, lineNum):
        if len(input.strip())==0:
            return None
        valueMatch = self.valueRegex.match(input)
        if(valueMatch):
            return [int(valueMatch.group("address")), int(valueMatch.group("value"))]

        operatorMatch = self.operatorRegex.match(input)
        if(operatorMatch):
            operator = operatorMatch.group("operator")
            operator = MachineSim.OPERATIONS.get(MachineSim.FI_OPER.get(operator, operator)) 
            value = int(operatorMatch.group("value"))
            address = int(operatorMatch.group("address"))
            self.last_address = address
            return [address, operator, value]
        # shorthandMatch = self.shorthandRegex.match(input)
        # if shorthandMatch:
        #     operator = shorthandMatch.group("operator")
        #     value = int(shorthandMatch.group("value"))
        #     address = self.last_address+1
        #     self.last_address += 1
        #     return [address, operator, value]
        nopMatch = self.nopRegex.match(input)

        if nopMatch:
            return [int(nopMatch.group("address")), MachineSim.OPERATIONS.get("NOP"), 1]
        if self.commentRegex.match(input):
            return None
        if(self.checkSpecialInstruction(input)):
            return None

        raise MachineException("Syntax error on line \"" + str(lineNum) + ":" + self.getLineStr(lineNum))

    def parse(self, input):
        input = [x for x in input.split("\n")]
        self.rawInput = input
        program = []
        for i in range(0, len(input)):

            line = input[i]
            parsedLine = self.parseLine(line, i)
            if(parsedLine):
                if parsedLine[0] < self.MIN_ADDRESS or parsedLine[0] > self.MAX_ADDRESS:
                    raise MachineException("Invalid address on line: " + line)
                program.append(parsedLine)
            continue

        return program



