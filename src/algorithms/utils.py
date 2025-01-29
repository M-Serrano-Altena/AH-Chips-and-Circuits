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
        self.position = position
        self.parent = parent
        self.cost = cost # associated cost of a node

    def __repr__(self):
        return f"Node(coords = {self.position}, cost = {self.cost})"


def cost_function(wire_length: int, intersect_amount: int, collision_amount: int=0) -> int:
    """
    Calculates the cost of the chip

    Args:
        wire_length (int): The length of the wire.
        intersect_amount (int): The number of intersections.
        collision_amount (int, optional): The number of collisions. Defaults to 0.

    Returns:
        int: The total cost of the chip.
    """
    return wire_length + INTERSECTION_COST * intersect_amount + COLLISION_COST * collision_amount

def manhattan_distance(coord1: Coords_3D, coord2: Coords_3D):
    """Calculates the Manhattan distance between two coordinates

    Args:
        coord1 (Coords_3D): The first coordinate.
        coord2 (Coords_3D): The second coordinate.

    Returns:
        int: The Manhattan distance between the two coordinates.
    """
    return abs(coord1[0] - coord2[0]) + abs(coord1[1] - coord2[1]) + abs(coord1[2] - coord2[2])


def convert_to_matrix_coords(coords, matrix_y_size):
    """
    Converts axis coords representation to matrix coords representation
    (in a matrix 0 is the top row as opposed to the bottom position for y)


    Args:
        coords (tuple): coordinates in axis representation
        matrix_y_size (int): the amount of rows the matrix has

    Returns:
        tuple: the matrix coordinates corresponding to the axis coordinates
    """
    x_coord, y_coord = coords
    return matrix_y_size - 1 - y_coord, x_coord

def add_missing_extension(filename: str, extension: str) -> str:
    """Add an extension to a filename if the extension is missing

    Args:
        filename (str): The filename.
        extension (str): The extension to add if missing.

    Returns:
        str: The filename with the extension.
    """
    base, existing_extension = os.path.splitext(filename)
    if not existing_extension:
        filename = filename + extension

    return filename

def save_object_to_pickle_file(object: Any, filename: str) -> None:
    """Saves an object to a pickle file

    Args:
        object (Any): The object to save.
        filename (str): The filename to save to.
    """
    filename = add_missing_extension(filename=filename, extension=".pkl")
    with open(filename, "wb") as file:
        pickle.dump(object, file)

def load_object_from_pickle_file(filename: str) -> Any:
    """Loads an object from a pickle file

    Args:
        filename (str): The filename to load from.

    Returns:
        Any: The loaded object.
    """
    filename = add_missing_extension(filename=filename, extension=".pkl")
    with open(filename, "rb") as file:
        return pickle.load(file)
    
def save_object_to_json_file(object: Any, filename: str) -> None:
    """Saves an object to a JSON file

    Args:
        object (Any): The object to save.
        filename (str): The filename to save to.
    """
    filename = add_missing_extension(filename=filename, extension=".json")
    with open(filename, "w") as file:
        json.dump(object, file, indent=4)

def load_object_from_json_file(filename: str) -> Any:
    """Loads an object from a JSON file

    Args:
        filename (str): The filename to load from.

    Returns:
        Any: The loaded object.
    """
    filename = add_missing_extension(filename=filename, extension=".json")
    with open(filename, "r") as file:
        return json.load(file)

def extract_algo_name_from_plot_title(plot_file_path: str, chip_id: int, net_id: int) -> str:
    """Extracts the algorithm name from the chip plot title

    Args:
        plot_file_path (str): The path to the plot file.
        chip_id (int): The chip ID.
        net_id (int): The net ID.

    Returns:
        str: The extracted algorithm name.
    """
    with open(plot_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Find the algorithm from the Plotly title
    match = re.search(re.escape(f'"title":{"{"}"text":"Chip {chip_id}, Net {net_id} -') + r'(.*?)\(', html_content, re.DOTALL)
    
    algorithm = ""
    if match:
        algorithm = match.group(1).strip()
    
    return algorithm
    

def clean_np_int64(file_path: str) -> None:
    """Removes np.int64 around numbers from a CSV file

    Args:
        file_path (str): The path to the CSV file.
    """
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
    """Extracts the chip_id and net_id from a file path

    Args:
        file_path (str): The file path from which to extract the chip_id and net_id.

    Returns:
        tuple[int, int]: The extracted chip_id and net_id.
    
    Raises:
        ValueError: If no chip_id and net_id can be extracted.
    """
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
    """Runs the specified algorithm on the chip

    Args:
        chip (Chip): The chip object to run the algorithm on.
        algorithm_name (str): The name of the algorithm to run.
        routing_type (str, optional): The routing type to use (with IRRA). Defaults to "A*".
        shuffle_wires (bool, optional): Whether to shuffle wires. Defaults to False.
        iterations (int, optional): The number of iterations to run. Defaults to 1.
        save_wire_config (bool, optional): Whether to save the wire configuration. Defaults to False.
        use_plot (bool, optional): Whether to display a plot. Defaults to False.
        save_plot (bool, optional): Whether to save the plot. Defaults to False.
    """

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
            acceptable_intersection=3000
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
    """Optimizes the chip layout using A* optimization

    Args:
        chip (Chip): The chip object to optimize.
        algo_used (str): The algorithm used for optimization.
        reroute_n_wires (int, optional): The number of wires to reroute. Defaults to 10.
        start_temperature (int, optional): The starting temperature for the optimization. Defaults to 0.
        alpha (float, optional): The cooling rate for the optimization. Defaults to 0.99.
        save_wire_config (bool, optional): Whether to save the wire configuration. Defaults to False.
        use_plot (bool, optional): Whether to display a plot. Defaults to True.
        save_plot (bool, optional): Whether to save the plot. Defaults to False.
        total_permutations_limit (int, optional): The total limit of permutations before switching to random permutations. Defaults to 500000.
        amount_of_random_iterations (int, optional): The number of random iterations to run after limit is exceeded. Defaults to 20000.
    """
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