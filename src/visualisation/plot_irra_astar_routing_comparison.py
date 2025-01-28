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

    save_path = os.path.join(plot_save_base_dir, plot_save_name)
    plt.savefig(save_path)