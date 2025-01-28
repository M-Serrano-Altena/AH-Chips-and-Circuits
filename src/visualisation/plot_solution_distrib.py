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
):
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

    save_path_hist_cost = os.path.join(plot_save_base_dir, plot_costs_save_name)
    plt.savefig(save_path_hist_cost)

    fig = plt.figure()
    plt.title(f"Intersections Histogram {algorithm_name} Algorithm (Chip {chip_id}, Net {net_id}, n={len(total_intersections)})")
    plt.hist(total_intersections, bins=bins, color='green')
    plt.xlabel("Intersections")
    plt.ylabel("Frequency")


    if plot_intersections_save_name is None:
        plot_intersections_save_name = f"chip{chip_id}w{net_id}_intersections_distrib_{algorithm_name_file}.png"

    save_path_hist_intersections = os.path.join(plot_save_base_dir, plot_intersections_save_name)
    plt.savefig(save_path_hist_intersections)