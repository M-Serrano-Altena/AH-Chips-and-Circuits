# main.py (or any script you prefer)
from src.classes.chip import Chip
from src.algorithms import IRRA
import copy
import statistics
import json


chip_id = 2
net_id = 7

# 1) we initialize the chip
base_data_path = r"data/"
chip0 = Chip(base_data_path, chip_id=chip_id, net_id=net_id, output_folder="output", padding=1)
chip_og = copy.deepcopy(chip0)

temperature_candidates = [500, 750, 1000, 1500, 2000]
alpha_candidates = [0.9, 0.925, 0.95, 0.975, 0.99]
results = []

for temperature in temperature_candidates:
    for alpha in alpha_candidates:
        chip0 = chip_og
        irra_irra = IRRA.IRRA(chip= chip0, iterations=250, intersection_limit= 0, acceptable_intersection=100, simulated_annealing= True, temperature_alpha= alpha, start_temperature= temperature)
        best_chip = irra_irra.run()
        all_costs = irra_irra.all_costs
        results.append({
                "temperature": temperature,
                "alpha": alpha,
                "mean_cost": statistics.mean(all_costs),
                "median_cost": statistics.median(all_costs),
                "stdev_cost": statistics.stdev(all_costs),
                "best_cost found": min(all_costs),
                "all_costs": all_costs
                })
        
output_file = 'output/parameter_research/chip2w7_annealing_PseudoRandom.json'
with open(output_file, 'w') as file:
    json.dump(results, file, indent=4)


