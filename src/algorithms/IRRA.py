from src.classes.chip import Chip
from src.algorithms.utils import *
from src.algorithms.random_algo import Random_random
from collections import deque
import random
import copy

class IRRA(Random_random):

    """
    Iterative Random Rerouting Algorithm (IRRA):
    The IRRA algorithm starts off in a random configuration after which it will try to reroute the wiring which will cause a short circuit. 
    The algorithm will start off in another random configuration after there are no short circuits left, or after no short circuits are able to be filtered out.
    Optional: put a limit on the goal of working out the intersections, making the algorithm more efficient
    Optional: put a limit on the initial intersection amount (l * GATE) checking only random configurations with a low intersection amount
    """

    def __init__(self, chip: "Chip", iterations: int = 100, intersection_limit: int = 0, acceptable_intersection: int = 2, max_offset: int = 10, allow_short_circuit: bool = False, sort_wires: bool = False, random_seed: int|None = None):

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
        self.gate_amount = len(self.chip.gates)


        # we use these variables to keep track of the best solution
        self.best_cost = float("inf")
        self.best_configuration: list[list[tuple[int,int,int]]] = []

    def run(self) -> None:
        """
        Running this algorithm as follows:
        1) For up to `self.iterations` attempts:
           a) Clear the chip occupancy & wire paths.
           b) Let parent (Random_random) create a random configuration, if within acceptable_intersection continue.
           c) Iteratively fix short circuits until we can't reduce them further.
           d) If intersection limit is reached, we stop early.
        2) Restore the best configuration found to the chip.
        """
        for iteration in range(1, self.iterations + 1):
            print(f"[IRRA] Starting iteration {iteration}/{self.iterations}:")
            i = 0

            # 1) clear occupancy and reset wire paths
            self.reset_chip()

            # 2) let parent produce a random wiring
            super().run()


            # repeat this step untill we have wiring that has ascceptable intersection amount
            while(self.chip.get_wire_intersect_amount() >= (self.acceptable_intersection * self.gate_amount)):
                self.reset_chip()
                super().run()
                print(f"Finding configuration: {i}, intersections: {self.chip.get_wire_intersect_amount()} for {self.gate_amount}")
                i += 1

            # 3) try to reroute (reduce intersections) in a loop
            print(f"Started rerouting...")
            self.intersections_rerouting()

            # 4) TODO: quick optimization of the route found
            print(f"Optimizing costs...")
            print(f"Current cost: {self.chip.calc_total_grid_cost()}")
            # self.greed_optimize()


            print(f"Optimized, current cost: {self.chip.calc_total_grid_cost()}")
            # 5) check if we beat the best cost or reached the intersection limit
            current_cost = self.chip.calc_total_grid_cost()
            current_intersections = self.chip.get_wire_intersect_amount()
            print(f"[IRRA] After rerouting: cost={current_cost}, intersections={current_intersections}")

            if current_cost < self.best_cost:
                self.best_cost = current_cost
                self.best_configuration = [
                    # we copy the segments of wire into the best config list
                    wire.coords_wire_segments[:] for wire in self.chip.wires
                ]

            # if at or below intersection_limit, we can stop early
            if current_intersections <= self.intersection_limit:
                print("[IRRA] Intersection limit reached or better. Stopping early.")
                break

        # after all iterations, restore the best solution found
        self.restore_best_solution()

        final_cost = self.chip.calc_total_grid_cost()
        final_intersections = self.chip.get_wire_intersect_amount()
        print(f"[IRRA] Done. Best cost={self.best_cost}, Final cost={final_cost}, Intersections={final_intersections}")

    def reset_chip(self) -> None:

        # initializes the occupancy grid again
        self.chip.occupancy.reset()
        self.chip.occupancy.add_gates(self.chip.gate_coords)

        # inserting the default gate wire_segments
        for wire in self.chip.wires:
            wire.coords_wire_segments = [wire.gates[0], wire.gates[1]]

    def intersections_rerouting(self) -> None:
        """
        Tries to remove intersections by rerouting intersecting wires one-by-one.
        Continues until no more improvements are made or no intersections remain.
        """
        while True:
            intersection_count_before = self.chip.get_wire_intersect_amount()
            if intersection_count_before == 0:
                # no intersections, thus fully fixed
                return

            improved = False

            # identify all intersection coordinates
            intersection_coords = self.chip.get_intersection_coords()
            if not intersection_coords:
                return

            for coord in intersection_coords:
                # we find all wires passing through this intersection coordinate
                occupation_set = self.chip.occupancy.occupancy[coord]
                
                # if no short circuit we continue
                if len(occupation_set) < 2:
                    continue

                # choose wire causing short circuit at random
                wire_to_fix = random.choice(tuple(occupation_set))

                # attempt reroute
                if self.reroute_wire(wire_to_fix):
                    improved = True
                    # if improved, break out to recalculate intersections
                    break

            intersection_count_after = self.chip.get_wire_intersect_amount()

            # no intersection was removed, or no single-wire reroute improved things => stop
            if not improved or intersection_count_after >= intersection_count_before:
                return

    def reroute_wire(self, wire) -> bool:
        """
        Removes a wire from the occupancy grid and tries to find a new
        shortcircuit-free path for it. Returns True if rerouting improved the situation,
        else False (and reverts).
        """
        # we create a copies of the old state
        old_coords = wire.coords_wire_segments[:]
        old_cost = self.chip.calc_total_grid_cost()
        old_intersections = self.chip.get_wire_intersect_amount()

        # 1) remove old segments from occupancy (except gates)
        for c in old_coords:
            # remove all wire from occupancy coords accept in gate coords
            if c not in wire.gates: 
                self.chip.occupancy.remove_from_occupancy(c, wire)

        # 2) try to BFS-route again with offset=10 avoiding collisions
        # TODO: this offset is currently arbitrary, try finding an optimal one
        wire.coords_wire_segments = [wire.gates[0], wire.gates[1]]
        new_path = self.bfs_route(
            chip=self.chip,
            start=wire.gates[0],
            end=wire.gates[1],
            offset=10,
            allow_short_circuit=False
        )

        if new_path:
            # if successful, add new path segments to occupancy
            for c in new_path:
                self.chip.add_wire_segment_to_occupancy(c, wire)
                wire.append_wire_segment(c)

            # check whether intersection count improved
            new_intersections = self.chip.get_wire_intersect_amount()
            new_cost = self.chip.calc_total_grid_cost()
            # if we actually lowered intersection count or cost, keep it
            if new_intersections < old_intersections or new_cost < old_cost:
                print(f"Reduced the intersections to: {new_intersections}")
                return True

        # 3) if BFS failed or no improvement, return to old state and return False
        self.restore_wire(wire, old_coords)
        return False

    def restore_wire(self, wire, coords) -> None:
        """
        Restores a wire to given coords in occupancy.
        """
        start = wire.gates[0]
        end = wire.gates[1]

        wire.coords_wire_segments = [start, end]
        for c in coords:
            if c not in wire.gates:
                self.chip.add_wire_segment_to_occupancy(c, wire)
            wire.append_wire_segment(c)

    def restore_best_solution(self) -> None:
        """
        After all iterations, put the chip back to the best configuration found.
        """
        if not self.best_configuration:
            print("[IRRA] No valid solution found better than initial. Keeping current layout.")
            return

        # clear chip to insert optimal layout found
        self.reset_chip()

        # add the best wire coordinates
        for wire, coords in zip(self.chip.wires, self.best_configuration):
            start = wire.gates[0]
            end = wire.gates[1]
            wire.coords_wire_segments = [start, end]
            for c in coords:
                self.chip.add_wire_segment_to_occupancy(c, wire)
                wire.append_wire_segment(c)