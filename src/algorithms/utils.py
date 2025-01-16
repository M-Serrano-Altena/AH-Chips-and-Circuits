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