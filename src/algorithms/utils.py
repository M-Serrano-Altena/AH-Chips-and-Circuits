INTERSECTION_COST = 300
COLLISION_COST = 1000000

Coords_3D = tuple[int, int, int]

class Node:
    def __init__(self, position: Coords_3D, parent: "Node", cost: int=0):
        # here the state is just the node coords
        self.position = position
        self.parent = parent
        self.cost = cost # associated cost of a node

    def __repr__(self):
        return f"Node(coords = {self.position}, cost = {self.cost})"


def cost_function(wire_length: int, intersect_amount: int, collision_amount: int=0) -> int:
    """Calculates the cost of creating the chip"""
    return wire_length + INTERSECTION_COST * intersect_amount + COLLISION_COST * collision_amount

def manhattan_distance(coord1: Coords_3D, coord2: Coords_3D):
    """Calculates the Manhattan distance between two coordinates"""
    return abs(coord1[0] - coord2[0]) + abs(coord1[1] - coord2[1]) + abs(coord1[2] - coord2[2])