# main.py (or any script you prefer)
from src.classes.chip import Chip
from src.algorithms import IRRA
from sys import argv

chip_id = 1
net_id = 4

if len(argv) >= 2:
    chip_id = argv[1]

if len(argv) == 3:
    net_id = argv[2]

# 1) we initialize the chip
base_data_path = r"data/"
chip0 = Chip(base_data_path, chip_id=chip_id, net_id=net_id, output_folder="output", padding=1)

# 2) we use the algo with offset
irra_irra = IRRA.IRRA(chip= chip0, iterations=10, intersection_limit= 2, acceptable_intersection=10, simulated_annealing= True, temperature_alpha= 0.85, start_temperature= 100)
best_chip = irra_irra.run()

# 3) we check the final costs
print("Total wire cost:", best_chip.calc_total_grid_cost())
print(f"Intersections are at: {best_chip.get_intersection_coords()}")

# 4) show and save the grid
base_save_name = f"chip_{chip_id}_net_{net_id}"
plot_save_name = "layout_" + base_save_name
csv_save_name = "output_" + base_save_name

best_chip.show_grid(plot_save_name, "A*")
best_chip.save_output(csv_save_name)