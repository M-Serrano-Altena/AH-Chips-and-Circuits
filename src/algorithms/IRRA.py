from src.classes.chip import Chip
from src.algorithms.utils import manhattan_distance, Coords_3D
from src.algorithms.random_algo import Pseudo_random
from src.algorithms.A_star import A_star, A_star_optimize
import random
from math import inf

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.wire import Wire

class IRRA_PR(Pseudo_random):
    """
    Iterative Random Rerouting Algorithm (IRRA):
    This algorithm starts with a random configuration and iteratively tries to reroute wires 
    to minimize short circuits (wire intersections). The algorithm runs for a set number 
    of iterations or until it reaches a solution with an acceptable number of intersections. 
    Optionally, limits can be applied to control the algorithm's efficiency or restrict the initial 
    intersection amount when generating an initial input solution. The initial input solution is generated
    using the Pseudo Random (PR) algorithm.
    """

    def __init__(
        self,
        chip: "Chip",
        iterations: int = 100,
        intersection_limit: int = 0,
        acceptable_intersection: int = 3000,
        early_stopping_patience: int = 999999,
        max_offset: int = 58,
        rerouting_offset: int = 58,
        allow_short_circuit: bool = False,
        A_star_rerouting: bool = False,
        simulated_annealing: bool = False,
        start_temperature: int = 500,
        temperature_alpha: int = 0.9,
        random_seed: int | None = None,
        **kwargs
    ) -> None:
        """
        Initializes the IRRA_PR algorithm with various parameters for rerouting and optimization.

        Args:
            chip: The Chip object to be rerouted.
            iterations: The number of iterations the algorithm will run.
            intersection_limit: The maximum number of intersections allowed for the input solution.
            acceptable_intersection: The maximum acceptable number of wire intersections before stopping.
            early_stopping_patience: The number of iterations to wait without improvement before stopping early.
            max_offset: The maximum offset allowed when rerouting wires.
            rerouting_offset: The offset used for rerouting wires.
            allow_short_circuit: Flag indicating whether short circuits are allowed during rerouting.
            A_star_rerouting: Flag indicating whether A* rerouting should be used.
            simulated_annealing: Flag indicating whether simulated annealing should be used.
            start_temperature: The starting temperature for simulated annealing.
            temperature_alpha: The cooling rate for simulated annealing.
            random_seed: A random seed for reproducibility.
        """
        super().__init__(
            chip=chip,
            max_offset=max_offset,
            allow_short_circuit=allow_short_circuit,
            random_seed=random_seed
        )
        self.chip = chip
        self.iterations = iterations
        self.intersection_limit = intersection_limit
        self.acceptable_intersection = acceptable_intersection
        self.early_stopping_patience = early_stopping_patience
        self.gate_amount = len(self.chip.gates)
        self.A_star_rerouting = A_star_rerouting
        self.simulated_annealing = simulated_annealing
        self.temperature_alpha = temperature_alpha
        self.start_temperature = start_temperature
        self.rerouting_offset = rerouting_offset

        if self.A_star_rerouting:
            self.a_star = A_star(
                chip=chip,
                max_offset=max_offset,
                allow_short_circuit=allow_short_circuit,
            )


        # we use these variables to keep track of the best solution
        self.best_cost = inf   # inf, such that current_cost < best_cost
        self.best_wire_segment_list: list[list[Coords_3D]] = self.chip.wire_segment_list
        self.all_costs = [] # we use all_costs to save cost for parameter research

        if self.A_star_rerouting and self.simulated_annealing:
            raise ValueError("A* rerouting is not compatible with simulated Annealing")

    def run(self) -> Chip:
        """
        Runs the IRRA algorithm. It tries to find an optimal wiring configuration by:
        1) Generating a random configuration.
        2) Rerouting wires to minimize intersections.
        3) Optimizing the wiring cost.
        4) Stopping early if the intersection limit is met or further improvements are not found.

        Returns:
            The Chip object with the best configuration found.
        """
        algo_name_input = "[IRRA input]"
        algo_name_routing = "[IRRA A* routing]" if self.A_star_rerouting else "[IRRA annealing routing]" if self.simulated_annealing else "[IRRA BFS routing]"
        for new_solution_iteration in range(1, self.iterations + 1):
            print(f"{algo_name_input} Starting iteration {new_solution_iteration}/{self.iterations}:")
            improvement_iteration = 0
            optimal_solution_counter = 0 # count the amount of times we encounter the same cost in a row

            # 1) clear occupancy and reset wire paths
            if new_solution_iteration != 1:
                self.chip.reset_all_wires()


            # 2) let parent produce a random wiring
            super().run()

            # repeat this step until we find a configuration that is fully connected 
            # optional) repeat this step until we have wiring that has acceptable intersection amount 
            while (not self.chip.is_fully_connected() or self.chip.get_wire_intersect_amount() >= self.acceptable_intersection):
                self.chip.reset_all_wires()
                super().run()
                print(f"{algo_name_input} Finding configuration: {improvement_iteration}, intersections: {self.chip.get_wire_intersect_amount()}")
                improvement_iteration += 1

            # 3) try to reroute (reduce intersections) in a loop
            print(f"{algo_name_routing} Started rerouting...")
            if self.A_star_rerouting:
                self.intersections_rerouting_A_star()
            else:
                self.intersections_rerouting()

            # 4) quick optimization of the route found
            print(f"Optimizing costs...")
            print(f"Current cost: {self.chip.calc_total_grid_cost()}")
            
            if self.A_star_rerouting:
                self.A_star_optimize_chip()
            else:
                self.greed_optimize()
            

            print(f"Costs after optimization: {self.chip.calc_total_grid_cost()}")
        

            # 5) check if we beat the best cost or reached the intersection limit
            current_cost = self.chip.calc_total_grid_cost()
            current_intersections = self.chip.get_wire_intersect_amount()
            print(f"{algo_name_routing} After rerouting: cost={current_cost}, intersections={current_intersections}")

            # save current cost to all cost list for parameter research
            self.all_costs.append(current_cost) 

            if current_cost < self.best_cost:
                self.best_cost = current_cost
                self.best_wire_segment_list = self.chip.wire_segment_list
                optimal_solution_counter = 0
            
            # we encounter the same cost, perhaps optimal reached, add 1 optimal iteration
            if current_cost == self.best_cost:
                optimal_solution_counter += 1

            # if at or below intersection_limit and above early_stopping_patience, we can stop early
            if current_intersections <= self.intersection_limit and optimal_solution_counter > self.early_stopping_patience:
                print(f"{algo_name_routing} Intersection limit reached or better. Stopping early.")
                break
        
        self.restore_best_solution()
        print(f"{algo_name_routing} Done. Best cost={self.best_cost}, Intersections={self.chip.get_wire_intersect_amount()}")

        return self.chip


    def intersections_rerouting(self) -> None:
        """
        Attempts to reroute intersecting wires one-by-one with BFS or Simulated Annealing to reduce intersections.
        Continues until no further improvements are made or all intersections are resolved.
        """
        intersection_count = self.chip.get_wire_intersect_amount()
        improved = True
        temperature_iterations = 0
        temperature = self.start_temperature

        while improved and intersection_count != 0:
            improved = False

            # identify all intersection coordinates
            intersection_coords = self.chip.get_intersection_coords()
            if not intersection_coords:
                return

            for coord in intersection_coords:
                temperature_iterations += 1

                # we find all wires passing through this intersection coordinate
                occupation_set = self.chip.get_coord_occupancy(coord, exclude_gates=True)
                
                # if no short circuit we continue
                if len(occupation_set) < 2:
                    continue

                # choose wire causing short circuit at random
                wire_to_fix = random.choice(tuple(occupation_set))

                # attempt reroute
                if self.reroute_wire(wire_to_fix, temperature):
                    improved = True
                    # if improved, break out to recalculate intersections
                    break

                # we cool down the temperature
                if self.simulated_annealing:
                    temperature = self.exponential_cooling(self.start_temperature, self.temperature_alpha, temperature_iterations)
            

            if not improved and self.simulated_annealing:
                print(f"Currently using start temperature: {self.start_temperature} with alpha: {self.temperature_alpha}.")

            
            intersection_count = self.chip.get_wire_intersect_amount()
            print(f"We reduced the intersections to: {intersection_count} with {self.chip.calc_total_grid_cost()}")

            
    def intersections_rerouting_A_star(self) -> None:
        """
        Attempts to reroute intersecting wires one-by-one using A* to resolve intersections.
        Continues until no further improvements are made or all intersections are resolved.
        """
        improved = True
        intersection_count = self.chip.get_wire_intersect_amount()
        while improved and intersection_count != 0:
            improved = False

            # identify all intersection coordinates
            intersection_coords = self.chip.get_intersection_coords()
            for coord in intersection_coords:
                # we find all wires passing through this intersection coordinate
                occupation_set = self.chip.get_coord_occupancy(coord, exclude_gates=True)
                
                # if no short circuit we continue
                if len(occupation_set) < 2:
                    continue

                # choose wire causing short circuit at random
                wire_to_fix = random.choice(tuple(occupation_set))

                # attempt reroute
                if self.reroute_wire_A_star(wire_to_fix):
                    improved = True
                    # if improved, break out to recalculate intersections
                    break
            
            intersection_count = self.chip.get_wire_intersect_amount()

    def reroute_wire(self, wire: 'Wire', temperature: int=0) -> bool:
        """
        Attempts to reroute the specified wire to avoid intersections with other wires.
        The wire is rerouted by removing it and then rerouting it using BFS or simulated annealing.
        If the new path reduces the number of intersections, it is kept. Otherwise, the old path is restored
        based on a probabilty for Simulated Annealing and is always restored with BFS.

        Args:
            wire (Wire): The wire to be rerouted.
            temperature (int): The temperature used for simulated annealing (optional).

        Returns:
            bool: True if the rerouting was successful, False otherwise.
        """
        new_path = None

        # we create a copies of the old state
        old_coords = wire.coords_wire_segments[:]
        old_cost = self.chip.calc_total_grid_cost()

        # 1) remove old segments from occupancy (except gates)
        self.chip.remove_wire_from_occupancy(wire)

        # reset wire_coords just in case
        wire.coords_wire_segments = [wire.gates[0], wire.gates[1]]

        # if simulated annealing we first try to find suboptimal route 
        if self.simulated_annealing and temperature > 0:

            # we allow short circuit
            new_path = self.bfs_route(
                chip=self.chip,
                start=wire.gates[0],
                end=wire.gates[1],
                offset=self.rerouting_offset,
                allow_short_circuit=True
            )

            if new_path:
                self.add_new_path(wire, new_path)
                new_cost = self.chip.calc_total_grid_cost()

                # if acceptance function refuses new path we set path to none and continue
                if (random.random() < self.acceptance_probability(new_cost, old_cost, temperature)) and new_cost != old_cost and self.chip.is_fully_connected():
                    # print(f"We have a temperature of {temperature} and a accepetanceprob of: {self.acceptance_probability(new_cost, old_cost, temperature)}")
                    if new_cost > old_cost:
                        print(f"Our old costs are: {old_cost} and our new costs are {new_cost}")
                    return True
                
                else:
                    # we remove the wire from occupancy, and reset the coords
                    self.chip.remove_wire_from_occupancy(wire)
                    wire.coords_wire_segments = [wire.gates[0], wire.gates[1]]
                    new_path = None


        # if simulated annealing refused suboptimal path, or if no simulated annealing, try to find new optimal path through bfs
        if new_path is None:
            new_path = self.bfs_route(
                chip=self.chip,
                start=wire.gates[0],
                end=wire.gates[1],
                offset=self.rerouting_offset,
                allow_short_circuit=False
            )

        # if we have found a new path, we add it to the chip
        if new_path:
            self.add_new_path(wire, new_path)
            return True

        # 3) if BFS failed or no improvement, return to old state and return False
        self.restore_wire(wire, old_coords)
        return False

    def reroute_wire_A_star(self, wire: 'Wire') -> bool:
        """
        Attempts to reroute the specified wire to avoid intersections using the A* algorithm.
        The wire is rerouted by removing it and then rerouting it using A*. If the new path
        reduces the number of intersections, it is kept. Otherwise, the old path is restored.
        
        Args:
            wire (Wire): The wire to be rerouted.

        Returns:
            bool: True if the rerouting was successful, False otherwise.
        """
        # we create a copie of the old state
        old_coords = wire.coords_wire_segments[:]
        old_intersection_amount = self.chip.get_wire_intersect_amount()
        old_cost = self.chip.calc_total_grid_cost()

        # 1) remove old segments from occupancy (except gates)
        self.chip.remove_wire_from_occupancy(wire)

        start = wire.gates[0]
        end = wire.gates[1]

        # 2) try to use A* to reroute the wire
        wire.coords_wire_segments = [start, end]
        new_path = self.a_star.shortest_cable(self.chip, start, end, allow_short_circuit=True)

        if new_path:
            # if successful, add new path
            wire.append_wire_segment_list(new_path)
            self.chip.add_wire_segment_list_to_occupancy(new_path, wire)
            new_intersection_amount = self.chip.get_wire_intersect_amount()
            is_fully_connected = self.chip.is_fully_connected()
            
            # if we lowered cost, keep it
            if new_intersection_amount < old_intersection_amount and is_fully_connected:
                print(f"Reduced the intersections to: {new_intersection_amount}")
                return True
            
            elif new_intersection_amount == old_intersection_amount and is_fully_connected:
                new_cost = self.chip.calc_total_grid_cost()
                if new_cost < old_cost:
                    print(f"Reduced the costs to: {new_cost}")
                    return True

        # 3) if no improvement, return to old state and return False
        self.restore_wire(wire, old_coords)
        return False
    
    def add_new_path(self, wire: Wire, new_path: list[Coords_3D]) -> None:
        """
        Adds a new path to the wire and occupancy.

        Args:
            wire (Wire): The wire to add the new path to.
            new_path (list[Coords_3D]): The new path to add.
        """
        wire.append_wire_segment_list(new_path)
        self.chip.add_wire_segment_list_to_occupancy(new_path, wire)

    def restore_wire(self, wire: 'Wire', old_coords: list[Coords_3D]) -> None:
        """
        Restores the wire to its previous state.

        Args:
            wire (Wire): The wire to restore.
            old_coords (list[Coords_3D]): The old coordinates of the wire.
        """
        self.chip.reset_wire(wire)
        wire.append_wire_segment_list(old_coords)
        self.chip.add_wire_segment_list_to_occupancy(old_coords, wire)

    def restore_best_solution(self) -> None:
        """
        Restores the best solution found to the chip.
        """
        self.chip.reset_all_wires()
        self.chip.add_entire_wires(self.best_wire_segment_list)

    def greed_optimize(self) -> None:
        """
        Performs a local greedy improvement pass to reduce the total wire length/cost
        after the grid is fully connected and intersections are minimized.

        For each wire:
        1) Temporarily removes the wire from occupancy.
        2) Performs a BFS to find a shorter path, prioritizing shorter routes.
        3) Compares the new path's total cost or intersections to the old one. If better,
           the new path is kept; otherwise, the old route is restored.

        The process is repeated for all wires in the chip, with the goal of minimizing 
        the total grid cost.
        """
        
        for wire in self.chip.wires:
            # snapshot old wire state
            old_coords = wire.coords_wire_segments[:]
            old_cost   = self.chip.calc_total_grid_cost()

            # 1) remove old wire from occupancy 
            for coord in old_coords:
                if coord not in wire.gates:
                    self.chip.occupancy.remove_from_occupancy(coord, wire)

            # 2) attempt BFS for a new, presumably shorter route.
            start, end = wire.gates[0], wire.gates[1]
            wire.coords_wire_segments = [start, end]  
            new_path = self.bfs_route(
                chip=self.chip,
                start=start,
                end=end,
                offset=self.rerouting_offset,              
                allow_short_circuit=False
            )

            # If BFS yields a path, see whether it improves the total cost
            if new_path:
        
                proposed_wire = [start] + new_path + [end]

                # temporarily add proposed route to occupancy
                for coord in proposed_wire[1:-1]:
                    self.chip.add_wire_segment_to_occupancy(coord, wire)
                wire.coords_wire_segments = proposed_wire

                # check new cost
                new_cost = self.chip.calc_total_grid_cost()

                # 3) if no improvement, revert
                if new_cost >= old_cost or not self.chip.is_fully_connected():
                    # remove newly added route
                    for coord in proposed_wire[1:-1]:
                        self.chip.occupancy.remove_from_occupancy(coord, wire)
                    # restore old wire
                    wire.coords_wire_segments = old_coords
                    for coord in old_coords:
                        if coord not in wire.gates:
                            self.chip.add_wire_segment_to_occupancy(coord, wire)
            else:
                # BFS failed to find a path -> revert
                wire.coords_wire_segments = old_coords
                for coord in old_coords:
                    if coord not in wire.gates:
                        self.chip.add_wire_segment_to_occupancy(coord, wire)

    def A_star_optimize_chip(self) -> None:
        """
        Optimizes the chip's wiring configuration using the A* algorithm.

        This method initiates an A* optimization process on the chip's wiring, aiming to 
        reroute all wires by rerouting 1 each time by temporarily removing it. It uses 
        the A* algorithm for rerouting while considering short-circuit allowance.

        The optimization is performed with the objective of reducing total wiring cost 
        or intersections.
        """
        self.a_star_optimize = A_star_optimize(
            chip=self.chip,
            allow_short_circuit=True
        )
        self.a_star_optimize.optimize(reroute_n_wires=1)

    @staticmethod
    def acceptance_probability(new_cost: int, old_cost: int, temperature: int) -> int:
        """
        Calculates the acceptance probability for a new solution in a simulated annealing 
        algorithm.

        Args:
            new_cost: The cost of the new solution.
            old_cost: The cost of the previous solution.
            temperature: The current temperature used in the simulated annealing process.

        Returns:
            The probability of accepting the new solution (1 or a value between 0 and 1).
        """
        if new_cost < old_cost:
            return 1
        
        if new_cost >= old_cost:
            return pow(2,  (old_cost - new_cost)/temperature)

    @staticmethod    
    def exponential_cooling(start_temperature: int, alpha: int, iterations: int) -> int:
        """
        Computes the temperature for each iteration in an exponential cooling schedule.

        Args:
            start_temperature: The initial temperature at the start of the process.
            alpha: The cooling rate (0 ≤ alpha ≤ 1).
            iterations: The number of iterations completed so far.

        Returns:
            The new temperature after applying the exponential cooling formula.
        """
        return start_temperature * (alpha ** iterations)


class IRRA_A_star(A_star, IRRA_PR):
    """
    The IRRA_A_star class uses the Iterative Reconfiguration of Routing Algorithm (IRRA) with
    an A* solutions as input to optimize chip wire routing. 
    The algorithm iterates over multiple solutions to minimize 
    total cost and wire intersections.

    It generates random wire configurations, reroutes to reduce intersections, 
    optimizes that routing, and checks for the best solution, stopping early if 
    certain conditions (e.g., intersection limit or optimal cost) are met.

    Attributes:
        A_star_rerouting (bool): Enables A* rerouting.
        simulated_annealing (bool): Enables simulated annealing rerouting.
        iterations (int): Number of iterations.
        intersection_limit (int): Max allowed intersections before stopping early.
        early_stopping_patience (int): Consecutive iterations with same cost before early stop.
        acceptable_intersection (int): Acceptable wire intersections for the input solution.
        best_cost (int): Best found cost.
        best_wire_segment_list (list): Wire segments of the best solution.
        all_costs (list): List of all encountered costs.
    """

    def run(self) -> Chip:
        """
        Runs the IRRA A* optimization algorithm, iterating over multiple random wiring 
        configurations to find the best solution with minimized total cost and intersections.

        The process consists of the following steps:
        1) Clears occupancy and resets wire paths for the chip.
        2) Generates a random wiring configuration using A*.
        3) Repeats until a configuration is fully connected and has acceptable intersections.
        4) Attempts to reroute wires to reduce intersections using A* or BFS.
        5) Performs quick optimization of the route to minimize cost.
        6) Tracks the best solution found and stops early if the intersection limit or 
           optimal solution is reached.

        Returns:
            Chip: The optimized chip object with the best wire routing configuration found.
        """
        self.shuffle_wires = True
        algo_name_input = "[IRRA A* input]"
        algo_name_routing = "[IRRA A* routing]" if self.A_star_rerouting else "[IRRA annealing routing]" if self.simulated_annealing else "[IRRA BFS routing]"
        for new_solution_iteration in range(1, self.iterations + 1):
            print(f"{algo_name_input} Starting iteration {new_solution_iteration}/{self.iterations}:")
            improvement_iteration = 0
            optimal_solution_counter = 0 # count the amount of times we encounter the same cost in a row

            if new_solution_iteration != 1:
                # 1) clear occupancy and reset wire paths
                self.chip.reset_all_wires()

            # 2) let parent produce a random wiring
            super().run()

            # repeat this step until we find a configuration that is fully connected 
            # optional) repeat this step until we have wiring that has acceptable intersection amount 
            while (self.chip.get_wire_intersect_amount() >= self.acceptable_intersection) or not self.chip.is_fully_connected():
                self.chip.reset_all_wires()
                super().run()
                print(f"Finding configuration: {improvement_iteration}, intersections: {self.chip.get_wire_intersect_amount()}")
                improvement_iteration += 1

            # 3) try to reroute (reduce intersections) in a loop
            print(f"{algo_name_routing} Started rerouting...")
            if self.A_star_rerouting:
                self.intersections_rerouting_A_star()
            else:
                self.intersections_rerouting()

            # 4) quick optimization of the route found
            print(f"Optimizing found route...")
            print(f"Current cost: {self.chip.calc_total_grid_cost()}")
            
            if self.A_star_rerouting:
                self.A_star_optimize_chip()
            else:
                self.greed_optimize()

            print(f"Costs after optimization: {self.chip.calc_total_grid_cost()}")

            # 5) check if we beat the best cost or reached the intersection limit
            current_cost = self.chip.calc_total_grid_cost()
            current_intersections = self.chip.get_wire_intersect_amount()
            print(f"{algo_name_routing} After rerouting: cost={current_cost}, intersections={current_intersections}")

            # save current cost to all cost list for parameter research
            self.all_costs.append(current_cost) 

            if current_cost < self.best_cost:
                self.best_cost = current_cost
                self.best_wire_segment_list = self.chip.wire_segment_list
                optimal_solution_counter = 0
            
            # we encounter the same cost, perhaps optimal reached, add 1 optimal iteration
            if current_cost == self.best_cost:
                optimal_solution_counter += 1

            # if at or below intersection_limit and above early_stopping_patience, we can stop early
            if current_intersections <= self.intersection_limit and optimal_solution_counter > self.early_stopping_patience:
                print(f"{algo_name_routing} Intersection limit reached or better. Stopping early.")
                break

        self.restore_best_solution()
        print(f"{algo_name_routing} Done. Best cost={self.best_cost}, Intersections={self.chip.get_wire_intersect_amount()}")
        return self.chip