from src.classes.chip import *
from src.classes.wire import *
from src.algorithms.utils import *
from collections import deque
import random

class Greed:
    """
    First: makes wire connections shortest possible without any short circuit (offset = 0)
    If shortest possible not possible: check for less short for each cable iteratively (offset + 2, 4, 6 untill k)
    If still no solution found (and allow_short_circuit = True): we connect ignoring short circuit
    Optional: sort wires, first fills in the wires with the lowest manhatthan distance
    """

    def __init__(self, chip: "Chip", max_offset: int = 6, allow_short_circuit: bool = False, sort_wires: bool = False):
        self.chip = chip
        self.max_offset = max_offset
        self.allow_short_circuit = allow_short_circuit
        self.sort_wires = sort_wires

    def get_wire_order(self, wires: list[Wire]) -> list[Wire]:
        """
        Return the wires in the order they should be processed.
        """
        if self.sort_wires:
            wires.sort(
                key=lambda w: manhattan_distance(w.coords[0], w.coords[1]),
                reverse=False)
        return wires

    def run(self) -> None:

        # we first sort the wires if needed
        self.get_wire_order(self.chip.wires)

        # we start increasing the offset iteratively after having checked each wire
        # note: it is impossible for the offset to be uneven and still have a valid connection, thus we check only for even values
        for offset in range(0, self.max_offset, 2):
            print(f"Checking offset: {offset}")

            # in greed_random this randomizes the order again per offset-check
            self.chip.wires = self.get_wire_order(self.chip.wires)

            for wire in self.chip.wires:
                # wire is already connected so we skip
                if wire.is_wire_connected():
                    continue 

                start = wire.gates[0]  # gate1
                end = wire.gates[1]    # gate2

                # we overwrite the coords to be safe, since we are trying a new set:
                wire.coords = [start, end]

                # we attempt to find the route breath first 
                path = self.bfs_route(self.chip, start, end, offset = offset, allow_short_circuit=False)

                # if path is possible, we branch off to add option to randomize for child
                if path is not None and offset == 0:
                    path = self.shortest_cable(self.chip, start, end, offset = offset, allow_short_circuit=False)

                    # we were not able to find a route by randomization
                    if path is None:
                        path = self.bfs_route(self.chip, start, end, offset = offset, allow_short_circuit=False)

                if path is not None:
                    print(f"Found shortest route with offset = {offset} and for wire = {wire.gates}")
                    # we have found a viable path and insert the coords in the wire
                    for coord in path:
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
                        print(f"Found route while allowing short circuit")
                        for coord in force_path:
                            wire.append_wire_segment(coord)

        if self.chip.not_fully_connected:
            print("Warning: Not all wires were able to be connected")
        else:
            print("All wires are connected")
            print(f"Status of wire collision: {self.chip.grid_has_wire_collision()}")

    def bfs_route(self, 
        chip: 'Chip', start: Coords_3D, end: Coords_3D, 
        offset: int=0, allow_short_circuit: bool=False, max_only: bool = False) -> list[Coords_3D]|None:
        """
        We use a breath first technique to find a route based on the Manhattan technique with an added max_extra_length to the minimal length of the route.
        If we have found a path, we return the path as a list of tuples (without gate coords), otherwise we return None

        Optional: boolian to the function to allow or not allow short circuiting of the wire. 
        Optional: boolian to find only paths of certain length (minimal + offset)
        
        """

        manhattan_dist = manhattan_distance(start, end)
        limit = manhattan_dist + offset

        # queue consists of tuple entries of (current node, [path])
        queue = deque([(start, [start])])
        visited = set([start])

        wire_gates = {start, end}

        while queue:
            current, path = queue.popleft()
            if current == end and max_only is False:
                # we have made it to the end and return the path to the end
                return path[1:-1] if len(path) > 2 else []
            
            if current == end and max_only is True and len(path) == limit:
                # max_only option: only returning when length of path is equal to a certain length (minimal + offset)
                return path[1:-1] if len(path) > 2 else []

            # if path is longer than limit, we prune
            if len(path) > limit:
                continue

            for neighbour in self.get_neighbours(chip, current):
                if neighbour not in visited:
                    # if neighbour is occupied and we do not allow short circuit we continue, otherwise we save option
                    if not allow_short_circuit and self.is_occupied(chip, neighbour, own_gates=wire_gates):
                        continue
                    
                    # if wiresegment cause wire_collision we continue 
                    if self.wire_collision(chip, neighbour, current):
                        continue

                    visited.add(neighbour)
                    # we add the current node and path to the queue
                    queue.append((neighbour, path + [neighbour]))

        return None
    
    @staticmethod
    def wire_collision(chip: Chip, neighbour: Coords_3D, current: Coords_3D) -> bool:
        """Checks if wiresegment causes a collision in chip"""

        # check if the line piece already exists in chip, if it does we skip 
        for wire in chip.wires:
            for i in range(len(wire.coords) - 1):
                # two consecutive coords in the wire
                wire_seg_1 = wire.coords[i]
                wire_seg_2 = wire.coords[i + 1]
                
                # we check if linepiece is in wire.coords, if so break out of loops and continue checking other neighbours
                if (wire_seg_1 == current and wire_seg_2 == neighbour) or (wire_seg_1 == neighbour and wire_seg_2 == current):
                    return True
                
        return False
        
    @staticmethod    
    def get_neighbours(chip: 'Chip', coord: Coords_3D) -> list[Coords_3D]:
        """
        Return valid neighboring coordinates in 3D (±x, ±y, ±z), 
        ensuring we stay within the grid boundaries.
        """
        (x, y, z) = coord

        possible_moves = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
        neighbours = []
        
        for (dx, dy, dz) in possible_moves:

            (nx, ny, nz) = (x + dx, y + dy, z + dz)

            # we check if options are within boundries of chip, if so we add to neighbours
            if (0 <= nx < chip.grid_size_x 
                and 0 <= ny < chip.grid_size_y 
                and 0 <= nz < chip.grid_size_z):

                neighbours.append((nx, ny, nz))

        return neighbours
    
    @staticmethod
    def gate_occupied(chip: 'Chip', coord: Coords_3D, own_gates: set[Coords_3D] = None) -> bool:
        """
        Checks if 'coord' is occupied by any gate, except its own
        """

        # if coord is own_gate return false
        if own_gates and (coord in own_gates): 
            return False
        
        # if gate is in general gate coords, return true
        gate_coords = set(chip.gates.values())
        if coord in gate_coords:
            return True
        
        return None
    
    @staticmethod
    def is_occupied(chip: 'Chip', coord: Coords_3D, own_gates: set[Coords_3D] = None) -> bool:
        """ 
        Checks if `coord` is already occupied by any wire
        (Optionally checks if the coord is its own gate, to return false since occupation is from its own wire.) 
        """

        # check if gate is occupied, or own gate or none
        gate_occupied = Greed.gate_occupied(chip, coord, own_gates)

        if gate_occupied is not None:
            return gate_occupied

        for wire in chip.wires:
            if coord in wire.coords:
                return True
        return False
    
    def shortest_cable(self, 
        chip: 'Chip', start: Coords_3D, end: Coords_3D, 
        offset: int=0, allow_short_circuit: bool=False, max_only: bool = False) -> list[Coords_3D]|None:

        return self.bfs_route(chip, start, end, offset, allow_short_circuit, max_only)
    

class Greed_random(Greed):
    """
    we first make wire connections shortest possible at random wire order, also shortest routes are created at random
    if shortest possible not possible check for less short for each cable at random iteratively (offset + 2, 4, 6 untill k)
    if still no solution found, and allow_short_circuit = True, we connect ignoring short circuit
    """

    def __init__(self, chip: "Chip", max_offset: int = 6, allow_short_circuit: bool = False, sort_wires: bool = False, random_seed: int|None=None):
        # Use Greed class init
        super().__init__(chip, max_offset, allow_short_circuit, sort_wires)
        
        # add a random seed if given
        if random_seed is not None:
            random.seed(random_seed)

    def get_wire_order(self, wires):

        random.shuffle(wires)

        return wires
    
    def shortest_cable(self, 
        chip: 'Chip', start: Coords_3D, end: Coords_3D, 
        offset: int=0, allow_short_circuit: bool=False, max_only: bool = False) -> list[Coords_3D]|None:
        """Adds a shortest possible wire route to the wire variable (chosen at random)"""

        random_limit = 1000

        # we calculate how many steps we need to make in each ditrection
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dz = end[2] - start[2]

        # now we create a list of moves needed to be made:

        moves = []

        for _ in range(abs(dx)):
            moves.append(((1, 0, 0) if dx > 0 else (-1, 0, 0)))
        for _ in range(abs(dy)):
            moves.append((0, 1, 0) if dy > 0 else (0, -1, 0))
        for _ in range(abs(dz)):
            moves.append(((0, 0, 1) if dz > 0 else (0, 0, -1)))

        # we have all our moves we need to make for the shortest route, now we shuffle the order to randomize route 

        counter = 0

        while counter < random_limit:

            # each try we shuffle the minimized route to find a random path that avoids collision and short circuit
            counter += 1
            path = []
            current_coord = start
            random.shuffle(moves)

            for move in moves:
                
                previous_coord = current_coord
                current_coord = tuple(current_coord[i] + move[i] for i in range(len(current_coord)))

                # continue if collision is found
                if self.wire_collision(chip, previous_coord, current_coord):
                    continue
                
                # if short circuit is not allowed, we continue if we short circuit
                if not allow_short_circuit:
                    if self.is_occupied(chip, current_coord, [start,end]):
                        continue
                
                path.append(current_coord)
            
            # return path if it isnt empty and last entry is gate
            if len(path) != 0 and path[-1] == end:
                return path[:-1]
        
        return None
    

