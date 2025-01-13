import random
from collections import deque
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

def manhattan_distance(coord1, coord2):
    """ returns the distance between two points"""
    return abs(coord1[0] - coord2[0]) + abs(coord1[1] - coord2[1]) + abs(coord1[2] - coord2[2])


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

        current_coord = current_coord + move 
        wire.append_wire_segment(current_coord)


def get_neighbours(chip: 'Chip', coord: tuple[int,int,int]) -> list[tuple[int,int,int]]:
    """
    Return valid neighboring coordinates in 3D (±x, ±y, ±z), 
    ensuring we stay within the grid boundaries.
    """
    (x, y, z) = coord

    possible_moves = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    neighbours = []
    
    for (dx, dy, dz) in possible_moves:

        (nx, ny, nz) = (x + dx, y + dy, z + dz)

        # we check if options are within boundries of chip, if so we add to neighbours
        if (0 <= nx < chip.grid_size_x 
            and 0 <= ny < chip.grid_size_y 
            and 0 <= nz < chip.grid_size_z):

            neighbours.append((nx, ny, nz))

    return neighbours

def is_occupied(chip: 'Chip', coord: tuple[int,int,int], own_gates: set[tuple[int,int,int]] = None) -> bool:
    """ 
    Checks if `coord` is already occupied by any wire
    (Optionally checks if the coord is its own gate, to return false since occupation is from its own wire.) 
    """

    if own_gates and (coord in own_gates):
        return False

    gate_coords = set(chip.gates.values())
    if coord in gate_coords:
        return True

    for wire in chip.wires:
        if coord in wire.coords:
            return True
    return False

def bfs_route(chip: 'Chip', start: tuple[int,int,int], end: tuple[int,int,int], 
              max_extra_length: int = 0, allow_short_circuit: bool = False) -> list[tuple[int,int,int]]|None:
    """
    We use a breath first technique to find a route based on the Manhattan technique with an added max_extra_length to the minimal length of the route.
    We add a boolian to the function to allow or not allow short circuiting of the wire. 
    If we have found a path, we return the path as a list of tuples, otherwise we return None
    """

    manhattan_dist = abs(start[0]-end[0]) + abs(start[1]-end[1]) + abs(start[2]-end[2])
    limit = manhattan_dist + max_extra_length

    # queue consists of tuple entries of (current node, [path])
    queue = deque([(start, [start])])
    visited = set([start])

    wire_gates = {start, end}

    while queue:
        (current, path) = queue.popleft()
        if current == end:
            # we have made it to the end and return the path to the end
            return path[1:-1] if len(path) > 2 else []

        # if path is longer than limit, we prune
        if len(path) - 1 > limit:
            continue

        for neighbour in get_neighbours(chip, current):
            if neighbour not in visited:
                # if neighbour is occupied and we do not allow short circuit we continue, otherwise we save option
                if (not allow_short_circuit) and is_occupied(chip, neighbour, own_gates=wire_gates):
                    continue

                visited.add(neighbour)
                # we add the current node and path to the queue
                queue.append((neighbour, path + [neighbour]))

    return None
