import os
import matplotlib.pyplot as plt
from src.algorithms.utils import load_object_from_json_file, extract_chip_id_net_id_from_file_name


def create_routing_comparison_hist(
    json_data_filepath: str, 
    solution_input: str, 
    chip_id: int|None=None, 
    net_id: int|None=None, 
    plot_save_name: str|None=None, 
    plot_save_base_dir: str="results/latest/experiment_plots"
) -> None:
    """
    Creates and saves a histogram comparing IRRA routing methods for a given solution input.
    
    This function loads routing data from a JSON file, then generates a histogram comparing the 
    distribution of short circuits for the three routing algorithms (BFS, Simulated Annealing, and A*) 
    for the provided solution input ('PR' or 'A*'). The histogram is saved as a PNG file.

    Args:
        json_data_filepath (str): Path to the JSON file containing routing comparison data.
        solution_input (str): The solution input type, either 'PR' (Pseudo-Random) or 'A*'.
        chip_id (int, optional): The chip ID to include in the plot title and filename. 
                                 If not provided, extracted from the filename.
        net_id (int, optional): The net ID to include in the plot title and filename.
                                If not provided, extracted from the filename.
        plot_save_name (str, optional): Name of the output plot file. If not provided, a default 
                                        name based on chip and net IDs is used.
        plot_save_base_dir (str): Directory where the plot will be saved. Defaults to 
                                  "results/latest/experiment_plots".

    Raises:
        ValueError: If `solution_input` is not either 'PR' or 'A*'.
    
    Returns:
        None: The function saves the plot to the specified directory and file path.
    """
    if chip_id is None or net_id is None:
        chip_id, net_id = extract_chip_id_net_id_from_file_name(json_data_filepath)

    solution_input_options = ["PR", "A*"]
    if solution_input not in solution_input_options:
        raise ValueError("solution_input must be either 'PR' or 'A*'")
    
    A_star_input_results = load_object_from_json_file(json_data_filepath)
    short_circuit_bfs, short_circuit_anneal, short_circuit_astar = [
        result["short_circuit_count"] for result in A_star_input_results
    ]

    plt.title(
        f"IRRA {solution_input} input, routing comparison "
        f"({solution_input} input, Chip{chip_id}w{net_id}, n={len(short_circuit_bfs)})"
    )
    plt.hist(short_circuit_bfs, color='b', bins=63, alpha=0.7, label="BFS routing", zorder=2)
    plt.hist(short_circuit_anneal, color='g', bins=58, alpha=0.7, label="Simulated Annealing routing", zorder=1)
    plt.hist(short_circuit_astar, color='r', bins=69, alpha=0.7, label="A* routing", zorder=0)

    plt.xlabel("Amount of Short Circuits")
    plt.ylabel("Frequency")
    plt.legend()

    solution_input = solution_input.replace("*", "star").lower()

    if plot_save_name is None:
        plot_save_name = (
            f"chip{chip_id}w{net_id}_irra_{solution_input}_input_routing_comparison.png"
        )

    os.makedirs(plot_save_base_dir, exist_ok=True)
    save_path = os.path.join(plot_save_base_dir, plot_save_name)
    
    plt.savefig(save_path)
    plt.clf()