import os
import sys
import seaborn as sns
import pandas as pd
from statistics import median, mean, stdev

# add the base folder to sys so that the modules are found
current_dir = os.path.dirname(__file__)
base_folder = os.path.join(current_dir, "..")
os.chdir(base_folder)
sys.path.append(base_folder)

import matplotlib.pyplot as plt
from src.algorithms.utils import load_object_from_json_file

# load data
output_folder = os.path.join("output", "Astar_vs_PR")
A_star_output_file = "chip2w7_astar_input_final.json"
pr_output_file = "chip2w7_PR_input_final.json"

A_star_input_results = load_object_from_json_file(os.path.join(output_folder, A_star_output_file))
pr_input_results = load_object_from_json_file(os.path.join(output_folder, pr_output_file))

# fix results dataframe for boxplot
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

# load baseline
baseline_folder = os.path.join("output", "distributions")
baseline_paths = {
    "pr_costs": os.path.join(baseline_folder, "total_costs_chip_2_net_7.json"),
    "astar_costs": os.path.join(baseline_folder, "total_costs_astar_chip_2_net_7.json"),
    "pr_intersections": os.path.join(baseline_folder, "total_intersections_chip_2_net_7.json"),
    "astar_intersections": os.path.join(baseline_folder, "total_intersections_astar_chip_2_net_7.json"),
}


A_star_input_baseline_cost = load_object_from_json_file(baseline_paths["astar_costs"])
A_star_input_baseline_short_circuit = load_object_from_json_file(baseline_paths["astar_intersections"])
pr_input_baseline_cost = load_object_from_json_file(baseline_paths["pr_costs"])
pr_input_baseline_short_circuit = load_object_from_json_file(baseline_paths["pr_intersections"])

def create_baseline_dict(basline_costs: list[int], baseline_short_circuits: list[int], input_solution: str):
    return {
        "mean_cost": mean(basline_costs),
        "median_cost": median(basline_costs),
        "stdev_cost": stdev(basline_costs),
        "best_cost found": min(basline_costs),
        "median short circuit": median(baseline_short_circuits),
        "lowest short circuit": min(baseline_short_circuits),
        "n_runs": len(basline_costs),
        "all_costs": basline_costs,
        "short_circuit_count": baseline_short_circuits,
        "Routing": "Baseline",
        "Input Solution": input_solution
    }

# add baseline to input dataframes
A_star_input_baseline_dict = create_baseline_dict(A_star_input_baseline_cost, A_star_input_baseline_short_circuit, "A*")
pr_input_baseline_dict = create_baseline_dict(pr_input_baseline_cost, pr_input_baseline_short_circuit, "PR")

A_star_input_baseline_df = pd.DataFrame(A_star_input_baseline_dict)
pr_input_baseline_df = pd.DataFrame(pr_input_baseline_dict)

A_star_input_df = pd.concat([A_star_input_baseline_df, A_star_input_df])
pr_input_df = pd.concat([pr_input_baseline_df, pr_input_df])


# add input results together
results_df = pd.concat([pr_input_df, A_star_input_df])
results_df.rename(columns={"short_circuit_count": "Short Circuit Count"}, inplace=True)

# print(results_df.columns)

plot_output_folder = "output"
plot_name = "A_star_vs_PR_boxplot.png"
plot_output_path = os.path.join(current_dir, plot_output_folder, plot_name)

plt.title("Pseudo Random input vs A* input")
sns.boxplot(x="Routing", y="Short Circuit Count", hue="Input Solution", palette=["m", "g"], data=results_df)
plt.savefig(plot_output_path)
