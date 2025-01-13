from classes.chip import *
from classes.wire import *
import random
from collections import deque


def cost_function(wire_length: int, intersect_amount: int) -> int:
    """Calculates the cost of creating the chip"""
    
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

def is_occupied(chip: 'Chip', coord: tuple[int,int,int]) -> bool:
    """ Checks if `coord` is already occupied by any wire (TODO: we now use an exception for gates). """

    gate_coords = set(chip.gates.values())
    if coord in gate_coords:
        return False

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

    queue = deque([(start, [start])])
    visited = set([start])

    while queue:
        (current, path) = queue.popleft()
        if current == end:
            # we have made it to the end and return the path to the end
            return path[1:-1] if len(path) > 2 else []

        # if path is longer than limit, we prune
        if len(path) - 1 > limit:
            continue

        for nbr in get_neighbours(chip, current):
            if nbr not in visited:
                # if short_circuit not allowed, we do not save nbr if occupied
                if (not allow_short_circuit) and is_occupied(chip, nbr):
                    continue

                visited.add(nbr)
                # we add the current node and path to the queue
                queue.append((nbr, path + [nbr]))

    return None