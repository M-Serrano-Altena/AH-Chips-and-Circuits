import os
import sys
import seaborn as sns
import pandas as pd

# add the base folder to sys so that the modules are found
current_dir = os.path.dirname(__file__)
base_folder = os.path.join(current_dir, "..")
os.chdir(base_folder)
sys.path.append(base_folder)

import matplotlib.pyplot as plt
from src.algorithms.utils import load_object_from_json_file
import random

A_star_input_results_folder = os.path.join("output", "Astar_input")
A_star_results_file = "chip2w7_astar_10000_test_final.json"
A_star_results_path = os.path.join(A_star_input_results_folder, A_star_results_file)

A_star_input_results = load_object_from_json_file(A_star_results_path)[2]
A_star_input_short_circuit = A_star_input_results["short_circuit_count"]


pr_input_results_folder = os.path.join("output", "PR_input")
pr_results_file = "chip2w7_astar_rerouting_1000_final.json"
pr_results_path = os.path.join(pr_input_results_folder, pr_results_file)

pr_input_results = load_object_from_json_file(pr_results_path)[0]
pr_results_short_circuit = pr_input_results["short_circuit_count"]

A_star_input_short_circuit_sample = random.sample(A_star_input_short_circuit, len(pr_results_short_circuit))


plt.title("IRRA A* input routing comparison")
plt.hist(A_star_input_short_circuit_sample, color='b', bins=62, alpha=0.7, label="A* input", zorder=0)
plt.hist(pr_results_short_circuit, color='g', bins=46, alpha=0.7, label="Pseudo Random input", zorder=1)

plt.xlabel("Amount of Short Circuits")
plt.ylabel("Frequency")
plt.legend()

save_folder = os.path.join(current_dir, "output")
save_name = "A_star_routing_input_comparison.png"
save_path = os.path.join(save_folder, save_name)
plt.savefig(save_path)