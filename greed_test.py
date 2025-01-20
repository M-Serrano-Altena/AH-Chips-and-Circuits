# main.py (or any script you prefer)
from src.classes.chip import Chip
from src.algorithms.greed import Greed as gr
from sys import argv

chip_id = 0
net_id = 1

if len(argv) >= 2:
    chip_id = argv[1]

if len(argv) == 3:
    net_id = argv[2]

# 1) we initialize the chip
base_data_path = r"data/"
chip = Chip(base_data_path, chip_id=chip_id, net_id= net_id, output_folder="output", padding=1)

# 2) we use the algo with offset
greedy = gr(chip, 50, True, True)
greedy.run()
# chip = greedy.run_random_netlist_orders(iterations=1000)

# 3) we check the final costs
print("Total wire cost:", chip.calc_total_grid_cost())

# 4) show and save the grid
chip.show_grid("final_layout.html", "Greed")
chip.save_output("final_output.csv")
