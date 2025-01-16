from classes.chip import Chip
from algorithms.utils import *
from algorithms.greed import Greed_random, Greed
from collections import deque

import random

class Random_random(Greed_random):

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

            wire.coords = [start, end] # reset the coords to just the gates

            max_length = self.max_offset + manhattan_distance(start, end)

            # generate and shuffle possible offsets [1, 2, 3, ..., max_length]
            max_length_candidates = list(range(1, max_length + 1))
            random.shuffle(max_length_candidates)

            for random_length in max_length_candidates:
                path = bfs_route_exact_length(
                    chip = self.chip,
                    start = start, 
                    end = end, 
                    exact_length = random_length
                )

                if path is not None:
                    print(f"[Random] Found path with random_length ={random_length} for wire={wire.gates}")
                    # append the path coords to the wire
                    for coord in path:
                        wire.append_wire_segment(coord)
                    break

            # we let this loop untill all wires have been tried for random offsets

        # if not all wires were connected with random offsets
        # fallback to the greed approach to find solution
        if self.chip.not_fully_connected:
            print("[Random] Falling back to parent (Greed) approach")
            super().run()

    from collections import deque

@staticmethod
def bfs_route_exact_length(chip: Chip, start: Coords_3D, end: Coords_3D, exact_length: int) -> list[Coords_3D]|None:
    """
    This function finds a route from start_gate to end_gate of exactly the length given 
    """
    # queue consists of tuple entries of (current node, [path])
    queue = deque([(start, [start])])
    # we store (node, dist) instead of node, this way we can make inefficient routes
    visited = set()  

    while queue:
        (current, path) = queue.popleft()
        dist = len(path)

        # check for success
        if current == end and dist == exact_length:
            return path[1:-1] if dist > 2 else []

        # prune if we exceed exact_length
        if dist > exact_length:
            continue

        # explore
        for neighbour in Greed.get_neighbours(chip, current):

            # if the coordinate is already in its own path we continue
            if neighbour in path:
                continue

            # if wiresegment cause wire_collision we continue 
            if Greed.wire_collision(chip, neighbour, current):
                continue

            # if neighbour contains another gate we continue
            if Greed.gate_occupied(chip, neighbour, {start, end}):
                continue

            newDist = dist + 1
            if (neighbour, newDist) not in visited:
                visited.add((neighbour, newDist))
                queue.append((neighbour, path + [neighbour]))

    return None
