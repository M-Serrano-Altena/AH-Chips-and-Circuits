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

        # 2D array where 0 is empty, 1 is wire and 2 is gate location
        self.grid = np.zeros(self.grid_size, dtype=int)
        for coords in self.gates.values():
            matrix_coords = convert_to_matrix_coords(coords, grid_size_y)
            self.grid[matrix_coords] = 2

        print(self.grid)


    def show_grid(self, save_filename: str|None = None):
        cmap = plt.cm.colors.ListedColormap(['white', 'blue', 'red'])
        bounds = [0, 0.5, 1.5, 2.5]  # Boundaries for the colors
        norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)
        plt.imshow(self.grid, cmap=cmap, norm=norm, zorder=1)
        plt.grid(visible=True, color="k", linestyle="-", zorder=0)


        if save_filename is not None:
            save_filename = add_missing_extension(save_filename, ".png")
            print(save_filename)
            plt.savefig(save_filename)

        plt.show()


chips = Chips(r"gates&netlists/chip_0/print_0.csv")

# for testing
sub_optimal_wire_coords = [
    (1, 2), (1, 3), (1, 4), (1, 5),
    (2, 6),
    (2, 5),
    (3, 5), (4, 5),
    (4, 7), (5, 7),
    (5, 6), (5, 5), (5,4),
    (6, 3), (6, 2), (6,1), (6, 0),
    (5, 0), (4, 0), (3,0),
    (3, 1), (3, 2), (3,3), (3,4),
    (2, 3), (2,2), (2,1),
]

for coords in sub_optimal_wire_coords:
    if chips.grid[coords] == 0:
        chips.grid[coords] = 1

chips.show_grid("test")