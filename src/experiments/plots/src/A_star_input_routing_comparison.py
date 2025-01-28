import os
import sys

# add the base folder to sys so that the modules are found
current_dir = os.path.dirname(__file__)
base_folder = os.path.join(current_dir, "..")
os.chdir(base_folder)
sys.path.append(base_folder)

import matplotlib.pyplot as plt
from src.algorithms.utils import load_object_from_json_file


output_folder = os.path.join("output", "Astar_input")
A_star_results_file = "chip2w7_astar_10000_test_final.json"
A_star_results_path = os.path.join(output_folder, A_star_results_file)

A_star_input_results = load_object_from_json_file(A_star_results_path)

short_circuit_bfs, short_circuit_anneal, short_circuit_astar = [result["short_circuit_count"] for result in A_star_input_results]


plt.title("IRRA A* input routing comparison")
plt.hist(short_circuit_bfs, color='b', bins=63, alpha=0.7, label="BFS routing", zorder=2)
plt.hist(short_circuit_anneal, color='g', bins=58, alpha=0.7, label="Simulated Annealing routing", zorder=1)
plt.hist(short_circuit_astar, color='r', bins=69, alpha=0.7, label="A* routing", zorder=0)

plt.xlabel("Amount of Short Circuits")
plt.ylabel("Frequency")
plt.legend()

save_folder = os.path.join(current_dir, "output")
save_name = "A_star_input_routing_comparison.png"
save_path = os.path.join(save_folder, save_name)
plt.savefig(save_path)