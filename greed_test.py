# main.py (or any script you prefer)
from classes.chip import Chip
from algorithms.greed import greed_algo

# 1) we initialize the chip
base_data_path = r"data/"
chip0 = Chip(base_data_path, chip_id=0, net_id=3, output_folder="output")

# 2) we use the algo with offset
greed_algo(chip0, max_offset=10, allow_short_circuit=False, sort_wires= True)

# 3) we check the final costs
print("Total wire cost:", chip0.calc_total_wire_cost())

# 4) show and save the grid
chip0.show_grid("final_layout.html")
chip0.save_output("final_output.csv")
