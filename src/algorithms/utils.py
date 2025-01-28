import pickle
import json
import os
import re
import csv
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.chip import Chip

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

def extract_algo_name_from_plot_title(plot_file_path: str, chip_id: int, net_id: int) -> str:
    with open(plot_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Find the algorithm from the Plotly title
    match = re.search(re.escape(f'"title":{"{"}"text":"Chip {chip_id}, Net {net_id} -') + r'(.*?)\(', html_content, re.DOTALL)
    
    algorithm = ""
    if match:
        algorithm = match.group(1).strip()
    
    return algorithm
    

def clean_np_int64(file_path: str) -> None:
    # Read the entire file into memory
    with open(file_path, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        rows = list(reader)

    # Process the rows
    cleaned_rows = []
    for row in rows:
        cleaned_row = [re.sub(r"np\.int64\((\d+)\)", r"\1", cell) for cell in row]
        cleaned_rows.append(cleaned_row)

    # Write the cleaned content back to the same file
    with open(file_path, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(cleaned_rows)

def extract_chip_id_net_id_from_file_name(file_path: str) -> tuple[int, int]:
    """Extracts the chip_id and net_id from a file path"""
    possible_patterns = [
        r"c(\d+)w(\d+)",
        r"chip(\d+)w(\d+)",
        r"chip(\d+)_net(\d+)"
    ]

    for pattern in possible_patterns:
        match = re.search(pattern, file_path)
        if match:
            chip_id = int(match.group(1))
            net_id = int(match.group(2))
            return chip_id, net_id
    
    raise ValueError("Could not extract chip_id and net_id from file path")


def run_algorithm(
    chip: 'Chip', 
    algorithm_name: str, 
    routing_type: str="A*", 
    shuffle_wires: bool=False, 
    iterations: int=1, 
    save_wire_config: bool=False,
    use_plot: bool=False,
    save_plot: bool=False
) -> None:
    from src.algorithms.A_star import A_star, A_star_optimize
    from src.algorithms.greed import Greed, Greed_random
    from src.algorithms.random_algo import Pseudo_random, True_random
    from src.algorithms.IRRA import IRRA_PR, IRRA_A_star

    algorithm_name_options = {
        "Greed": Greed,
        "Greed Random": Greed_random,
        "GR": Greed_random,
        "Pseudo Random": Pseudo_random,
        "PR": Pseudo_random,
        "True Random": True_random,
        "TR": True_random,
        "A*": A_star,
        "IRRA_PR": IRRA_PR,
        "IRRA_A*": IRRA_A_star
    }

    routing_options = {
        "BFS": [False, False],
        "Simulated Annealing": [True, False],
        "A*": [False, True]
    }

    if algorithm_name not in algorithm_name_options:
        valid_options = "', '".join(algorithm_name_options.keys()).strip()
        raise ValueError(f"Algorithm name is invalid. Options: '{valid_options}'")
    
    if routing_type not in routing_options:
        valid_options = "', '".join(routing_options.keys()).strip()
        raise ValueError(f"Routing type is invalid. Options: '{valid_options}'")

    
    if "IRRA" in algorithm_name:
        simulated_annealing, A_star_rerouting = routing_options[routing_type]
        algorithm = algorithm_name_options[algorithm_name](
            chip, 
            shuffle_wires=shuffle_wires, 
            iterations=iterations, 
            simulated_annealing=simulated_annealing, 
            A_star_rerouting=A_star_rerouting,
            acceptable_intersection=500
        )
    else:
        algorithm = algorithm_name_options[algorithm_name](chip, shuffle_wires=shuffle_wires)
    
    if "IRRA" not in algorithm_name and iterations > 1:
        algorithm.run_random_netlist_orders(iterations)
    
    else:
        algorithm.run()

    if "IRRA" in algorithm_name:
        algorithm_name = algorithm_name + f" ({routing_type} routing)"
    
    if use_plot:
        save_plot_name = None
        if save_plot:
            save_plot_name = f"layout_chip_{chip.chip_id}_net_{chip.net_id}.html"

        chip.show_grid(save_plot_name, algorithm_name)


    if save_wire_config:
        save_csv_name = f"output_chip_{chip.chip_id}_net_{chip.net_id}.csv"
        chip.save_output(save_csv_name)


def optimize_chip(
    chip: 'Chip', 
    algo_used: str, 
    reroute_n_wires: int=10, 
    start_temperature: int=0, 
    alpha: float=0.99, 
    save_wire_config: bool=False,
    use_plot: bool=True, 
    save_plot: bool=False, 
    total_permutations_limit: int=500000, 
    amount_of_random_iterations: int=20000
) -> None:
    
    from src.algorithms.A_star import A_star_optimize

    a_star_optimize = A_star_optimize(chip)
    a_star_optimize.optimize(
        reroute_n_wires=reroute_n_wires, 
        start_temperature=start_temperature, 
        alpha=alpha,
        total_permutations_limit=total_permutations_limit,
        amount_of_random_iterations=amount_of_random_iterations
    )

    if "+ A* optimize" not in algo_used and algo_used:
        algorithm_new_name = f"{algo_used} + A* optimize"
    else:
        algorithm_new_name = algo_used

    if use_plot:
        save_plot_name = None
        if save_plot:
            save_plot_name = f"optimized_layout_chip_{chip.chip_id}_net_{chip.net_id}.html"

        chip.show_grid(save_plot_name, algorithm_new_name)

    if save_wire_config:
        save_csv_name = f"optimized_output_chip_{chip.chip_id}_net_{chip.net_id}.csv"
        chip.save_output(save_csv_name)