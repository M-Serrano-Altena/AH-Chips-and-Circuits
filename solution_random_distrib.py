from src.classes.chip import Chip
from src.algorithms import random_algo as ra
import os
from sys import argv
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(__file__)
os.chdir(BASE_DIR)

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
    algorithm = ra.Random_random(chip, max_offset=30, allow_short_circuit=True, sort_wires=True, random_seed=i)
    algorithm.run()
    cost = chip.calc_total_grid_cost()
    total_costs.append(cost)

print(total_costs)
total_costs = [38739, 45947, 40217, 45660, 42362, 55033, 41994, 54411, 60405, 40858, 40234, 46870, 60793, 56239, 52909, 50168, 56811, 49266, 52919, 52919, 51697, 55929, 57161, 61979, 57735, 49877, 52009, 55911, 64679, 46291, 43203, 54409, 48091, 47471, 35066, 49646, 46931, 49899, 49235, 58622, 43208, 47739, 51709, 51697, 48964, 49933, 54102, 51389, 55912, 49911, 56497, 51420, 57769, 45083, 52304, 64395, 41155, 56221, 52008, 60167, 53451, 42040, 49615, 47739, 52920, 48663, 55031, 38415, 57454, 55035, 55307, 63775, 62899, 59905, 35697, 43555, 47465, 50801, 43238, 54698, 50473, 61651, 37483, 39276, 46248, 55323, 52310, 60754, 52629, 49620, 50851, 54169, 50195, 55011, 62610, 47429, 59255, 48971, 44167, 41425]

plt.title(f"Cost Histogram Random Algorithm (Chip {chip_id}, Net {net_id})")
plt.hist(total_costs, color='blue', bins=10)
plt.xlabel("Cost")
plt.ylabel("Frequency")

distrib_path = os.path.join(OUTPUT_FOLDER, "distributions")
save_name = f"cost_distrib_random_chip_{chip_id}_net{net_id}"
save_path = os.path.join(distrib_path, save_name)
plt.savefig(save_path)

