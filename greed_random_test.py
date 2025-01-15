# main.py (or any script you prefer)
from classes.chip import Chip
from algorithms import greed as gr

# 1) we initialize the chip
base_data_path = r"data/"
chip0 = Chip(base_data_path, chip_id=2, net_id=9, output_folder="output")

# 2) we use the algo with offset
greedy = gr.Greed_random(chip0, 20, True, True)
greedy.run()

# 3) we check the final costs
print("Total wire cost:", chip0.calc_total_grid_cost())

# 4) show and save the grid
chip0.show_grid("final_layout.html")
chip0.save_output("final_output.csv")