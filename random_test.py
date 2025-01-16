# main.py (or any script you prefer)
from src.classes.chip import Chip
from src.algorithms import random_algo as ra

# 1) we initialize the chip
base_data_path = r"data/"
chip0 = Chip(base_data_path, chip_id=0, net_id=1, output_folder="output")

# 2) we use the algo with offset
random_random = ra.Random_random(chip0, 15, True, True)
random_random.run()

# 3) we check the final costs
print("Total wire cost:", chip0.calc_total_grid_cost())

# 4) show and save the grid
chip0.show_grid("final_layout.html")
chip0.save_output("final_output.csv")