from src.classes.chip import Chip
from src.algorithms.utils import *
from src.algorithms.random_algo import Pseudo_random
from src.algorithms.A_star import A_star
import math
import random
import copy
from math import inf

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.wire import Wire

class IRRA(Pseudo_random):

    """
    Iterative Random Rerouting Algorithm (IRRA):
    The IRRA algorithm starts off in a random configuration after which it will try to reroute the wiring which will cause a short circuit. 
    The algorithm will start off in another random configuration after there are no short circuits left, or after no short circuits are able to be filtered out.
    Optional: put a limit on the goal of working out the intersections, making the algorithm more efficient
    Optional: put a limit on the initial intersection amount (l * GATE) checking only random configurations with a low intersection amount
    """

    def __init__(self, chip: "Chip", iterations: int = 100, intersection_limit: int = 0, acceptable_intersection: int = 2, early_stopping_patience: int=5, max_offset: int = 10, allow_short_circuit: bool = False, sort_wires: bool = False, A_star_rerouting: bool=False, simulated_annealing: bool = False, start_temperature: int = 500, temperature_alpha: int = 0.9, random_seed: int|None = None):

        super().__init__(
            chip=chip,
            max_offset=max_offset,
            allow_short_circuit=allow_short_circuit,
            sort_wires=sort_wires,
            random_seed=random_seed
        )
        self.iterations = iterations
        self.intersection_limit = intersection_limit
        self.acceptable_intersection = acceptable_intersection
        self.early_stopping_patience = early_stopping_patience
        self.gate_amount = len(self.chip.gates)
        self.A_star_rerouting = A_star_rerouting
        self.simulated_annealing = simulated_annealing
        self.temperature_alpha = temperature_alpha
        self.start_temperature = start_temperature

        if self.A_star_rerouting:
            self.a_star = A_star(
                chip=chip,
                max_offset=max_offset,
                allow_short_circuit=allow_short_circuit,
                sort_wires=sort_wires,
            )


        # we use these variables to keep track of the best solution
        self.best_cost = inf   # inf, such that current_cost < best_cost
        self.best_chip: Chip|None = None
        self.chip_og = copy.deepcopy(chip)

        if self.A_star_rerouting and self.simulated_annealing:
            raise ValueError("A* rerouting is not compatible with simulated Annealing")

    def run(self) -> Chip:
        """
        Running this algorithm as follows:
        1) For up to `self.iterations` attempts:
           a) Clear the chip occupancy & wire paths.
           b) Let parent (Random_random) create a random configuration, if within acceptable_intersection continue.
           c) Iteratively fix short circuits until we can't reduce them further.
           d) If intersection limit is reached, we stop early.
        2) Restore the best configuration found to the chip.
        """
        algo_name_input = "[IRRA input]"
        algo_name_routing = "[IRRA A* routing]" if self.A_star_rerouting else "[IRRA annealing routing]" if self.simulated_annealing else "[IRRA BFS routing]"
        for new_solution_iteration in range(1, self.iterations + 1):
            print(f"{algo_name_input} Starting iteration {new_solution_iteration}/{self.iterations}:")
            improvement_iteration = 0
            optimal_solution_counter = 0 # count the amount of times we encounter the same cost in a row

            # 1) clear occupancy and reset wire paths
            self.reset_chip()

            # 2) let parent produce a random wiring
            super().run()

            # repeat this step until we find a configuration that is fully connected 
            # optional) repeat this step until we have wiring that has acceptable intersection amount 
            while (not self.chip.is_fully_connected() or self.chip.get_wire_intersect_amount() >= (self.acceptable_intersection * self.gate_amount)):
                self.reset_chip()
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
                self.A_star_optimize()
            else:
                self.greed_optimize()
            

            print(f"Costs after optimization: {self.chip.calc_total_grid_cost()}")

            # 5) check if we beat the best cost or reached the intersection limit
            current_cost = self.chip.calc_total_grid_cost()
            current_intersections = self.chip.get_wire_intersect_amount()
            print(f"{algo_name_routing} After rerouting: cost={current_cost}, intersections={current_intersections}")

            if current_cost < self.best_cost:
                self.best_cost = current_cost
                self.best_chip = copy.deepcopy(self.chip)
                optimal_solution_counter = 0
            
            # we encounter the same cost, perhaps optimal reached, add 1 optimal iteration
            if current_cost == self.best_cost:
                optimal_solution_counter += 1

            # if at or below intersection_limit and above early_stopping_patience, we can stop early
            if current_intersections <= self.intersection_limit and optimal_solution_counter > self.early_stopping_patience:
                print(f"{algo_name_routing} Intersection limit reached or better. Stopping early.")
                break

        print(f"{algo_name_routing} Done. Best cost={self.best_cost}, Intersections={self.best_chip.get_wire_intersect_amount()}")
        return self.best_chip

    def reset_chip(self) -> None:
        self.chip.occupancy.reset()
        self.chip.occupancy.add_gates(self.chip.gate_coords)
        for wire in self.chip.wires:
            wire.coords_wire_segments = [wire.gates[0], wire.gates[1]]


    def intersections_rerouting(self) -> None:
        """
        Tries to remove intersections by rerouting intersecting wires one-by-one.
        Continues until no more improvements are made or no intersections remain.
        """

        temperature_iterations = 0
        temperature = self.start_temperature

        while True:

            temperature_iterations += 1

            intersection_count = self.chip.get_wire_intersect_amount()
            if intersection_count == 0:
                # no intersections, thus fully fixed
                return
            
            print(f"We reduced the intersections to: {intersection_count} with {self.chip.calc_total_grid_cost()}")

            improved = False

            # identify all intersection coordinates
            intersection_coords = self.chip.get_intersection_coords()
            if not intersection_coords:
                return

            for coord in intersection_coords:
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
            temperature = self.exponential_cooling(temperature, self.temperature_alpha, temperature_iterations)

            # if no single-wire reroute improved things => stop
            if not improved:
                return
            
    def intersections_rerouting_A_star(self) -> None:
        """
        Tries to remove intersections by rerouting intersecting wires one-by-one.
        Continues until no more improvements are made or no intersections remain.
        """
        while True:
            intersection_count = self.chip.get_wire_intersect_amount()
            if intersection_count == 0:
                # no intersections, thus fully fixed
                return

            improved = False

            # identify all intersection coordinates
            intersection_coords = self.chip.get_intersection_coords()
            if not intersection_coords:
                return

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

            # if no single-wire reroute improved things => stop
            if not improved:
                return

    def reroute_wire(self, wire: 'Wire', temperature: int) -> bool:
        """
        Removes a wire from the occupancy grid and tries to find a new
        shortcircuit-free path for it. Returns True if rerouting improved the situation,
        else False (and reverts).
        """
        new_path = None

        # we create a copies of the old state
        old_coords = wire.coords_wire_segments[:]
        old_cost = self.chip.calc_total_grid_cost()

        # 1) remove old segments from occupancy (except gates)
        self.chip.remove_wire_from_occupancy(wire)

        # 2) try to BFS-route again with offset=10 avoiding collisions
        # TODO: this offset is currently arbitrary, try finding an optimal one

        # reset wire_coords just in case
        wire.coords_wire_segments = [wire.gates[0], wire.gates[1]]

        # if simulated annealing we first try to find suboptimal route 
        if self.simulated_annealing and temperature > 0:

            # we allow short circuit
            new_path = self.bfs_route(
                chip=self.chip,
                start=wire.gates[0],
                end=wire.gates[1],
                offset=10,
                allow_short_circuit=True
            )

            if new_path:

                self.add_new_path(wire, new_path)
                new_cost = self.chip.calc_total_grid_cost()

                # if acceptance function refuses new path we set path to none and continue
                if (random.random() < self.acceptance_probability(new_cost, old_cost, temperature)):
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
                offset=10,
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
        Removes a wire from the occupancy grid and tries to find a new
        shortcircuit-free path for it. Returns True if rerouting improved the situation,
        else False (and reverts).
        """
        # we create a copie of the old state
        old_coords = wire.coords_wire_segments[:]
        old_intersection_amount = self.chip.get_wire_intersect_amount()
        old_cost = self.chip.calc_total_grid_cost()

        # 1) remove old segments from occupancy (except gates)
        for c in old_coords:
            # remove all wire from occupancy coords except in gate coords
            if c not in wire.gates: 
                self.chip.occupancy.remove_from_occupancy(c, wire)

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
    
    def add_new_path(self, wire, new_path) -> None:
            
            start = wire.gates[0]
            end = wire.gates[1]
            wire.coords_wire_segments = [start] + new_path + [end]

            for c in new_path:
                self.chip.add_wire_segment_to_occupancy(c, wire)

    def restore_wire(self, wire: 'Wire', old_coords: list[Coords_3D]) -> None:
        """
        Restores a wire to given coords in occupancy.
        """
        self.chip.reset_wire(wire)
        wire.append_wire_segment_list(old_coords)
        self.chip.add_wire_segment_list_to_occupancy(old_coords, wire)

    def restore_best_solution(self) -> None:
        """
        After all iterations, put the chip back to the best configuration found.
        """
        if not self.best_chip:
            print("[IRRA] No valid solution found better than initial. Keeping current layout.")
            return

        # clear chip to insert optimal layout found
        self.chip = copy.deepcopy(self.best_chip)

    def greed_optimize(self) -> None:
        """
        After the grid is fully connected and intersections are minimized,
        do a local 'greedy' improvement pass to reduce total wire length/cost.

        For each wire:
        1) Temporarily remove it from occupancy.
        2) BFS-route again (prioritizing short paths).
        3) Compare new total cost (or intersections) vs. old. Keep if better.
            Otherwise revert to the old route.
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
                offset=10,              
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
                if new_cost >= old_cost:
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

    def A_star_optimize(self) -> None:
        """
        After the grid is fully connected and intersections are minimized,
        do an A* search for each wire to reduce total wire length/cost.

        For each wire:
        1) Temporarily remove it from occupancy.
        2) Calculate the route again using A* (prioritizing short paths).
        3) Compare new total cost (or intersections) vs. old. Keep if better.
            Otherwise revert to the old route.
        """
        iteration = 0
        while True:
            iteration += 1
            best_cost = inf
            previous_best_cost = inf
            random.shuffle(self.chip.wires)
            for wire in self.chip.wires:
                # snapshot old wire state
                old_coords = wire.coords_wire_segments[:]
                old_cost = self.chip.calc_total_grid_cost()
                new_cost = old_cost

                # 1) remove old wire from chip
                self.chip.reset_wire(wire)

                # 2) attempt A* for a new, hopefully shorter route.
                start, end = wire.gates[0], wire.gates[-1]
                new_path = self.a_star.shortest_cable(self.chip, start, end, allow_short_circuit=True)

                # If A* yields a path, see whether it improves the total cost
                if new_path:
                    wire.append_wire_segment_list(new_path)
                    self.chip.add_wire_segment_list_to_occupancy(new_path, wire)
                    new_cost = self.chip.calc_total_grid_cost()

                # 3) if no improvement, revert
                if new_cost >= old_cost or not self.chip.is_fully_connected():
                    self.chip.reset_wire(wire)
                    wire.append_wire_segment_list(old_coords)
                    self.chip.add_wire_segment_list_to_occupancy(old_coords, wire)

                else:
                    best_cost = new_cost
                    print(f"{iteration}: Route optimized: new cost = {new_cost}")


            if best_cost == previous_best_cost:
                return
            
            previous_best_cost = best_cost

    @staticmethod
    def acceptance_probability(new_cost: int, old_cost: int, temperature: int) -> int:
        
        if new_cost < old_cost:
            return 1
        
        if new_cost >= old_cost:
            return pow(2,  (old_cost - new_cost)/temperature)

    @staticmethod    
    def exponential_cooling(start_temperature: int, alpha: int, iterations: int) -> int:

        return start_temperature * (alpha ** iterations)
    
    @staticmethod
    def logarithmic_cooling(start_temperature: int, iterations: int) -> int:

        return start_temperature / math.log(1 + iterations)

    @staticmethod 
    def linear_cooling(start_temperature: int, alpha: int, iterations: int) -> int:

        return start_temperature - (alpha * iterations)







class IRRA_A_star(A_star, IRRA):

    """
    Iterative Random Rerouting Algorithm (IRRA):
    The IRRA algorithm starts off in a random configuration after which it will try to reroute the wiring which will cause a short circuit. 
    The algorithm will start off in another random configuration after there are no short circuits left, or after no short circuits are able to be filtered out.
    Optional: put a limit on the goal of working out the intersections, making the algorithm more efficient
    Optional: put a limit on the initial intersection amount (l * GATE) checking only random configurations with a low intersection amount
    """

    def run(self) -> Chip:
        """
        Running this algorithm as follows:
        1) For up to `self.iterations` attempts:
           a) Clear the chip occupancy & wire paths.
           b) Let parent (Random_random) create a random configuration, if within acceptable_intersection continue.
           c) Iteratively fix short circuits until we can't reduce them further.
           d) If intersection limit is reached, we stop early.
        2) Restore the best configuration found to the chip.
        """
        self.shuffle_wires = True
        algo_name_input = "[IRRA A* input]"
        algo_name_routing = "[IRRA A* routing]" if self.A_star_rerouting else "[IRRA annealing routing]" if self.simulated_annealing else "[IRRA BFS routing]"
        for new_solution_iteration in range(1, self.iterations + 1):
            print(f"{algo_name_input} Starting iteration {new_solution_iteration}/{self.iterations}:")
            improvement_iteration = 0
            optimal_solution_counter = 0 # count the amount of times we encounter the same cost in a row

            # 1) clear occupancy and reset wire paths
            self.chip.reset_all_wires()

            # 2) let parent produce a random wiring
            super().run()

            # repeat this step until we find a configuration that is fully connected 
            # optional) repeat this step until we have wiring that has acceptable intersection amount 
            while (self.chip.get_wire_intersect_amount() >= (self.acceptable_intersection * self.gate_amount)) or not self.chip.is_fully_connected:
                self.reset_chip()
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
                self.A_star_optimize()
            else:
                self.greed_optimize()

            print(f"Costs after optimization: {self.chip.calc_total_grid_cost()}")

            # 5) check if we beat the best cost or reached the intersection limit
            current_cost = self.chip.calc_total_grid_cost()
            current_intersections = self.chip.get_wire_intersect_amount()
            print(f"{algo_name_routing} After rerouting: cost={current_cost}, intersections={current_intersections}")

            if current_cost < self.best_cost:
                self.best_cost = current_cost
                self.best_chip = copy.deepcopy(self.chip)
                optimal_solution_counter = 0
            
            # we encounter the same cost, perhaps optimal reached, add 1 optimal iteration
            if current_cost == self.best_cost:
                optimal_solution_counter += 1

            # if at or below intersection_limit and above early_stopping_patience, we can stop early
            if current_intersections <= self.intersection_limit and optimal_solution_counter > self.early_stopping_patience:
                print(f"{algo_name_routing} Intersection limit reached or better. Stopping early.")
                break

        print(f"{algo_name_routing} Done. Best cost={self.best_cost}, Intersections={self.best_chip.get_wire_intersect_amount()}")
        return self.best_chip