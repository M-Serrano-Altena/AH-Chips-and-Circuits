from src.classes.chip import *
from src.classes.wire import *
from src.algorithms.utils import *
from collections import deque
import random
from numpy import sign, inf
import copy

class Greed:
    """
    First: makes wire connections shortest possible without any short circuit (offset = 0)
    If shortest possible not possible: check for less short for each cable iteratively (offset + 2, 4, 6 untill k)
    If still no solution found (and allow_short_circuit = True): we connect ignoring short circuit
    Optional: sort wires, first fills in the wires with the lowest manhatthan distance
    """

    def __init__(self, chip: "Chip", max_offset: int = 6, allow_short_circuit: bool = False, sort_wires: bool = False, shuffle_wires: bool=False, print_log_messages: bool=False):
        self.chip = chip
        self.chip_og = copy.deepcopy(self.chip)
        self.max_offset = max_offset
        self.allow_short_circuit = allow_short_circuit
        self.sort_wires = sort_wires
        self.shuffle_wires = shuffle_wires
        self.print_log_messages = print_log_messages

    def get_wire_order(self, wires: list[Wire]) -> list[Wire]:
        """
        Return the wires in the order they should be processed.
        """
        if self.sort_wires:
            wires.sort(
                key=lambda w: manhattan_distance(w.coords_wire_segments[0], w.coords_wire_segments[-1]),
                reverse=False)
            
        elif self.shuffle_wires:
            random.shuffle(wires)

        return wires
    
    def run_random_netlist_orders(self, iterations: int) -> Chip:
        self.sort_wires = False
        self.shuffle_wires = True
        self.print_log_messages = False

        lowest_cost = inf
        for i in range(iterations):
            self.chip = copy.deepcopy(self.chip_og)
            netlist = copy.deepcopy(self.chip_og.netlist)
            random.shuffle(netlist)
            self.chip.netlist = netlist
            self.run()
            cost = self.chip.calc_total_grid_cost()
            if cost < lowest_cost and self.chip.is_fully_connected():
                lowest_cost = cost
                best_chip = self.chip

            #print(f"{i}: cost = {cost}, lowest cost = {lowest_cost}")
            
        return best_chip

    def run(self) -> None:

        # we first sort the wires if needed
        self.get_wire_order(self.chip.wires)

        # we start increasing the offset iteratively after having checked each wire
        # note: it is impossible for the offset to be uneven and still have a valid connection, thus we check only for even values
        for offset in range(0, self.max_offset, 2):
            if self.print_log_messages:

                # in greed_random this randomizes the order again per offset-check
                self.chip.wires = self.get_wire_order(self.chip.wires)

            for wire in self.chip.wires:
                # wire is already connected so we skip
                if wire.is_wire_connected():
                    continue 

                start = wire.gates[0]  # gate1
                end = wire.gates[1]    # gate2

                # we add the wire to the occupy grid on position of gates:
                self.chip.add_wire_segment_to_occupancy(coord=start, wire=wire)
                self.chip.add_wire_segment_to_occupancy(coord=end, wire=wire)

                # we overwrite the coords to be safe, since we are trying a new set:
                wire.coords_wire_segments = [start, end]

                # we attempt to find the route breath first 
                path = self.bfs_route(self.chip, start, end, offset = offset, allow_short_circuit=False)

                if path is not None:
                    if self.print_log_messages:
                        print(f"Found shortest route with offset = {offset} and for wire = {wire.gates}")
                    # we have found a viable path and insert the coords in the wire and set occupancy
                    for coord in path:
                        self.chip.add_wire_segment_to_occupancy(coord=coord, wire=wire)
                        wire.append_wire_segment(coord)
            
        # if we have not found a route for a wire with this max offset, we allow short_circuit
        if self.allow_short_circuit:
            for wire in self.chip.wires:
                if not wire.is_wire_connected():

                    start = wire.gates[0]  # gate1
                    end = wire.gates[1]    # gate2

                    force_path = self.bfs_route(self.chip, start, end, offset=1000, allow_short_circuit=True)
                    # we add the path coords to the wire
                    if force_path is not None:
                        if self.print_log_messages:
                            print(f"Found route while allowing short circuit")
                        for coord in force_path:
                            self.chip.add_wire_segment_to_occupancy(coord=coord, wire=wire)
                            wire.append_wire_segment(coord)

        if not self.print_log_messages:
            return
        
        if not self.chip.is_fully_connected():
            pass
        else:
            print("All wires are connected")
            print(f"Has wire collision: {self.chip.get_grid_wire_collision()}")

    def bfs_route(self, 
        chip: 'Chip', start: Coords_3D, end: Coords_3D, 
        offset: int=0, allow_short_circuit: bool=False) -> list[Coords_3D]|None:
        """
        We use a breath first technique to find a route based on the Manhattan technique with an added max_extra_length to the minimal length of the route.
        If we have found a path, we return the path as a list of tuples (without gate coords), otherwise we return None

        Optional: boolian to the function to allow or not allow short circuiting of the wire. 
        Optional: boolian to find only paths of certain length (minimal + offset)
        
        """

        manhattan_dist = manhattan_distance(start, end)
        limit = manhattan_dist + offset

        # queue consists of tuple entries of (current coords, [path])
        queue = deque([(start, [start])])
        visited = set([start])

        while queue:
            current, path = queue.popleft()

            if current == end:
                # we have made it to the end and return the path to the end
                return path[1:-1] if len(path) > 2 else []

            # if path is longer than limit, we prune
            if len(path) > limit:
                continue

            for neighbour in chip.get_neighbours(current):
                # pruning for shortest option
                if neighbour in visited:
                    continue

                occupant_set = chip.get_coord_occupancy(neighbour)

                # skip collisions
                if self.chip.wire_segment_causes_collision(neighbour, current):
                    continue

                # if occupied by a gate which is not its end gate we continue
                if "GATE" in occupant_set and neighbour != end:
                    continue

                # if occupied by wire, and we do not allow short circuit, we continue
                if not allow_short_circuit and len(occupant_set) > 0 and "GATE" not in occupant_set:
                    continue

                visited.add(neighbour)
                
                # we add the current node and path to the queue
                queue.append((neighbour, path + [neighbour]))

        return None
    

class Greed_random(Greed):
    """
    we first make wire connections shortest possible at random wire order, also shortest routes are created at random
    if shortest possible not possible check for less short for each cable at random iteratively (offset + 2, 4, 6 untill k)
    if still no solution found, and allow_short_circuit = True, we connect ignoring short circuit
    """

    def __init__(self, chip: "Chip", max_offset: int = 10, allow_short_circuit: bool = False, sort_wires: bool = False, random_seed: int|None=None):
        # Use Greed class init
        super().__init__(chip, max_offset, allow_short_circuit, sort_wires)
        
        # add a random seed if given
        if random_seed is not None:
            random.seed(random_seed)

    def get_wire_order(self, wires):

        random.shuffle(wires)

        return wires
    
    def bfs_route(self, 
        chip: 'Chip', start: Coords_3D, end: Coords_3D, 
        offset: int=0, allow_short_circuit: bool=False) -> list[Coords_3D]|None:
        """
        We use a breath first technique to find a route based on the Manhattan technique with an added max_extra_length to the minimal length of the route.
        If we have found a path, we return the path as a list of tuples (without gate coords), otherwise we return None

        Optional: boolian to the function to allow or not allow short circuiting of the wire. 
        Optional: boolian to find only paths of certain length (minimal + offset)
        
        """

        manhattan_dist = manhattan_distance(start, end)
        limit = manhattan_dist + offset

        # queue consists of tuple entries of (current coords, [path])
        queue = deque([(start, [start])])
        visited = set([start])

        while queue:
            current, path = queue.popleft()
            neighbours = chip.get_neighbours(current)
            random.shuffle(neighbours)

            if current == end:
                # we have made it to the end and return the path to the end
                return path[1:-1] if len(path) > 2 else []

            # if path is longer than limit, we prune
            if len(path) > limit:
                continue

            for neighbour in neighbours:
                # pruning for shortest option
                if neighbour in visited:
                    continue

                occupant_set = chip.get_coord_occupancy(neighbour)

                # skip collisions
                if self.chip.wire_segment_causes_collision(neighbour, current):
                    continue

                # if occupied by a gate which is not its end gate we continue
                if "GATE" in occupant_set and neighbour != end:
                    continue

                # if occupied by wire, and we do not allow short circuit, we continue
                if not allow_short_circuit and len(occupant_set) > 0 and "GATE" not in occupant_set:
                    continue

                visited.add(neighbour)
                
                # we add the current node and path to the queue
                queue.append((neighbour, path + [neighbour]))

        return None
