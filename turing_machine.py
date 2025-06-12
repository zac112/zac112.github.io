class InfiniteLoop(Exception): pass
class InvalidRule(Exception): pass

class State:
    
    def __init__(self, state):
        back = "<"
        if len(state) != 4:
            raise InvalidRule(f"Sääntö väärin: {','.join(state)}; säännössä pitää olla 4 osaa pilkulla erotettuna, sinulla {len(state)}")
        self.currState, self.transition, self.movement, self.newState = state

        if len(self.transition) < 2:
            raise InvalidRule(f"Sääntö väärin: {','.join(state)}; uudelleenkirjoitusosan pitää olla muotoa x->y")
        self.fromSymbol = self.transition[0]
        self.toSymbol = self.transition[-1]

        if self.movement not in "<_>":
            raise InvalidRule(f"Sääntö väärin: {','.join(state)}; lukupään liike pitää olla joko < tai >")

        self.movement = "<_>".index(self.movement)-1

    def fromSymbolMatches(self, symbol):
        if self.fromSymbol == "_": return True
        return self.fromSymbol==symbol

    def getToSymbol(self, symbol):
        if self.toSymbol == "_": return symbol
        return self.toSymbol

    def getMovement(self):
        return self.movement

    def getCurrentState(self):
        return self.currState

    def getNewState(self):
        return self.newState
        
class Machine:

    def __init__(self, tape, states):
        self.maxSteps = 1000
        self.i = 0
        self.tape = set([i for i,x in enumerate(tape.replace(" ","")) if x=="1"])
        self.states = [State(x) for x in states]
        self.currState = "s1"

        print("<ignore>Kone käynnistyy:")
        self.printTape(ignore=True)

    def run(self, printEndTape=True):
        steps = 0
        while self.currState not in ["A","R"]:
            possibleStates = [x for x in self.states if x.getCurrentState()==self.currState]
            bit = self.getBitOnTape(self.i)
            rule = [x for x in possibleStates if x.fromSymbolMatches(bit)]
            if not rule:
                print(f"<ignore>Nykyinen nauha:")
                self.printTape()
                print(f"<ignore>Ei sääntöä tilalle {self.currState}, symbolille {self.getBitOnTape(self.i)}")
                break            
            
            rule = rule[0]
            self.setBitOnTape(self.i, rule.getToSymbol(bit))
            self.i += rule.getMovement()
            self.currState = rule.getNewState()

            steps += 1
            if steps >= self.maxSteps:
                raise InfiniteLoop("Loputon silmukka")

        print(f"Suoritus loppui tilaan {machine.getState()}.")
        if printEndTape: 
            self.printTape()

    def printTape(self, ignore=False):
        ignore = "<ignore>" if ignore else ""
        if len(self.tape)==0:
            print(f"{ignore}Nauha: Kaikki nollabittejä")
            return
        
        offset = 0 if min(self.tape)>=0 else abs(min(self.tape))
        tapelength = max(self.tape)+offset+1
        tape = ["0"]*tapelength
        for bit in self.tape:
            tape[bit+offset] = "1"
        print(f"{ignore}Nauha:","".join(tape))

    def getState(self):
        return {"s1":"START",
         "A":"ACCEPT",
         "R":"REJECT"}.get(self.currState,self.currState)

    def getBitOnTape(self, index):
        return "1" if index in self.tape else "0"

    def setBitOnTape(self, index, bit):
        if bit == "1":
            self.tape.add(index)
        else:
            self.tape.discard(index)
    
def parseStates(s):
    s = [x.split(",") for x in states.splitlines() if len(x)>0]
    return s

