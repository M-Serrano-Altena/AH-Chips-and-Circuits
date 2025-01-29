from src.classes.chip import Chip
from src.classes.wire import Wire
from src.algorithms.utils import manhattan_distance, Coords_3D
from collections import deque
import random
from numpy import inf

class Greed:
    """
    A greedy algorithm for routing wires on a chip while minimizing path lengths 
    and avoiding short circuits when possible.

    The algorithm follows these steps:
    1. Attempts to connect wires using the shortest possible paths (offset = 0) without short circuits.
    2. If no valid shortest path is found, it incrementally increases the offset (offset + 2, 4, 6, ..., up to `max_offset`),
       allowing slightly longer paths.
    3. If no valid route is found and `allow_short_circuit=True`, it permits short circuits to establish connections.

    Additional behavior:
    - If `sort_wires=True`, wires are processed in ascending order of Manhattan distance.
    - If `shuffle_wires=True`, the order of wire processing is randomized.
    """

    def __init__(
        self, 
        chip: "Chip", 
        max_offset: int = 6, 
        allow_short_circuit: bool = False, 
        sort_wires: bool = False, 
        shuffle_wires: bool = False, 
        print_log_messages: bool = False, 
        **kwargs
    ) -> None:
        """
        Initializes the Greed algorithm with configurable parameters.

        Parameters:
        - chip (Chip): The chip object containing the circuit layout.
        - max_offset (int, optional): The maximum allowed deviation from the shortest route. Default is 6.
        - allow_short_circuit (bool, optional): If True, the algorithm allows short-circuiting when no other routes exist. Default is False.
        - sort_wires (bool, optional): If True, wires are sorted by ascending Manhattan distance before routing. Default is False.
        - shuffle_wires (bool, optional): If True, the order of wire processing is randomized. Default is False.
        - print_log_messages (bool, optional): If True, debug messages are printed during execution. Default is False.
        - **kwargs: Additional arguments for potential subclass extensions.
        """

        self.chip = chip
        self.max_offset = max_offset
        self.allow_short_circuit = allow_short_circuit
        self.sort_wires = sort_wires
        self.shuffle_wires = shuffle_wires
        self.print_log_messages = print_log_messages

    def get_wire_order(self, wires: list[Wire]) -> list[Wire]:
        """
        Determines the order in which wires should be processed.
        Sorting is based on Manhattan distance if sorting is enabled, or wires are shuffled if shuffling is enabled.
        
        Args:
            wires (list[Wire]): A list of wires to be processed.
        
        Returns:
            list[Wire]: The ordered list of wires.
        """
        if self.sort_wires:
            wires.sort(
                key=lambda w: manhattan_distance(w.coords_wire_segments[0], w.coords_wire_segments[-1]),
                reverse=False)
            
        elif self.shuffle_wires:
            random.shuffle(wires)

        return wires
    
    def run_random_netlist_orders(self, iterations: int) -> None:
        """
        Runs multiple randomized wire orders to route the wires, keeping track of the best (lowest cost) solution found.
        
        Args:
            iterations (int): The number of random netlist order attempts to perform.
        """
        self.sort_wires = False
        self.shuffle_wires = True
        self.print_log_messages = False
        best_wire_segment_list = self.chip.wire_segment_list

        lowest_cost = inf
        for i in range(iterations):
            self.chip.reset_all_wires()
            self.run()
            cost = self.chip.calc_total_grid_cost()
            if cost < lowest_cost and self.chip.is_fully_connected():
                lowest_cost = cost
                best_wire_segment_list = self.chip.wire_segment_list
            
            print(f"{i}: cost = {cost}, lowest cost = {lowest_cost}")
            
        self.chip.reset_all_wires()
        self.chip.add_entire_wires(best_wire_segment_list)

    def run(self) -> None:
        """
        Executes the greedy routing algorithm to connect wires while minimizing wire length and avoiding short circuits.  
        Adjusts wire placement iteratively using increasing offsets and, if enabled, allows short circuits as a last resort.
        """

        # we first sort the wires if needed
        self.get_wire_order(self.chip.wires)

        # we start increasing the offset iteratively after having checked each wire
        # Note: it is impossible for the offset to be uneven and still have a valid connection, 
        # i.e. each extra direction must be canceled out eventually, and thus we check only for even values
        for offset in range(0, self.max_offset, 2):
            if self.print_log_messages:
                print(f"Checking offset: {offset}")

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
            print("Warning: Not all wires were able to be connected")
        else:
            print("All wires are connected")
            print(f"Has wire collision: {self.chip.get_grid_wire_collision()}")

    def bfs_route(
        self, 
        chip: 'Chip', 
        start: Coords_3D, 
        end: Coords_3D, 
        offset: int = 0, 
        allow_short_circuit: bool = False
    ) -> list[Coords_3D] | None:
        """
        Uses a breadth-first search (BFS) algorithm to find a path between two points while considering obstacles and constraints.
        
        Args:
            chip (Chip): The chip instance containing wire placement and occupancy information.
            start (Coords_3D): The starting coordinate.
            end (Coords_3D): The target coordinate.
            offset (int, optional): Additional allowed path length beyond the Manhattan distance. Defaults to 0.
            allow_short_circuit (bool, optional): Whether to allow paths that introduce short circuits. Defaults to False.
        
        Returns:
            list[Coords_3D] | None: A list of coordinates representing the path if found, otherwise None.
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
    A greedy routing algorithm that connects wires in a randomized order while 
    still prioritizing the shortest possible connections.

    - The algorithm first attempts to connect wires in a random order using the shortest route.
    - If the shortest route is unavailable, it iteratively increases the allowed route length 
      (by offset + 2, 4, 6, etc., up to 'max_offset').
    - If no valid route is found and `allow_short_circuit=True`, it permits short circuits 
      to complete the connection.

    This class extends `Greed`, but introduces randomness in wire selection and pathfinding.
    """

    def __init__(
        self, 
        chip: "Chip", 
        max_offset: int = 20, 
        allow_short_circuit: bool = False, 
        random_seed: int | None = None, 
        **kwargs
    ):
        """
        Initializes the Greed_random algorithm.

        Parameters:
        - chip (Chip): The chip object containing the circuit layout.
        - max_offset (int, optional): The maximum allowed deviation from the shortest route. Default is 20.
        - allow_short_circuit (bool, optional): If True, the algorithm allows short-circuiting when no other routes exist. Default is False.
        - random_seed (int | None, optional): A seed for randomization to ensure reproducibility. Default is None.
        - **kwargs: Additional arguments passed to the parent class.
        """

        # Use Greed class init
        super().__init__(chip, max_offset, allow_short_circuit, sort_wires=False, shuffle_wires=True)
        
        # set random seed if given
        if random_seed is not None:
            random.seed(random_seed)

    def get_wire_order(self, wires):
        """
        Randomizes the order of wires before routing.

        Parameters:
        - wires (list): A list of wire connections to be routed.

        Returns:
        - list: The input list shuffled randomly.
        """
        random.shuffle(wires)
        return wires
    
    def bfs_route(self, 
        chip: 'Chip', start: Coords_3D, end: Coords_3D, 
        offset: int=0, allow_short_circuit: bool=False) -> list[Coords_3D]|None:
        """
        Performs a breadth-first search (BFS) to find a route between two points using a Manhattan-based heuristic.

        - The search attempts to find the shortest possible route while allowing an optional `offset` 
          that increases the maximum path length.
        - If a valid route is found, it returns a list of coordinates excluding the start and end points.
        - If no route is found, it returns None.
        - If `allow_short_circuit` is enabled, the route can pass through existing wires when necessary.

        Parameters:
        - chip (Chip): The chip object containing the circuit layout.
        - start (Coords_3D): The starting coordinate of the wire.
        - end (Coords_3D): The destination coordinate.
        - offset (int, optional): The extra allowed length beyond the Manhattan distance. Default is 0.
        - allow_short_circuit (bool, optional): If True, short circuits are permitted when necessary. Default is False.

        Returns:
        - list[Coords_3D] | None: The computed path as a list of coordinates (excluding start and end), or None if no path is found.
        """

        manhattan_dist = manhattan_distance(start, end)
        limit = manhattan_dist + offset

        # queue consists of tuple entries of (current coords, [path])
        queue = deque([(start, [start])])
        visited = set([start])

        while queue:
            current, path = queue.popleft()
            neighbours = chip.get_neighbours(current)

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
