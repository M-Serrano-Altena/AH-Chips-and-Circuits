from src.classes.chip import Chip
from src.algorithms.utils import *
from src.algorithms.greed import Greed_random
from collections import deque
import random

class Pseudo_random(Greed_random):

    """
    First: makes wire connections at random for random offsets if possible
    If finding random configuration not viable: check for cable connections iteratively (offset + 2, 4, 6 untill k)
    If still no solution found (and allow_short_circuit = True): we connect ignoring short circuit
    """

    def run(self) -> None:
        self.chip.wires = self.get_wire_order(self.chip.wires)

        # we go through all the wires in the chip
        for wire in self.chip.wires:
            if wire.is_wire_connected():
                # already connected, skip
                continue

            start = wire.gates[0]  # gate1
            end = wire.gates[1]    # gate2

            # we add the wire to the occupy grid on position of gates:
            self.chip.add_wire_segment_to_occupancy(coord=start, wire=wire)
            self.chip.add_wire_segment_to_occupancy(coord=end, wire=wire)

            wire.coords_wire_segments = [start, end] # reset the coords to just the gates

            min_length = manhattan_distance(start, end)
            max_length = self.max_offset + min_length

            # generate and shuffle possible lengths: [min_length, min_length + 1, ..., max_length]
            length_candidates = list(range(min_length - 1, max_length + 1, 2))
            random.shuffle(length_candidates)

            for random_length in length_candidates:
                path = self.bfs_route_exact_length(
                    chip = self.chip,
                    start = start, 
                    end = end, 
                    exact_length = random_length
                )

                if path is not None:
                    # append the path coords to the wire
                    for coord in path:
                        self.chip.add_wire_segment_to_occupancy(coord=coord, wire=wire)
                        wire.append_wire_segment(coord)
                    break

            # we let this loop until all wires have been tried for random offsets

    @staticmethod
    def bfs_route_exact_length(chip: Chip, start: Coords_3D, end: Coords_3D, exact_length: int) -> list[Coords_3D]|None:
        """
        This function finds a route from start_gate to end_gate of exactly the length given 
        It also shuffles the neighbours, thus making each route found random in shape
        """
        # queue consists of tuple entries of (current node, [path])
        queue = deque([(start, [start])])
        # we store (node, dist) instead of node, this way we can make inefficient routes
        visited = set()  

        while queue:
            (current, path) = queue.popleft()
            dist = len(path)
            path_set = set(path)
            neighbours = chip.get_neighbours(current)
            #random.shuffle(neighbours)

            # check for success
            if current == end and dist == exact_length:
                return path[1:-1] if dist > 2 else []

            # prune if we exceed exact_length
            if dist > exact_length:
                continue

            # explore
            for neighbour in neighbours:
                # if the coordinate is already in its own path we continue
                if neighbour in path_set:
                    continue

                occupant_set = chip.get_coord_occupancy(neighbour)

                # we continue if grid is occupied by another gate (occupancy grid only contains gate coords) which is not its own
                if "GATE" in occupant_set and neighbour != end:
                    continue

                # if wire segment causes a collision we continue 
                if chip.wire_segment_causes_collision(neighbour, current):
                    continue

                newDist = dist + 1
                if (neighbour, newDist) not in visited:
                    visited.add((neighbour, newDist))
                    queue.append((neighbour, path + [neighbour]))

        return None
    

class True_random(Pseudo_random):
    """
    A class that extends Random_random but ignores collisions and gate occupancy.
    Wires can pass through anything. The BFS only ensures it doesn't revisit
    the same coordinate in its own path (to avoid infinite loops).
    """

    def run(self) -> None:
        # Same overall without fallback structure,
        # And we call our unconstrained BFS
        self.chip.wires = self.get_wire_order(self.chip.wires)

        for wire in self.chip.wires:
            if wire.is_wire_connected():
                continue  # skip already-connected wires

            start = wire.gates[0]
            end = wire.gates[1]

            # we add occupancy for the gates themselves
            self.chip.add_wire_segment_to_occupancy(coord=start, wire=wire)
            self.chip.add_wire_segment_to_occupancy(coord=end, wire=wire)
            wire.coords_wire_segments = [start, end]  # reset coords

            min_length = manhattan_distance(start, end)
            max_length = self.max_offset + min_length

            # generate and shuffle possible lengths
            length_candidates = list(range(min_length - 1, max_length + 1, 2))
            random.shuffle(length_candidates)

            for random_length in length_candidates:
                print(f"Checking: {random_length}")
                path = self.bfs_route_exact_length_unconstrained(
                    chip=self.chip,
                    start=start,
                    end=end,
                    exact_length=random_length
                )

                if path is not None:
                    print(f"We have a found path...")
                    # we found a path: add to occupancy & wire
                    for coord in path:
                        self.chip.add_wire_segment_to_occupancy(coord=coord, wire=wire)
                        wire.append_wire_segment(coord)
                    break

    @staticmethod
    def bfs_route_exact_length_unconstrained(chip: Chip, start: Coords_3D, end: Coords_3D,exact_length: int) -> list[Coords_3D] | None:

        """
        Finds a path of exactly `exact_length` steps from `start` to `end`
        ignoring collisions/gates entirely. We only avoid revisiting the same
        coordinate in our current BFS path to prevent loops.
        Chooses path of exact length at random because neighbours are shuffled
        """
        queue = deque([(start, [start])])

        while queue:
            current, path = queue.popleft()
            path_set = set(path)
            dist = len(path)
            neighbours = chip.get_neighbours(current)
            random.shuffle(neighbours)

            # success check
            if dist == exact_length and current == end:
                return path[1:-1] if dist > 2 else []

            # prune
            if dist > exact_length:
                continue

            # explore neighbors unconstrained
            for neighbour in neighbours:
                if neighbour in path_set:
                    continue  # avoid looping over own path

                if neighbour == end and dist + 1 != exact_length:
                    continue
               
                queue.append((neighbour, path + [neighbour]))
        
