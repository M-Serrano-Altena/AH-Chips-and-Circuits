from classes.chip import *
from classes.wire import *
from utils import *

# first we load in the configuration of the problem. 

Chip0 = Chip(base_data_path= "/data", chip_id= 0, net_id= 1)

# explanation of algorithm:
# make wire connections shortest possible without any short circuit, follow order of netlist
# if shortest possible not possible check for not shortest possible and still no short circuit
# if no options possible anymore short circuit

for connection in Chip0.netlist:
    continue