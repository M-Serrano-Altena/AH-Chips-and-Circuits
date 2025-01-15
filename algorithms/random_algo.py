from algorithms.utils import *
from algorithms.greed import Greed_random

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

            # generate and shuffle possible offsets [0, 2, 4, ..., max_offset]
            offset_candidates = list(range(0, self.max_offset + 1, 2))
            random.shuffle(offset_candidates)

            for offset in offset_candidates:
                path = self.bfs_route(
                    chip=self.chip,
                    start=start,
                    end=end,
                    offset=offset,
                    allow_short_circuit=False,
                    max_only=True  # route must be exactly manhattan_dist + offset
                )

                if path is not None:
                    print(f"[Random] Found path with offset={offset} for wire={wire.gates}")
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