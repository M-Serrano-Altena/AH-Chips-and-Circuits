import os
from src.algorithms.utils import load_object_from_json_file, extract_chip_id_net_id_from_file_name
import matplotlib.pyplot as plt

def create_solution_distribution_hist(
    json_solution_distrib_filepath: str, 
    algorithm_name: str,
    chip_id: int|None=None, 
    net_id: int|None=None,
    bins: int=59,
    plot_costs_save_name: str|None=None, 
    plot_intersections_save_name: str|None=None, 
    plot_save_base_dir: str="results/latest/experiment_plots"
) -> None:
    """
    Creates and saves a cost and intersection histogram of the solution distribution for the given algorithm.

    This function loads the solution distribution data from a JSON file, then creates two histograms: 
    one showing the distribution of costs and the other showing the distribution of intersections 
    for the given algorithm. The histograms are saved as PNG files.

    Args:
        json_solution_distrib_filepath (str): Path to the JSON file containing solution distribution data.
        algorithm_name (str): Name of the algorithm (e.g., "A*", "PR", "Greed", "IRRA_PR", etc.).
        chip_id (int, optional): The chip ID to include in the plot title and filename. 
                                 If not provided, extracted from the filename.
        net_id (int, optional): The net ID to include in the plot title and filename. 
                                If not provided, extracted from the filename.
        bins (int, optional): Number of bins for the histograms. Default is 59.
        plot_costs_save_name (str, optional): Name of the output plot file for the cost histogram.
                                               If not provided, a default name based on chip and net IDs is used.
        plot_intersections_save_name (str, optional): Name of the output plot file for the intersections histogram.
                                                     If not provided, a default name based on chip and net IDs is used.
        plot_save_base_dir (str): Directory where the plots will be saved. Defaults to "results/latest/experiment_plots".

    Returns:
        None: The function saves the cost and intersection histograms as PNG files to the specified directory.
    """
    if chip_id is None or net_id is None:
        chip_id, net_id = extract_chip_id_net_id_from_file_name(json_solution_distrib_filepath)

    results = load_object_from_json_file(json_solution_distrib_filepath)
    total_costs = results["all_costs"]
    total_intersections = results["short_circuit_count"]

    algorithm_name_file = algorithm_name.replace(" ", "_")
    algorithm_name_file = algorithm_name_file.replace("A*", "astar").lower()

    fig = plt.figure()
    plt.title(f"Cost Histogram {algorithm_name} Algorithm (Chip {chip_id}, Net {net_id}, n={len(total_costs)})")
    plt.hist(total_costs, bins=bins, color='blue')
    plt.xlabel("Cost")
    plt.ylabel("Frequency")

    if plot_costs_save_name is None:
        plot_costs_save_name = f"chip{chip_id}w{net_id}_cost_distrib_{algorithm_name_file}.png"

    os.makedirs(plot_save_base_dir, exist_ok=True)

    save_path_hist_cost = os.path.join(plot_save_base_dir, plot_costs_save_name)
    plt.savefig(save_path_hist_cost)

    fig = plt.figure()
    plt.title(f"Short Circuit Histogram {algorithm_name} Algorithm (Chip {chip_id}, Net {net_id}, n={len(total_intersections)})")
    plt.hist(total_intersections, bins=bins, color='green')
    plt.xlabel("Short Circuit Count")
    plt.ylabel("Frequency")


    if plot_intersections_save_name is None:
        plot_intersections_save_name = f"chip{chip_id}w{net_id}_intersections_distrib_{algorithm_name_file}.png"

    save_path_hist_intersections = os.path.join(plot_save_base_dir, plot_intersections_save_name)
    
    plt.savefig(save_path_hist_intersections)
    plt.clf()