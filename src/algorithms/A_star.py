from src.classes.chip import Chip
from src.algorithms.greed import Greed
from src.algorithms.utils import Coords_3D, INTERSECTION_COST, COLLISION_COST, manhattan_distance
import heapq
import itertools
from math import inf, perm
import random

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

class A_star_optimize(A_star):
    """
    An algorithm using A* to optimize a given chip configuration.
    
    This algorithm optimizes a completed chip by reducing wire costs. 
    It removes and reroutes multiple wires simultaneously to achieve a lower cost.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.current_cost = self.chip.calc_total_grid_cost()
        self.best_wire_coords: list[list[Coords_3D]] = [wire.coords_wire_segments for wire in self.chip.wires]
        self.lowest_cost = self.current_cost
        self.previous_lowest_cost = self.current_cost

    def optimize(self, reroute_n_wires: int, start_temperature: int=0, alpha: int=0.99) -> None:
        """
        Optimize the chip by rerouting a specified number of wires with optional
        simulated annealing parameters for temperature and cooling rate.

        Args:
            reroute_n_wires (int): Number of wires to reroute simultaneously.
            start_temperature (int): Initial temperature for simulated annealing.
            alpha (int): Cooling rate for simulated annealing.
        """
        self.start_temperature = start_temperature
        self.alpha = alpha
        for i in range(1, reroute_n_wires + 1):
            improved = True
            cycle = 1
            self.temperature = self.start_temperature

            # keep rerouting until lowest cost doesn't improve in a cycle
            while improved:
                # each cycle, the temperature resets
                self.temperature = self.start_temperature
                print(f"optimizing {i} wire(s) at a time | cycle {cycle}")
                improved = self.optimize_n_wires_at_at_time(amount_of_wires=i, switch_equal_configs=cycle == 1)
                cycle += 1

        self.chip.reset_all_wires()
        self.chip.add_entire_wires(self.best_wire_coords)

    
    def optimize_n_wires_at_at_time(self, amount_of_wires: int, switch_equal_configs: bool=False) -> bool:
        """
        Optimize a specific number of wires by rerouting them to reduce cost or intersections.

        Args:
            amount_of_wires (int): Number of wires to optimize in a single pass.
            switch_equal_configs (bool): If True, allow switching configurations with equal costs.

        Returns:
            bool: True if a better configuration is found, False otherwise.
        """
        amount_of_permutations = perm(len(self.chip.wires), amount_of_wires)
        for i, wires in enumerate(itertools.permutations(self.chip.wires, r=amount_of_wires)):
            if i % 1000 == 0:
                print(f"wire combo {i} out of {amount_of_permutations} permutations")

            revert = False
            # snapshot old wire states
            old_wire_coords = [wire.coords_wire_segments[:] for wire in wires]
            old_intersection_num = self.chip.get_wire_intersect_amount()
            new_cost = self.lowest_cost

            # 1) remove old wires from chip
            self.chip.reset_wires(wires)

            for wire in wires:
                # 2) attempt A* for a new, hopefully shorter route.
                start, end = wire.gates[0], wire.gates[-1]
                new_path = self.shortest_cable(self.chip, start, end, allow_short_circuit=True)

                # If A* doesn't yield a new path, skip
                if not new_path:
                    revert = True
                    break

                wire.append_wire_segment_list(new_path)
                self.chip.add_wire_segment_list_to_occupancy(new_path, wire)

            # 3) if new path succesful, check amount of intersections
            if not revert:
                new_intersection_num = self.chip.get_wire_intersect_amount()
                if self.temperature == 0:
                    revert = new_intersection_num > old_intersection_num

            # if amount of intersections hasn't increased, check the cost
            if not revert:
                new_cost = self.chip.calc_total_grid_cost()

            # for simulated annealing
            if self.temperature != 0 and not revert:
                revert = not self.accept_new_config(new_cost=new_cost)

            # non-simulated annealing
            elif not revert:
                if switch_equal_configs:
                    revert = new_cost > self.lowest_cost
                else:
                    revert = new_cost >= self.lowest_cost

            # revert back to old configuration
            if revert or not self.chip.is_fully_connected():
                for wire, old_coords in zip(wires, old_wire_coords):
                    self.chip.reset_wire(wire)
                    wire.append_wire_segment_list(old_coords)
                    self.chip.add_wire_segment_list_to_occupancy(old_coords, wire)

            # keep current change
            else:
                if new_cost != self.current_cost:
                    print(f"new cost: {new_cost} | lowest cost = {self.lowest_cost}")
                self.current_cost = new_cost
                if new_cost < self.lowest_cost:
                    self.lowest_cost = new_cost
                    self.best_wire_coords = [wire.coords_wire_segments for wire in self.chip.wires]

            if self.temperature != 0:
                self.temperature = self.exponential_cooling(iterations=i, total_permutations=amount_of_permutations)


        if self.lowest_cost == self.previous_lowest_cost:
            return False
        
        self.previous_lowest_cost = self.lowest_cost
        return True
    
    @staticmethod
    def acceptance_probability(new_cost: int, old_cost: int, temperature: int) -> int:
        """
        Calculate the acceptance probability for a new configuration in simulated annealing.

        Args:
            new_cost (int): Cost of the new configuration.
            old_cost (int): Cost of the current configuration.
            temperature (int): Current temperature in simulated annealing.

        Returns:
            int: Acceptance probability for the new configuration.
        """
        if new_cost < old_cost:
            return 1

        return 2 ** ((old_cost - new_cost) / temperature)
    
    def accept_new_config(self, new_cost: int) -> bool:
        """
        Decide whether to accept a new configuration based on simulated annealing.

        Args:
            new_cost (int): Cost of the new configuration.

        Returns:
            bool: True if the new configuration is accepted, False otherwise.
        """
        rand_num = random.random()
        acceptance_prob = self.acceptance_probability(new_cost, self.current_cost, self.temperature)
        return rand_num < acceptance_prob

    def exponential_cooling(self, iterations: int, total_permutations: int) -> int:
        """
        Compute the new temperature based on exponential cooling.

        Args:
            iterations (int): Current iteration index.
            total_permutations (int): Total number of permutations being processed.

        Returns:
            int: New temperature after cooling.
        """
        return self.start_temperature * (self.alpha ** (iterations / total_permutations * 1500))