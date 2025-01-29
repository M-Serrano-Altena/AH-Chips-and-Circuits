from src.classes.chip import Chip
from src.algorithms.greed import Greed
from src.algorithms.utils import Coords_3D, INTERSECTION_COST, COLLISION_COST, manhattan_distance
import heapq
import itertools
from math import inf, perm
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.wire import Wire

class A_star(Greed):
    """
    A* pathfinding algorithm implementation for routing wires in a chip.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # uses a heap structure with 
        self.frontier = []

    def get_existing_path_cost(self, path: list[Coords_3D]) -> int:
        """
        Compute the cost of an existing path based on its length.

        Args:
            path (list[Coords_3D]): The list of coordinates forming the path.

        Returns:
            int: The cost of the path, equal to the number of segments (length - 1).
        """
        return len(path) - 1
    
    def get_extra_wire_cost(self, path: list[Coords_3D]) -> int:
        """
        Determine additional costs incurred by a wire segment due to intersections or collisions.

        Args:
            path (list[Coords_3D]): The list of coordinates forming the wire path.

        Returns:
            int: The additional cost based on intersections and collisions.
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
        Compute the heuristic cost for A* pathfinding.

        The heuristic cost includes:
        - Manhattan distance to the goal.
        - Existing path cost.
        - Extra cost due to intersections and collisions.

        Args:
            path (list[Coords_3D]): The current path.
            goal_coords (Coords_3D): The coordinates of the goal.

        Returns:
            int: The total heuristic cost.
        """
        manhattan_dist = manhattan_distance(path[-1], goal_coords)
        exising_path_cost = self.get_existing_path_cost(path)
        extra_cost = self.get_extra_wire_cost(path)
        return manhattan_dist + exising_path_cost + extra_cost
        
    def run(self) -> None:
        """
        Execute the A* algorithm to connect all wires in the chip.

        The function iterates through all wires, attempting to find the shortest
        valid route using the A* algorithm. If a path is found, it updates the
        chip's occupancy grid and wire configurations.
        """
        # we first sort the wires if needed
        self.get_wire_order(self.chip.wires)

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

    

    def shortest_cable(
        self, 
        chip: 'Chip', 
        start_coords: Coords_3D, 
        end_coords: Coords_3D,
        allow_short_circuit: bool = True,
        **kwargs
    ) -> list[Coords_3D] | None:
        """
        Find the shortest cable route between two points using A* search.

        Args:
            chip (Chip): The chip instance containing wire and occupancy information.
            start_coords (Coords_3D): The starting coordinates of the wire.
            end_coords (Coords_3D): The destination coordinates of the wire.
            allow_short_circuit (bool, optional): Whether to allow wires to pass through other wires. Defaults to True.

        Returns:
            list[Coords_3D] | None: The computed shortest path or None if no valid path exists.
        """
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
    A variant of the A* algorithm designed to optimize wire placement in a completed chip.

    This algorithm iteratively reroutes existing wires by temporarily removing them
    to minimize total cost.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.current_cost = self.chip.calc_total_grid_cost()
        self.best_wire_coords: list[list[Coords_3D]] = self.chip.wire_segment_list
        self.lowest_cost = self.current_cost
        self.previous_lowest_cost = self.current_cost

    def optimize(
        self, 
        reroute_n_wires: int, 
        start_temperature: int = 0, 
        alpha: float = 0.99, 
        total_permutations_limit: int = 500000, 
        amount_of_random_iterations: int = 20000
    ) -> None:
        """
        Optimize wire routing by rerouting multiple wires simultaneously.

        This method applies an optimization process to reduce total wire cost,
        utilizing simulated annealing if needed.

        Args:
            reroute_n_wires (int): The (max) number of wires to reroute simultaneously.
            start_temperature (int, optional): Initial temperature for simulated annealing. Defaults to 0.
            alpha (float, optional): Cooling rate for simulated annealing. Defaults to 0.99.
            total_permutations_limit (int, optional): Maximum number of wire permutations before switching to random search. Defaults to 500000.
            amount_of_random_iterations (int, optional): Number of random permutations to try if permutation limit is exceeded. Defaults to 20000.
        """
        print("Starting A* optimization...")
        self.start_temperature = start_temperature
        self.alpha = alpha
        for i in range(1, reroute_n_wires + 1):
            improved = True
            cycle = 1
            self.temperature = self.start_temperature
            total_permutations = perm(len(self.chip.wires), i)

            # keep rerouting until lowest cost doesn't improve in a cycle
            while total_permutations < total_permutations_limit and improved:
                # each cycle, the temperature resets
                self.temperature = self.start_temperature
                print(f"optimizing {i} wire(s) at a time | cycle {cycle}")
                improved = self.optimize_n_wires_all_permutations(amount_of_wires=i, switch_equal_configs=cycle == 1)
                cycle += 1

            while total_permutations >= total_permutations_limit and improved:
                # each cycle, the temperature resets
                self.temperature = self.start_temperature
                print(f"optimizing {i} wire(s) at a time | cycle {cycle}")
                improved = self.optimize_n_wires_random_permutations(amount_of_wires=i, switch_equal_configs=cycle == 1, amount_of_iterations=amount_of_random_iterations)
                cycle += 1

        

        self.chip.reset_all_wires()
        self.chip.add_entire_wires(self.best_wire_coords)

    
    def optimize_n_wires_all_permutations(self, amount_of_wires: int, switch_equal_configs: bool=False) -> bool:
        """
        Optimize wire routing by testing all possible wire permutations.

        This method systematically explores all possible rerouting options
        for a given number of wires and selects the configuration that minimizes cost.

        Args:
            amount_of_wires (int): The number of wires to reroute in each iteration.
            switch_equal_configs (bool, optional): Whether to allow switching configurations with equal cost. Defaults to False.

        Returns:
            bool: True if a better configuration is found, otherwise False.
        """
        total_permutations = perm(len(self.chip.wires), amount_of_wires)
        for i, wires in enumerate(itertools.permutations(self.chip.wires, r=amount_of_wires)):
            self.optimize_n_wires_1_permutation(wires=wires, amount_of_permutations=total_permutations, iteration=i, switch_equal_configs=switch_equal_configs)


        if self.lowest_cost == self.previous_lowest_cost:
            return False
        
        self.previous_lowest_cost = self.lowest_cost
        return True
    
    def optimize_n_wires_random_permutations(self, amount_of_wires: int, amount_of_iterations: int=20000, switch_equal_configs: bool=False) -> bool:
        """
        Optimize wire routing using random wire permutations.

        Instead of checking all possible permutations, this method randomly selects
        wire configurations to reroute, making the process managable for more simultanious wires.

        Args:
            amount_of_wires (int): The number of wires to reroute per iteration.
            amount_of_iterations (int, optional): The number of random permutations to try. Defaults to 20000.
            switch_equal_configs (bool, optional): Whether to allow switching configurations with equal cost. Defaults to False.

        Returns:
            bool: True if an improved configuration is found, otherwise False.
        """
        for i in range(amount_of_iterations):
            wires = random.sample(self.chip.wires, k=amount_of_wires)
            self.optimize_n_wires_1_permutation(wires=wires, amount_of_permutations=amount_of_iterations, iteration=i, switch_equal_configs=switch_equal_configs)


        if self.lowest_cost == self.previous_lowest_cost:
            return False
        
        self.previous_lowest_cost = self.lowest_cost
        return True

    def optimize_n_wires_1_permutation(
        self, 
        wires: list['Wire'], 
        amount_of_permutations: int, 
        iteration: int, 
        switch_equal_configs: bool = False
    ) -> None:
        """
        Attempts to optimize the routing of a given set of wires using A* search and simulated annealing.

        This method removes existing wire routes and recalculates them in an attempt to reduce
        overall wire cost and intersections. It decides whether to keep the new configuration 
        based on cost reduction and simulated annealing criteria.

        Args:
            wires (list[Wire]): List of wires to optimize.
            amount_of_permutations (int): Total number of permutations in the optimization process.
            iteration (int): Current iteration number in the optimization loop.
            switch_equal_configs (bool, optional): If True, allows switching to configurations 
                with equal cost. Defaults to False.

        Returns:
            None: Modifies the chip state in-place.
        """

        if iteration % 1000 == 0:
            print(f"wire combo {iteration} out of {amount_of_permutations} permutations")

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
                print(f"new cost: {new_cost} | previous lowest cost = {self.lowest_cost}")
            self.current_cost = new_cost
            if new_cost < self.lowest_cost:
                self.lowest_cost = new_cost
                self.best_wire_coords = self.chip.wire_segment_list

        if self.temperature != 0:
            self.temperature = self.exponential_cooling(iterations=iteration, total_permutations=amount_of_permutations)
    
    @staticmethod
    def acceptance_probability(new_cost: int, old_cost: int, temperature: int) -> int:
        """
        Compute the probability of accepting a new configuration based on simulated annealing.

        If the new cost is lower than the old cost, the new configuration is always accepted.
        Otherwise, acceptance follows an exponential probability function.

        Args:
            new_cost (int): Cost of the new configuration.
            old_cost (int): Cost of the current configuration.
            temperature (int): Current temperature in the annealing process.

        Returns:
            int: Probability of accepting the new configuration, in the range [0, 1].
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