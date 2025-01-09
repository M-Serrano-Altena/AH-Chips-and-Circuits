

class Wire():

    def __init__(self, chip: Chip):
        self.chip = chip
        self.coords: list[tuple] = []
        self.length: int = 0
        self.gate_connection: bool = False
        self.circular: bool = False
        self.wire_connection: bool = False

    @property
    def gate_connection(self):
        """ checks if gates correspond to the connection in the netlist"""

        netlist = self.chip.netlist
        gates = self.chip.gates
        coords_set = set(self.coords)

        for connection in netlist:
            gate_1 = connection.keys()
            gate_2 = connection.values()

            coords_gate_1 = gates[gate_1]
            coords_gate_2 = gates[gate_2]

            if coords_gate_1 in coords_set and  coords_gate_2 in coords_set:
                return True
            
        return False
 

        ## checks if the self.coords of the wire are corresponding to the assigned gates 
        ## that is get the connection to be made (netlist) and the coordinates of their corresponding gates
        ## if the coordinates of these gates correspond are in the set(self.coords) we have gate_connection = True

    @property
    def length(self):
        """ checks the length of the wire"""
        return len(self.coords) - 1
    
    @property
    def circular(self):
        """ checks if the wire touches itself"""    

        # if this is the case we have duplicates in our coordinates, this a crossing
        if len(self.coords) != len(set(self.coords)):
            return False
        else:
            return True
        
    @property
    def wire_connection(self):

        coords_set = set(self.coords)
        
        for (x,y) in self.coords:
            if (x + 1, y) in coords_set:
                continue
            elif (x - 1, y) in coords_set:
                continue
            elif (x, y + 1) in coords_set:
                continue
            elif (x, y - 1) in coords_set:
                continue
            else:
                return False


    

    




    

    
