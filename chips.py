import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os

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
class Chips:
    def __init__(self, filepath_print):
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

        # a wire is a list of horizontal/vertical coordinates
        self.wires: list[list[tuple]] = []


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
            rows, cols = zip(*wire)
            plt.plot(cols, rows, color="blue", linewidth=5)

        if save_filename is not None:
            save_filename = add_missing_extension(save_filename, ".png")
            print(save_filename)
            plt.savefig(save_filename)

        plt.show()


chips = Chips(r"gates&netlists/chip_0/print_0.csv")

# for testing
sub_optimal_wires = [
    [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6)],
    [(1, 6), (2, 6)],
    [(2, 6), (2, 5)],
    [(2, 5), (3, 5), (4, 5)],
    [(4, 5), (4, 6), (4, 7)],
    [(4, 7), (5, 7)],
    [(5, 7), (5, 6), (5, 5), (5, 4), (5, 3)],
    [(5, 3), (6, 3), (6, 2), (6,1), (6, 0)],
    [(6, 0), (5, 0), (4, 0), (3,0)],
    [(3,0), (3, 1), (3, 2), (3,3), (3,4)],
    [(3,4), (2,4)],
    [(2,4), (2, 3), (2,2), (2,1)],
    [(2,1), (1,1)]
]

chips.wires = sub_optimal_wires

chips.show_grid("test")