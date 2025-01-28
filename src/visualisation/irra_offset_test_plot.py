from src.algorithms.utils import load_object_from_json_file, extract_chip_id_net_id_from_file_name
import matplotlib.pyplot as plt
import os

def create_offset_experiment_plot(
    json_offset_results_file: str, 
    chip_id: int|None=None, 
    net_id: int|None=None, 
    solution_input: str="PR", 
    routing_type: str="BFS",
    plot_save_name: str|None=None, 
    plot_save_base_dir: str="results/latest/experiment_plots"
) -> None:
    if chip_id is None or net_id is None:
        chip_id, net_id = extract_chip_id_net_id_from_file_name(json_offset_results_file)

    solution_input_options = ["PR", "A*"]
    if solution_input not in solution_input_options:
        raise ValueError("solution_input must be either 'PR' or 'A*'")
    
    routing_type_options = ["BFS", "Simulated Annealing"]
    if routing_type not in routing_type_options:
        raise ValueError("routing_type must be either 'BFS' or 'Simulated Annealing'")
    
    results = load_object_from_json_file(json_offset_results_file)
    offsets = []
    median_cost = []

    for result in results:
        offsets.append(result["offset"])
        median_cost.append(result["median_cost"])

    solution_input = solution_input.replace("*", "star")
    solution_input = solution_input.lower()

    routing_type = routing_type.replace("*", "star")
    routing_type = routing_type.replace(" ", "_")
    routing_type = routing_type.lower()


    if plot_save_name is None:
        plot_save_name = f"chip{chip_id}w{net_id}_{solution_input}_{routing_type}_routing_offset_exp_plot.png"

    plot_save_path = os.path.join(plot_save_base_dir, plot_save_name)

    plt.title(
        f"Median cost with different offsets (IRRA_{solution_input} - "
        f"{routing_type} routing, Chip {chip_id} Net {net_id})"
    )
    plt.plot(offsets, median_cost, 'bo')
    plt.xlabel("Offset")
    plt.ylabel("Median cost")
    plt.savefig(plot_save_path)
