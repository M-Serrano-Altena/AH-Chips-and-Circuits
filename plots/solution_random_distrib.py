from src.classes.chip import Chip
from src.algorithms.utils import COLLISION_COST, save_object_to_json_file, load_object_from_json_file
from src.algorithms import random_algo as ra
import os
from sys import argv
import matplotlib.pyplot as plt
from brokenaxes import brokenaxes
import numpy as np

# BASE_DIR = os.path.dirname(__file__)
# os.chdir(BASE_DIR)

OUTPUT_FOLDER = "output"

base_data_path = r"data/"
chip_id = 0
net_id = 1

if len(argv) >= 2:
    chip_id = argv[1]

if len(argv) == 3:
    net_id = argv[2]


iterations = 0
total_costs = []

for i in range(iterations):
    print(i)
    chip = Chip(base_data_path, chip_id=chip_id, net_id=net_id, output_folder=OUTPUT_FOLDER)
    algorithm = ra.Pseudo_random(chip, max_offset=30, allow_short_circuit=True, sort_wires=True, random_seed=i)
    algorithm.run()
    cost = chip.calc_total_grid_cost()
    if chip.is_fully_connected():
        total_costs.append(cost)

print(total_costs)
distrib_path = os.path.join(OUTPUT_FOLDER, "distributions")

save_name_costs = f"total_costs_chip_{chip_id}_net_{net_id}"
save_path_costs = os.path.join(distrib_path, save_name_costs)

# save_object_to_json_file(total_costs, save_path_costs)
# total_costs = [38739, 45947, 40217, 54411, 60405, 60793, 56239, 52909, 56811, 52919, 51697, 55929, 57161, 57735, 55911, 64679, 54409, 49899, 49235, 51697, 49933, 51389, 49911, 57769, 64395, 56221, 60167, 53451, 49615, 47739, 48663, 55031, 63775, 62899, 59905, 50801, 50473, 55323, 50851, 54169, 50195, 55011, 59255, 48971, 44167, 41425, 58379, 55011, 45679, 56515, 46257, 47505, 48705, 49007, 43819, 44103, 51057, 52615, 41995, 48679, 50201, 57411, 47813, 52629, 52327, 53245, 50497, 54429, 42627, 65551, 47155, 46237, 48671, 52927, 50229, 54423, 45939, 63507, 55341, 61649, 50783, 46853, 46563, 39923, 52315, 62305, 44803, 41415, 56513, 46531, 52919, 56591, 52933, 51681, 63119, 50815, 53523, 51405, 45381, 51673, 45067, 55071, 41725, 41093, 65001, 58301, 58589, 43903, 54397, 44755, 55009, 49859, 51731, 43267, 51991, 61947, 52907, 46601, 55945, 55923, 48389, 52903, 45661, 51653, 46925, 39341, 53855, 54411, 48081, 52635, 60729, 48359, 58639, 57457, 45033, 50495, 59885, 44773, 46889, 52029, 60755, 53239, 48335, 54127, 55071, 42989, 44457, 39313, 46839, 43223, 48975, 50517, 56261, 55615, 43823, 45023, 59879, 48377, 47497, 52053, 49919, 69189, 61701, 46025, 53207, 51707, 50509, 49261, 59257, 46529, 56213, 60787, 46881, 56545, 50477, 46555, 55907, 46879, 46263, 49581, 54117, 45085, 42937, 45913, 55911, 43263, 44445, 58669, 51735, 54125, 52913, 45375, 53519, 54737, 49283, 48143, 48673, 47141, 41107, 56233, 55627, 50221, 53205, 53263, 58673, 53537, 50483, 53517, 48701, 61667, 48425, 41755, 48957, 45029, 59565, 55953, 61065, 54099, 54427, 51119, 49577, 48407, 45975, 47219, 54451, 46915]

load_path_costs = ""
if not load_path_costs:
    load_path_costs = save_path_costs

total_costs = load_object_from_json_file(load_path_costs)

plt.title(f"Cost Histogram Pseudo Random Algorithm (Chip {chip_id}, Net {net_id})")
plt.hist(total_costs, bins=20, color='blue')
plt.xlabel("Cost")
plt.ylabel("Frequency")

save_name_hist = f"cost_distrib_random_chip_{chip_id}_net{net_id}"
save_path_hist = os.path.join(distrib_path, save_name_hist)
plt.savefig(save_path_hist)

