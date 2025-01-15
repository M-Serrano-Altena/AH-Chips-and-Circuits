import random
from typing import TYPE_CHECKING

# only imported for typing to avoid circular importing
if TYPE_CHECKING:
    from classes.chip import Chip
    from classes.wire import Wire


INTERSECTION_COST = 300
COLLISION_COST = 1000000

Coords_3D = tuple[int, int, int]

class Node:
    def __init__(self, state: Coords_3D, parent: "Node", cost: int=0):
        # here the state is just the node coords
        self.state = state
        self.parent = parent
        self.cost = cost # associated cost of a node

    def __repr__(self):
        return f"Node(coords = {self.state}, cost = {self.cost})"


def cost_function(wire_length: int, intersect_amount: int) -> int:
    """Calculates the cost of creating the chip"""
    return wire_length + INTERSECTION_COST * intersect_amount

def manhattan_distance(coord1: Coords_3D, coord2: Coords_3D):
    """Returns the manhattan distance between two points"""
    return sum(abs(coord1[i] - coord2[i]) for i in range(len(coord1)))


def shortest_cable(wire: 'Wire') -> None:
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

        current_coord = tuple(current_coord[i] + move[i] for i in range(len(current_coord)))
        wire.append_wire_segment(current_coord)

