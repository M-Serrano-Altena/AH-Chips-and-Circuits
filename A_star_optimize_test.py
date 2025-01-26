from src.classes.chip import load_chip_from_csv
from src.algorithms.A_star import A_star_optimize
from src.algorithms.utils import extract_algo_name_from_plot_title, add_missing_extension
from sys import argv
import os


FILE_FOLDER = "best_output"
OUTPUT_FOLDER = "output"

base_data_path = r"data/"

# variables to change
chip_id = 2
net_id = 7
padding = 5
reroute_n_wires = 3

if len(argv) >= 2:
    chip_id = argv[1]

if len(argv) == 3:
    net_id = argv[2]

csv_file_name = f"best_output_chip_{chip_id}_net_{net_id}.csv"
csv_file_path = os.path.join(FILE_FOLDER, "csv", csv_file_name)


plot_file_name = f"best_layout_chip_{chip_id}_net_{net_id}.html"
plot_file_path = os.path.join(FILE_FOLDER, "img", plot_file_name)

algorithm_used_name = extract_algo_name_from_plot_title(plot_file_path, chip_id=chip_id, net_id=net_id)

chip = load_chip_from_csv(csv_file_path, padding=padding)
a_star_optimize = A_star_optimize(chip)
a_star_optimize.optimize(reroute_n_wires=reroute_n_wires, start_temperature=5, alpha=0.99)

if "+ A* optimize" not in algorithm_used_name and algorithm_used_name:
    algorithm_new_name = f"{algorithm_used_name} + A* optimize"
else:
    algorithm_new_name = algorithm_used_name

save_csv_name = f"optimized_output_chip_{chip_id}_net_{net_id}.csv"
save_plot_name = f"optimized_output_chip_{chip_id}_net_{net_id}.html"

chip.show_grid(save_plot_name, algorithm_new_name)
chip.save_output(save_csv_name)