import os
import seaborn as sns
import pandas as pd
from statistics import median, mean, stdev
import matplotlib.pyplot as plt
from src.algorithms.utils import load_object_from_json_file, extract_chip_id_net_id_from_file_name

def add_baseline_to_df(df: pd.DataFrame, json_baseline_path: str, input_solution: str) -> pd.DataFrame:
    if json_baseline_path is None:
        raise ValueError("json_baseline_path must be a valid path to a json file if add_baseline is True")

    baseline_results = load_object_from_json_file(json_baseline_path)
    baseline_costs = baseline_results["all_costs"]
    baseline_intersections = baseline_results["short_circuit_count"]
    baseline_dict = {
            "mean_cost": mean(baseline_costs),
            "median_cost": median(baseline_costs),
            "stdev_cost": stdev(baseline_costs),
            "best_cost found": min(baseline_costs),
            "median short circuit": median(baseline_intersections),
            "lowest short circuit": min(baseline_intersections),
            "n_runs": len(baseline_costs),
            "all_costs": baseline_costs,
            "short_circuit_count": baseline_intersections,
            "Routing": "Baseline",
            "Input Solution": input_solution
        }

    baseline_df = pd.DataFrame(baseline_dict)
    return pd.concat([baseline_df, df])


def create_irra_all_comparisons_boxplot(
    json_routing_comparison_astar_path: str, 
    json_routing_comparison_pr_path: str,
    chip_id: int|None=None, 
    net_id: int|None=None,
    add_baseline: bool=False,
    json_astar_solution_distrib_filepath: str|None=None,
    json_pr_solution_distrib_filepath: str|None=None,
    plot_save_name: str|None=None, 
    plot_save_base_dir: str="results/latest/experiment_plots"
):
    if chip_id is None or net_id is None:
        chip_id, net_id = extract_chip_id_net_id_from_file_name(json_routing_comparison_astar_path)

    A_star_input_results = load_object_from_json_file(json_routing_comparison_astar_path)
    pr_input_results = load_object_from_json_file(json_routing_comparison_pr_path)

    # create results dataframe for boxplot
    A_star_input_df = pd.concat([pd.DataFrame(A_star_input_result) for A_star_input_result in A_star_input_results])
    pr_input_df = pd.concat([pd.DataFrame(pr_input_result) for pr_input_result in pr_input_results])

    def determine_algorithm(row):
        if row["simulated annealing"]:
            return "Simulated Annealing"
        elif row["a_star_rerouting"]:
            return "A*"
        else:
            return "BFS"
        
    A_star_input_df["Routing"] = A_star_input_df.apply(determine_algorithm, axis=1)
    A_star_input_df = A_star_input_df.drop(columns=["simulated annealing", "a_star_rerouting"])

    pr_input_df["Routing"] = pr_input_df.apply(determine_algorithm, axis=1)
    pr_input_df = pr_input_df.drop(columns=["simulated annealing", "a_star_rerouting"])

    A_star_input_df["Input Solution"] = "A*"
    pr_input_df["Input Solution"] = "PR"

    if add_baseline:
        A_star_input_df = add_baseline_to_df(A_star_input_df, json_astar_solution_distrib_filepath, input_solution="A*")
        pr_input_df = add_baseline_to_df(pr_input_df, json_pr_solution_distrib_filepath, input_solution="PR")

    # add input results together
    results_df = pd.concat([pr_input_df, A_star_input_df])
    results_df.rename(columns={"short_circuit_count": "Short Circuit Count"}, inplace=True)

    if plot_save_name is None:
        plot_save_name = f"chip{chip_id}w{net_id}_irra_pr_vs_astar_boxplot.png"

    plot_output_path = os.path.join(plot_save_base_dir, plot_save_name)

    plt.title(f"Pseudo Random input vs A* input (Chip {chip_id}, Net {net_id})")
    sns.boxplot(x="Routing", y="Short Circuit Count", hue="Input Solution", palette=["m", "g"], data=results_df, width=0.75)

    plt.xlabel(xlabel="Routing", labelpad=17)
    plt.tight_layout()

    plt.savefig(plot_output_path)
