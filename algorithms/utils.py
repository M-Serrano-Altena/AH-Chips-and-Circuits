from classes.chip import *
from classes.wire import *
import random

def cost_function(wire_length: int, intersect_amount: int) -> int:
    return wire_length + 300 * intersect_amount

def shortest_cable(wire: Wire) -> None:
    """Adds a shortest possible wire route to the wire variable (chosen at random)"""

    # we get the start and end points of connection
    start = wire.coords[0]
    end = wire.coords[-1]

    # we calculate how many steps we need to make in each ditrection
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dz = end[2] - start[2]

    # now we create a list of moves needed to be made:

    moves = []

    for _ in range(abs(dx)):
        moves.append(((1, 0, 0) if dx > 0 else (-1, 0, 0)))
    for _ in range(abs(dy)):
        moves.append((0, 1, 0) if dy > 0 else (0, -1, 0))
    for _ in range(abs(dz)):
        moves.append(((0, 0, 1) if dz > 0 else (0, 0, -1)))

    # we have all our moves we need to make for the shortest route, now we shuffle the order to randomize route

    random.shuffle(moves)

    # we create and add the wire_segments to the wire

    current_coord = start

    for move in moves:

        current_coord = current_coord + move 
        wire.append_wire_segment(current_coord)