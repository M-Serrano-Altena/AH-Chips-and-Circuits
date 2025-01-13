import os
from classes.chip import Chip
from algorithms.A_star import A_star
from sys import argv

# travel to base folder
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

chip = Chip(base_data_path, chip_id=chip_id, net_id=net_id, output_folder=OUTPUT_FOLDER)
algorithm = A_star(chip, allow_intersections=True)

all_wire_segments = algorithm.solve()
chip.add_entire_wires(all_wire_segments)

base_save_name = f"chip_{chip_id}_net_{net_id}"
plot_save_name = "layout_" + base_save_name
csv_save_name = "output_" + base_save_name

chip.show_grid(plot_save_name)
chip.save_output(csv_save_name)