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
    return wire_length + INTERSECTION_COST * intersect_amount