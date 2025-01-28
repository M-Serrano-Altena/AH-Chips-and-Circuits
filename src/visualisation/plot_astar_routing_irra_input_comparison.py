import os
import matplotlib.pyplot as plt
from src.algorithms.utils import load_object_from_json_file, extract_chip_id_net_id_from_file_name
import random

def create_input_comparison_hist(
    json_pr_path: str, 
    json_astar_path: str, 
    routing_type: str,
    chip_id: int|None=None, 
    net_id: int|None=None, 
    plot_save_name: str|None=None, 
    plot_save_base_dir: str="results/latest/experiment_plots"
) -> None:
    if chip_id is None or net_id is None:
        chip_id, net_id = extract_chip_id_net_id_from_file_name(json_pr_path)

    routing_type_options = ["BFS", "Simulated Annealing", "A*"]
    if routing_type not in routing_type_options:
        valid_routing_types = "', '".join(routing_type_options).strip()
        raise ValueError(f"Invalid routing type. Options: '{valid_routing_types}'")
    
    routing_num = routing_type_options.index(routing_type)

    A_star_input_results = load_object_from_json_file(json_astar_path)
    pr_input_results = load_object_from_json_file(json_pr_path)

    # length of 1 is for the case when only a specific routing type
    # was selected in the json file
    if len(A_star_input_results) == 1:
        A_star_input_results = A_star_input_results[0]
    else:
        A_star_input_results = A_star_input_results[routing_num]

    if len(pr_input_results) == 1:
        pr_input_results = pr_input_results[0]
    else:
        pr_input_results = pr_input_results[routing_num]

    

    A_star_input_short_circuit = A_star_input_results["short_circuit_count"]
    pr_results_short_circuit = pr_input_results["short_circuit_count"]

    # make sure the lists are the same length
    if len(pr_results_short_circuit) < len(A_star_input_short_circuit):
        A_star_input_short_circuit = random.sample(A_star_input_short_circuit, len(pr_results_short_circuit))
    elif len(pr_results_short_circuit) > len(A_star_input_short_circuit):
        pr_input_results = random.sample(pr_results_short_circuit, len(A_star_input_short_circuit))

    plt.title(
        f"IRRA Pseudo Random vs A* ({routing_type} routing) "
        f"(Chip{chip_id}w{net_id}, n={len(pr_results_short_circuit)})"
    )
    plt.hist(A_star_input_short_circuit, color='b', bins=62, alpha=0.7, label="A* input", zorder=0)
    plt.hist(pr_results_short_circuit, color='g', bins=46, alpha=0.7, label="Pseudo Random input", zorder=1)

    plt.xlabel("Amount of Short Circuits")
    plt.ylabel("Frequency")
    plt.legend()

    routing_type = routing_type.replace(" ", "_")
    routing_type = routing_type.replace("*", "star")
    routing_type = routing_type.lower()

    if plot_save_name is None:
        plot_save_name = f"chip{chip_id}w{net_id}_irra_astar_vs_pr_input_{routing_type}_routing_comparison.png"

    save_path = os.path.join(plot_save_base_dir, plot_save_name)
    plt.savefig(save_path)