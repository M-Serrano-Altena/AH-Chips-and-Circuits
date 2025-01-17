import os
from src.classes.chip import Chip
from src.algorithms.A_star import A_star
from sys import argv
from math import inf

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
algorithm = A_star(chip, allow_intersections=True, best_n_nodes=inf)

# all_wire_segments = algorithm.solve()
# all_wire_segments = algorithm.solve_n_random_netlist_orders(random_netlist_order_amt=100)

intersection_wires = [
    [(1, 5, 0), (2, 5, 0), (3, 5, 0), (4, 5, 0), (5, 5, 0), (6, 5, 0)],
    [(6, 5, 0), (6, 5, 1), (6, 4, 1), (5, 4, 1), (5, 3, 1), (5, 2, 1), (6, 2, 1), (6, 2, 0)],
    [(6, 2, 0), (7, 2, 0), (7, 1, 0), (6, 1, 0), (5, 1, 0), (4, 1, 0), (3, 1, 0)],
    [(3, 1, 0), (3, 2, 0), (3, 3, 0), (4, 3, 0), (5, 3, 0), (5, 3, 1), (5, 3, 2), (4, 3, 2), (4, 4, 2), (4, 4, 1), (4,4,0)],
    [(4, 4, 0), (3, 4, 0), (2, 4, 0), (1, 4, 0), (1, 5, 0)]
]

double_wire_intersection = [
    [(1, 5, 0), (2, 5, 0), (3, 5, 0), (4, 5, 0), (5, 5, 0), (6, 5, 0)],
    [(6, 5, 0), (6, 5, 1), (6, 4, 1), (5, 4, 1), (5, 3, 1), (5, 2, 1), (6, 2, 1), (6, 2, 0)],
    [(6, 2, 0), (7, 2, 0), (7, 1, 0), (6, 1, 0), (5, 1, 0), (4, 1, 0), (3, 1, 0)],
    [(3, 1, 0), (3, 2, 0), (3, 3, 0), (4, 3, 0), (5, 3, 0), (5, 3, 1), (5, 3, 2), (4, 3, 2), (4, 4, 2), (4, 4, 1), (4,4,0)],
    [(4, 4, 0), (3, 4, 0), (3, 4, 1), (3, 3, 1), (4, 3, 1), (5, 3, 1), (6, 3, 1), (7, 3, 1), (7, 4, 1), (7, 5, 1), (7, 6, 1), (7, 6, 0), (6, 6, 0), (5, 6, 0), (4, 6, 0), (3, 6, 0), (2, 6, 0), (1, 6, 0), (1, 5, 0)]
]

collision_wires = [
    [(1, 5, 0), (2, 5, 0), (3, 5, 0), (4, 5, 0), (5, 5, 0), (6, 5, 0)],
    [(6, 5, 0), (6, 5, 1), (6, 4, 1), (5, 4, 1), (5, 3, 1), (5, 2, 1), (6, 2, 1), (6, 2, 0)],
    [(6, 2, 0), (7, 2, 0), (7, 1, 0), (6, 1, 0), (5, 1, 0), (4, 1, 0), (3, 1, 0)],
    [(3, 1, 0), (3, 2, 0), (3, 3, 0), (4, 3, 0), (5, 3, 0), (5, 3, 1), (5, 4, 1), (4, 4, 1), (4,4,0)],
    [(4, 4, 0), (3, 4, 0), (2, 4, 0), (1, 4, 0), (1, 5, 0)]
]

chip.add_entire_wires(collision_wires)

base_save_name = f"chip_{chip_id}_net_{net_id}"
plot_save_name = "layout_" + base_save_name
csv_save_name = "output_" + base_save_name

chip.show_grid(plot_save_name)
chip.save_output(csv_save_name)