from src.classes.chip import Chip
from src.algorithms.greed import Greed
from src.algorithms.utils import Coords_3D, INTERSECTION_COST, COLLISION_COST, manhattan_distance
import heapq

class A_star(Greed):
    """
    A* pathfinding algorithm implementation for routing wires in a chip
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # uses a heap structure with 
        self.frontier = []

    def get_existing_path_cost(self, path: list[Coords_3D]) -> int:
        """
        Calculate the cost of the existing path
        """
        return len(path) - 1
    
    def get_extra_wire_cost(self, path: list[Coords_3D]) -> int:
        """
        Calculate the extra cost for the current node due to intersections or collisions
        """

        # gate can't intersect or have a collision
        if path[-1] in self.chip.gate_coords:
            return 0

        extra_cost = 0

        current_coords = path[-1]
        parent_coords = path[-2]

        current_occupancy_set = self.chip.get_coord_occupancy(current_coords, exclude_gates=True)

        if current_occupancy_set:
            extra_cost += INTERSECTION_COST

            if self.chip.wire_segment_causes_collision(current=current_coords, neighbour=parent_coords):
                extra_cost += COLLISION_COST

        return extra_cost

    
    def heuristic_function(self, path: list[Coords_3D], goal_coords: Coords_3D) -> int:
        """
        Calculate the heuristic cost for the current node
        
        Args:
            current_node (Node): The current node
            goal_coords (Coords_3D): The goal coordinates
        
        Returns:
            int: The total heuristic cost including: manhattan distance, path cost, and extra cost
        """
        manhattan_dist = manhattan_distance(path[-1], goal_coords)
        exising_path_cost = self.get_existing_path_cost(path)
        extra_cost = self.get_extra_wire_cost(path)
        return manhattan_dist + exising_path_cost + extra_cost
        
    def run(self) -> None:

        # we first sort the wires if needed
        self.get_wire_order(self.chip.wires)

        # we start increasing the offset iteratively after having checked each wire
        # note: it is impossible for the offset to be uneven and still have a valid connection, thus we check only for even values

        if self.chip.is_fully_connected():
            if self.print_log_messages:
                print("All wires are connected")
                print(f"Has wire collision: {self.chip.get_grid_wire_collision()}")

            return

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

            # we attempt to find the route with A* algorithm
            path = self.shortest_cable(self.chip, start, end, allow_short_circuit=True)

            if path is not None:
                if self.print_log_messages:
                    print(f"Found shortest route for wire = {wire.gates}")
                # we have found a viable path and insert the coords in the wire and set occupancy
                self.chip.add_wire_segment_list_to_occupancy(path, wire)
                wire.append_wire_segment_list(path)

        if not self.print_log_messages:
            return
        
        if not self.chip.is_fully_connected():
            print("Warning: Not all wires were able to be connected")
        else:
            print("All wires are connected")
            print(f"Has wire collision: {self.chip.get_grid_wire_collision()}")

    

    def shortest_cable(self, 
        chip: 'Chip', start_coords: Coords_3D, end_coords: Coords_3D, 
        offset: int=0, allow_short_circuit: bool=True) -> list[Coords_3D]|None:

        self.frontier = []

        path = [start_coords]
        visited = set([start_coords])

        start_cost = self.heuristic_function(path, end_coords)

        heapq.heappush(self.frontier, (start_cost, start_coords, path))

        while self.frontier:
            cost, current_coords, path = heapq.heappop(self.frontier)
            path_set = set(path)

            if current_coords == end_coords:
                # we have made it to the end and return the path to the end
                return path[1:-1] if len(path) > 2 else []

            for neighbour_coords in self.chip.get_neighbours(current_coords):
                # pruning for shortest option
                if neighbour_coords in visited:
                    continue

                if neighbour_coords in path_set:
                    continue

                occupant_set = chip.get_coord_occupancy(neighbour_coords)

                # skip collisions
                if self.chip.wire_segment_causes_collision(neighbour_coords, current_coords):
                    continue

                # we skip coords that have gates other than the end goal
                if "GATE" in occupant_set and neighbour_coords != end_coords:
                    continue

                # if occupied by wire, and we do not allow short circuit, we continue
                if not allow_short_circuit and len(occupant_set) > 0 and "GATE" not in occupant_set:
                    continue
                
                neighbour_path = path + [neighbour_coords]
                neighbour_cost = self.heuristic_function(path=neighbour_path, goal_coords=end_coords)

                # we add the current cost, coords and path to the heap
                heapq.heappush(self.frontier, (neighbour_cost, neighbour_coords, neighbour_path))

                visited.add(neighbour_coords)
