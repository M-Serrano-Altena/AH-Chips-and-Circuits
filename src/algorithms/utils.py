import pickle
import json
import os
from typing import Any

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


def add_missing_extension(filename: str, extension: str):
    """Add an extension to a filename if the extension is missing"""
    base, existing_extension = os.path.splitext(filename)
    if not existing_extension:
        filename = filename + extension

    return filename

def save_object_to_pickle_file(object: Any, filename: str):
    filename = add_missing_extension(filename=filename, extension=".pkl")
    with open(filename, "wb") as file:
        pickle.dump(object, file)

def load_object_from_pickle_file(filename: str):
    filename = add_missing_extension(filename=filename, extension=".pkl")
    with open(filename, "rb") as file:
        return pickle.load(file)
    
def save_object_to_json_file(object: Any, filename: str):
    filename = add_missing_extension(filename=filename, extension=".json")
    with open(filename, "w") as file:
        json.dump(object, file, indent=4)

def load_object_from_json_file(filename: str):
    filename = add_missing_extension(filename=filename, extension=".json")
    with open(filename, "r") as file:
        return json.load(file)