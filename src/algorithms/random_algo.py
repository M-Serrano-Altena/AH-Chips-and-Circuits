from src.classes.chip import Chip
from src.algorithms.utils import Coords_3D, manhattan_distance
from src.algorithms.greed import Greed_random
from collections import deque
import random

class Pseudo_random(Greed_random):
    """
    A class that extends `Greed_random` and implements a pseudo-random wire routing algorithm.
    
    This method connects wires in a chip by first attempting to generate paths with random offsets
    around the minimum length between gates, using a breadth-first search (BFS) to find valid routes.
    The routing process avoids collisions and occupancy constraints by iterating over potential wire 
    lengths and trying them until a valid path is found.
    """
    def run(self) -> None:
        """
        Runs the pseudo-random wire routing algorithm for all unconnected wires in the chip.
        
        For each wire, the method attempts to find a valid path between its gates by generating 
        random lengths within a specified range and using BFS to explore possible paths.
        Once a path is found, the wire segments are added to the chip's occupancy grid and the wire
        is updated with the new coordinates.
        """
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

            # we let this loop until all wires have been tried for random offsets
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


    @staticmethod
    def bfs_route_exact_length(chip: Chip, start: Coords_3D, end: Coords_3D, exact_length: int) -> list[Coords_3D]|None:
        """
        Finds a path of exactly `exact_length` steps from `start` to `end` using BFS, while considering
        grid occupancy and gate constraints.

        Parameters:
        chip (Chip): The chip object that contains the grid and wire information.
        start (Coords_3D): The starting coordinate of the wire.
        end (Coords_3D): The ending coordinate of the wire.
        exact_length (int): The exact length of the path to be found.

        Returns:
        list[Coords_3D] | None: A list of coordinates representing the path, or None if no valid path is found.
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
    A class that extends `Pseudo_random` but allows wires to pass through anything,
    ignoring both collisions and gate occupancy.

    This method still ensures that wires do not revisit the same coordinate within
    the same routing attempt to avoid infinite loops, but it does not account for
    any other constraints like gate or wire segment collisions.
    """

    def run(self) -> None:
        """
        Runs the true-random wire routing algorithm for all unconnected wires in the chip.
        
        Unlike the `Pseudo_random` algorithm, this method does not consider grid occupancy
        or gate constraints. Wires can pass freely through any obstacles, but the pathfinding
        still avoids revisiting the same coordinate within a single path.
        """

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
        Finds a path of exactly `exact_length` steps from `start` to `end` while ignoring all
        constraints (like collisions and gate occupancy). The BFS ensures the path does not revisit
        the same coordinate within its current route.

        Parameters:
        chip (Chip): The chip object containing grid information.
        start (Coords_3D): The starting coordinate for the wire.
        end (Coords_3D): The ending coordinate for the wire.
        exact_length (int): The exact number of steps required in the path.

        Returns:
        list[Coords_3D] | None: A list of coordinates representing the path, or None if no valid path is found.
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