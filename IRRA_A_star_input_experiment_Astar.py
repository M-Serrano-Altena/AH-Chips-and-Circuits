from src.classes.chip import Chip
from src.algorithms import IRRA
import time
import copy
import statistics
import json
from math import inf

"""
In this file we run an experiment on pseudorandom input and the differences between BFS, BFS + Simulated Annealing and A_star rerouting
We have found that the optimal parameters for A_star_input annealing are: start_temperature: 750, temperature_alpha: 0.99
"""

chip_id = 2
net_id = 7

# 1) we initialize the chip
base_data_path = r"data/"
chip0 = Chip(base_data_path, chip_id=chip_id, net_id=net_id, output_folder="output/Astar_vs_PR", padding=1)
chip_og = copy.deepcopy(chip0)

start = time.time()
n_runs = 0
all_costs = []
short_circuit_count = []
results = []
boolian_variation = [[False, False], [True, False], [False, True]]
technique_names = ["IRRA_A*_BFS", "IRRA_A*_Annealing", "IRRA_A*_A*"]
best_output = []
best_chip = None
lowest_cost = inf

                     
                     
for i, reroute_type in enumerate(boolian_variation):
    while n_runs < 10000:
        print(f"run: {n_runs} of {reroute_type}")
        chip0 = chip_og
        irra_irra = IRRA.IRRA_A_star(chip= chip0, iterations=1, intersection_limit= 0, acceptable_intersection=100, simulated_annealing = reroute_type[0], A_star_rerouting= reroute_type[1], start_temperature = 750, temperature_alpha = 0.99)
        candidate_chip = irra_irra.run()
        chip_cost = candidate_chip.calc_total_grid_cost()
        short_circuit_count.append(candidate_chip.get_wire_intersect_amount())
        n_runs += 1
        if chip_cost < lowest_cost:
            best_chip = candidate_chip
            lowest_cost = chip_cost
            best_algorithm = technique_names[i]
        all_costs.append(chip_cost)

    results.append({
            "simulated annealing": reroute_type[0],
            "a_star_rerouting": reroute_type[1],
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

output_file = 'output/Astar_input/chip2w7_astar_10000_test_final.json' 
with open(output_file, 'w') as file:
    json.dump(results, file, indent=4)

best_chip.save_output('chip2w7_astar_10000_test_final.csv')
best_chip.show_grid('chip2w7_astar_10000_test_final.html', best_algorithm)