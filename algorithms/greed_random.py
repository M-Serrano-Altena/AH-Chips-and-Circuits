from classes.chip import *
from classes.wire import *
from algorithms.utils import *
import random


# explanation of algorithm:
# we first make wire connections shortest possible at random wire order, also shortest routes are created at random
# if shortest possible not possible check for less short for each cable at random iteratively (offset + 1, 2, 3 untill k)
# if still no solution found, and allow_short_circuit = True, we connect ignoring short circuit
# we repeat algorithm until chip.not_full_connected is false
# optional: sort wires, first fills in the wires with the highest manhatthan distance

def greed_random_algo(chip: Chip, max_offset: int = 5, allow_short_circuit: bool = False) -> None:

    # we start increasing the offset iteratively after having checked each wire
    for offset in range(max_offset +1):

        # we shuffle the order of wires to fill in connections at random order
        random.shuffle(chip.wires)

        print(f"Checking offset: {offset}")

        for wire in chip.wires:
            # wire is already connected so we skip
            if wire.is_wire_connected():
                continue 

            start = wire.gates[0]  # gate1
            end = wire.gates[1]    # gate2

            # we overwrite the coords to be safe, since we are trying a new set:
            wire.coords = [start, end]

            # first we attempt to find the shortest route 
            path = bfs_route(chip, start, end, offset = offset, allow_short_circuit=False)

            # if path is able to be found, and if this is the minimal path we use shortest_cable to generate a random shortest wire
            if path is not None and offset == 0:
                shortest_cable(wire)

            elif path is not None:
                print(f"Found shortest route with offset = {offset} and for wire = {wire.gates}")
                # we have found a viable path and insert the coords in the wire
                for coord in path:
                    wire.append_wire_segment(coord)
        
    # if we have not found a route for a wire with this max offset, we allow short_circuit
    if allow_short_circuit:
        for wire in chip.wires:
            if not wire.is_wire_connected():

                start = wire.gates[0]  # gate1
                end = wire.gates[1]    # gate2

                force_path = bfs_route(chip, start, end, offset=1000, allow_short_circuit=True)
                # we add the path coords to the wire
                if force_path is not None:
                    print(f"Found route while allowing short circuit")
                    for coord in force_path:
                        wire.append_wire_segment(coord)

    if chip.not_fully_connected:
        print("Warning: Not all wires were able to be connected")
    else:
        print("All wires are connected")
