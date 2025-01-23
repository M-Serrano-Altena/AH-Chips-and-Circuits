import os
from src.classes.chip import Chip
from src.algorithms.A_star import A_star
from sys import argv
from math import inf

# travel to base folder
# BASE_DIR = os.path.dirname(__file__)
# os.chdir(BASE_DIR)

OUTPUT_FOLDER = "output"

base_data_path = r"data/"
chip_id = 1
net_id = 4

if len(argv) >= 2:
    chip_id = argv[1]

if len(argv) == 3:
    net_id = argv[2]

chip = Chip(base_data_path, chip_id=chip_id, net_id=net_id, output_folder=OUTPUT_FOLDER, padding=1)
algorithm = A_star(chip, 1000, True, True)

# algorithm.run()
chip = algorithm.run_random_netlist_orders(iterations=1000)

base_save_name = f"chip_{chip_id}_net_{net_id}"
plot_save_name = "layout_" + base_save_name
csv_save_name = "output_" + base_save_name

chip.show_grid(plot_save_name, "A*")
chip.save_output(csv_save_name)