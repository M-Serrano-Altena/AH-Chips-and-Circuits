from classes.chip import *
from classes.wire import *
from algorithms.utils import *
from collections import deque

class Greedy:
    """
    Explanation of algorithm:
    we first make wire connections shortest possible without any short circuit (offset = 0)
    if shortest possible not possible check for less short for each cable iteratively (offset + 1, 2, 3 untill k)
    if still no solution found, and allow_short_circuit = True, we connect ignoring short circuit
    we repeat algorithm until chip.not_full_connected is false
    optional: sort wires, first fills in the wires with the lowest manhatthan distance
    """

    def __init__(self, chip: "Chip", max_offset: int = 6, allow_short_circuit: bool = False, sort_wires: bool = False):
        self.chip = chip
        self.max_offset = max_offset
        self.allow_short_circuit = allow_short_circuit
        self.sort_wires = sort_wires

    def run(self) -> None:
        if self.sort_wires:
            self.chip.wires.sort(
            key=lambda w: manhattan_distance(w.coords[0], w.coords[1]),
            reverse=False
            )

        # we start increasing the offset iteratively after having checked each wire
        # note: it is impossible for the offset to be uneven and still have a valid connection, thus we check only for even values
        for offset in range(0, self.max_offset, 2):
            print(f"Checking offset: {offset}")
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
        If we have found a path, we return the path as a list of tuples, otherwise we return None

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

                    # check if the line piece already exists in chip, if it does we skip 
                    in_collision = False
                    for wire in chip.wires:
                        for i in range(len(wire.coords) - 1):
                            # two consecutive coords in the wire
                            wire_seg_1 = wire.coords[i]
                            wire_seg_2 = wire.coords[i + 1]
                            
                            # we check if linepiece is in wire.coords, if so break out of loops and continue checking other neighbours
                            if (wire_seg_1 == current and wire_seg_2 == neighbour) or (wire_seg_1 == neighbour and wire_seg_2 == current):
                                in_collision = True
                                break

                        if in_collision: 
                            break

                    if in_collision:
                        continue

                    visited.add(neighbour)
                    # we add the current node and path to the queue
                    queue.append((neighbour, path + [neighbour]))

        return None
        
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
    def is_occupied(chip: 'Chip', coord: Coords_3D, own_gates: set[Coords_3D] = None) -> bool:
        """ 
        Checks if `coord` is already occupied by any wire
        (Optionally checks if the coord is its own gate, to return false since occupation is from its own wire.) 
        """

        if own_gates and (coord in own_gates):
            return False

        gate_coords = set(chip.gates.values())
        if coord in gate_coords:
            return True

        for wire in chip.wires:
            if coord in wire.coords:
                return True
        return False
