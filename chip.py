import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from wire import Wire

os.chdir(os.path.dirname(__file__))

def add_missing_extension(filename: str, extension: str):
    base, existing_extension = os.path.splitext(filename)
    if not existing_extension:
        filename = filename + extension

    return filename

def convert_to_matrix_coords(coords, matrix_y_size):
    """
    Converts axis coords representation to matrix coords representation
    (in a matrix 0 is the top row as opposed to the bottom position for y)


    Args:
        coords (tuple): coordinates in axis representation
        matrix_y_size (int): the amount of rows the matrix has

    Returns:
        tuple: the matrix coordinates corresponding to the axis coordinates
    """
    x_coord, y_coord = coords
    return matrix_y_size - 1 - y_coord, x_coord

# Load data
class Chip:
    def __init__(self, filepath_print, filepath_netlist):
        self.gates = pd.read_csv(filepath_print)
        self.gates = self.gates.set_index("chip").to_dict(orient='split')

        # dict with gate number as key, and coords as values
        self.gates: dict[int, tuple[int, int]] = {
            chip_num: tuple(coords) for chip_num, coords in zip(self.gates["index"], self.gates["data"])
        }

        grid_size_x = max(coords[0] for coords in self.gates.values()) + 2
        grid_size_y = max(coords[1] for coords in self.gates.values()) + 2
        self.grid_size = grid_size_y, grid_size_x

        # 2D array where 0 is empty, 1 is a wire and 2 is a gate location
        self.grid = np.zeros(self.grid_size, dtype=int)
        for coords in self.gates.values():
            matrix_coords = convert_to_matrix_coords(coords, grid_size_y)
            self.grid[matrix_coords] = 2

        self.wires: list[Wire] = []

        self.netlist = pd.read_csv(filepath_netlist).to_dict(orient="records")
        self.netlist = [{list(dicts.values())[0]: list(dicts.values())[1]} for dicts in self.netlist]
        netlist_reverse = [{value: key for key, value in dicts.items()} for dicts in self.netlist]
        self.netlist_double_sided = self.netlist + netlist_reverse


    def add_wire(self, wire_coord_list) -> None:
        wire = Wire(wire_coord_list[0], wire_coord_list[-1])
        wire.extend_coords(wire_coord_list)
        self.wires.append(wire)

    def add_wires(self, wires_coord_list) -> None:
        for wire_coord_list in wires_coord_list:
            self.add_wire(wire_coord_list)


    def get_intersection_coords(self):
        gate_coords = set(convert_to_matrix_coords(coords, matrix_y_size=self.grid_size[0]) for coords in self.gates.values())
        wires_coords_set = [set(wire.coords) for wire in self.wires]
        shared_coords = set()
        for wire1 in wires_coords_set:
            for wire2 in wires_coords_set:
                if wire1 == wire2:
                    continue

                shared_coords |= wire1 & wire2

        # exclude shared coords that correspond to gates
        shared_coords -= gate_coords
        return shared_coords

    def get_wire_intersect_amount(self):
        return len(self.get_intersection_coords())
    
    
    @staticmethod
    def wires_in_collision(wire1, wire2):
        for i in range(wire1.length - 1):
            for j in range(wire2.length - 1):
                wire1_coords1 = wire1.coords[i]
                wire1_coords2 = wire1.coords[i + 1]

                wire2_coords1 = wire2.coords[j]
                wire2_coords2 = wire2.coords[j + 1]

                # checks if subsequent coordinates in both wires are the same
                if wire1_coords1 == wire2_coords1 and wire1_coords2 == wire2_coords2:
                    return True
                elif wire1_coords2 == wire2_coords1 and wire1_coords1 == wire2_coords2:
                    return True
                
        return False

    
    def grid_has_wire_collision(self):
        for i, wire1 in enumerate(self.wires):
            for j, wire2 in enumerate(self.wires):
                if i == j:
                    continue

                if self.wires_in_collision(wire1, wire2):
                    return True
                
        return False
                


    def show_grid(self, save_filename: str|None = None):
        fig, ax = plt.subplots(figsize=(6, 6))

        plt.xlim(-0.5, self.grid_size[1] - 0.5)
        plt.ylim(-0.5, self.grid_size[0] - 0.5)

        plt.grid(visible=True, color="k", linestyle="-")
        ax.invert_yaxis()  # To match matrix-style coordinates

        # Plot the chips
        for chip, coords in self.gates.items():
            matrix_coords = convert_to_matrix_coords(coords, matrix_y_size=self.grid_size[0])
            y_coords, x_coords = matrix_coords
            plt.scatter(x_coords, y_coords, color="red", s=500, label=f"Chip {chip}")
            plt.text(x_coords, y_coords, str(chip), color="white", ha="center", va="center", fontsize=13)

        # Plot the wires
        for wire in self.wires:
            # Unzip the wire path into rows and columns
            rows, cols = zip(*wire.coords)
            plt.plot(cols, rows, color="blue", linewidth=5)

        if save_filename is not None:
            save_filename = add_missing_extension(save_filename, ".png")
            print(save_filename)
            plt.savefig(save_filename)

        plt.show()


base_path = r"gates&netlists/chip_0/"
filepath_print = os.path.join(base_path, "print_0.csv")
filepath_netlist = os.path.join(base_path, "netlist_1.csv")

chips = Chip(filepath_print, filepath_netlist)

# for testing (wire = from gate to gate)
sub_optimal_wires = [
    [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6)],
    [(1, 6), (2, 6), (2, 5), (3, 5), (4, 5), (4, 6)],
    [(4, 6), (4, 7), (5, 7), (5, 6), (5, 5), (5, 4), (5, 3)],
    [(5, 3), (6, 3), (6, 2), (6, 1), (6, 0), (5, 0), (4, 0), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (2, 4)],
    [(2, 4), (2, 3), (2, 2), (2, 1), (1, 1)]
]

intersection_wires = [
    [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6)],
    [(1, 6), (2, 6), (2, 5), (2, 4)],
    [(2, 4), (1, 4), (0, 4), (0, 3), (1, 3), (2, 3), (3, 3), (3, 3), (4, 3), (5, 3)],
]

collision_wires = [
    [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6)],
    [(1, 6), (2, 6), (2, 5), (2, 4)],
    [(2, 4), (1, 4), (0, 4), (0, 3), (1, 3), (2, 3), (3, 3), (3, 3), (4, 3), (5, 3)],
    [(5, 3), (4, 3), (4, 4), (4, 5), (4, 6)]
]

chips.add_wires(collision_wires)

print(chips.grid_has_wire_collision())
print(chips.get_intersection_coords())

chips.show_grid("test")