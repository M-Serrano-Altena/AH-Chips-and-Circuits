from src.classes.chip import Chip
from src.algorithms import IRRA
import subprocess
import time
import copy
import statistics
import json
from src.algorithms.utils import save_object_to_json_file

"""
In this file we run an experiment on pseudorandom input and the differences between BFS, BFS + Simulated Annealing and A_star rerouting
"""

chip_id = 2
net_id = 7

# 1) we initialize the chip
base_data_path = r"data/"
chip0 = Chip(base_data_path, chip_id=chip_id, net_id=net_id, output_folder="output", padding=1)
chip_og = copy.deepcopy(chip0)

start = time.time()
n_runs = 0
all_costs = []
short_circuit_count = []
results = []
boolian_variation = [{"sim_anneal": False, "A_star": False}, {"sim_anneal": False, "A_star": False}, {"sim_anneal": False, "A_star": False}]

RUNTIME_H = 1
RUNTIME_S = 30

if RUNTIME_S == 0:
    RUNTIME_S = 3600 * RUNTIME_H

for offset in range(10, 100, 2):
    while time.time() - start < RUNTIME_S:
        print(f"Offset: {offset} | run: {n_runs}")
        chip = chip_og
        irra_irra = IRRA.IRRA(chip= chip, iterations=1, intersection_limit=0, acceptable_intersection=100, rerouting_offset=offset, simulated_annealing=True, start_temperature=1000, temperature_alpha=0.95)
        best_chip = irra_irra.run()
        all_costs.append(best_chip.calc_total_grid_cost())
        short_circuit_count.append(best_chip.get_wire_intersect_amount())
        n_runs += 1

    results.append({
            "offset": offset,
            "mean_cost": statistics.mean(all_costs),
            "median_cost": statistics.median(all_costs),
            "stdev_cost": statistics.stdev(all_costs),
            "best_cost found": min(all_costs),
            "median short circuit": statistics.median(short_circuit_count),
            "lowest short circuit": min(short_circuit_count),
            "n_runs": n_runs, 
            "all_costs": all_costs,
            "short_circuit_count": short_circuit_count
            })
    all_costs = []
    short_circuit_count = []
    start = time.time()
    n_runs = 0

output_file = f'output/parameter_research/chip{chip_id}w{net_id}_offset_test.json'
save_object_to_json_file(results, output_file)