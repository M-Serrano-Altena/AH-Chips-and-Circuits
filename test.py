import os

base_path = r"gates&netlists/chip_0/"
filepath_print = os.path.join(base_path, "print_0.csv")
filepath_netlist = os.path.join(base_path, "netlist_1.csv")

print(int(os.path.dirname(filepath_print)[-1]))

print(int(os.path.splitext(filepath_netlist)[0][-1]))