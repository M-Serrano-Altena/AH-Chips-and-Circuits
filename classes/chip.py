import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly.io as pio
import pandas as pd
import os
from classes.wire import Wire
from algorithms.utils import cost_function


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
    def __init__(self, base_data_path, chip_id, net_id, output_folder="output/"):
        self.chip_id = chip_id
        self.net_id = net_id
        self.output_folder = output_folder

        chip_path = os.path.join(base_data_path, f"chip_{self.chip_id}")
        filepath_print = os.path.join(chip_path, f"print_{self.chip_id}.csv")
        filepath_netlist = os.path.join(chip_path, f"netlist_{self.net_id}.csv")

        self.gates = pd.read_csv(filepath_print)
        self.gates = self.gates.set_index("chip").to_dict(orient='split')

        # dict with gate number as key, and coords as values
        self.gates: dict[int, tuple[int, int, int]] = {
            chip_num: tuple(coords) + (0,) for chip_num, coords in zip(self.gates["index"], self.gates["data"])
        }

        self.grid_size_x = max(coords[0] for coords in self.gates.values()) + 2
        self.grid_size_y = max(coords[1] for coords in self.gates.values()) + 2
        self.grid_size_z = 8

        self.wires: list[Wire] = []

        self.netlist = pd.read_csv(filepath_netlist).to_dict(orient="records")
        self.netlist = [{list(dicts.values())[0]: list(dicts.values())[1]} for dicts in self.netlist]
        netlist_reverse = [{value: key for key, value in dicts.items()} for dicts in self.netlist]
        self.netlist_double_sided = self.netlist + netlist_reverse

        # we initiate in the first cordinates of the wires in the self.wires list 

        list_of_connections = [[key, value] for connection in self.netlist for (key, value) in connection.items()]

        for [gate_1, gate_2] in list_of_connections:
            gate_1_coords = self.gates[gate_1]
            gate_2_coords = self.gates[gate_2]

            wire_in_system = Wire(gate_1_coords, gate_2_coords)
            self.wires.append(wire_in_system)   


    def add_wire(self, wire_coord_list) -> None:
        wire = Wire(wire_coord_list[0], wire_coord_list[-1])
        wire.append_wire_segment_list(wire_coord_list)
        self.wires.append(wire)

    def add_wires(self, wires_coord_list) -> None:
        for wire_coord_list in wires_coord_list:
            self.add_wire(wire_coord_list)


    def get_intersection_coords(self):
        gate_coords = set(self.gates.values())
        wires_coords_set = [set(wire.coords) for wire in self.wires]
        shared_coords = set()
        # these are wire_segments right not wires?
        for wire_segment_set_1 in wires_coords_set:
            for wire_segment_set_2 in wires_coords_set:
                if wire_segment_set_1 == wire_segment_set_2:
                    continue
     
                shared_coords |= wire_segment_set_1 & wire_segment_set_2

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
                

    def calc_total_wire_cost(self) -> int:
        tot_wire_length = sum(wire.length for wire in self.wires)
        intersection_amount = self.get_wire_intersect_amount()
        return cost_function(wire_length=tot_wire_length, intersect_amount=intersection_amount)


    def show_grid(self, image_filename: str|None = None) -> None:
        camera_eye = dict(x=-1.3, y=-1.3, z=0.6)

        gates_x, gates_y, gates_z = zip(*self.gates.values())
        gates_plot = go.Scatter3d(x=gates_x, y=gates_y, z=gates_z, mode='markers', marker=dict(color='red', size=8), text=list(self.gates.keys()), textposition='top center', textfont=dict(size=100, color='black'), hovertemplate='Gate %{text}: (%{x}, %{y}, %{z})<extra></extra>', name='Gates')
        data = [gates_plot]

        # Plot the wires
        for i, wire in enumerate(self.wires):
            wire_x, wire_y, wire_z = zip(*wire.coords)
            wire_plot = go.Scatter3d(x=wire_x, y=wire_y, z=wire_z, mode='lines', line=dict(color='blue', width=3), name='Wires', showlegend=i == 0, hovertemplate=f'Wire {i + 1}: ' + '(%{x}, %{y}, %{z})<extra></extra>')
            data.append(wire_plot)

        fig = go.Figure(data=data)

        fig.update_layout(
            scene=dict(
            xaxis = dict(title='X Axis', range=[-0.5, self.grid_size_x - 1]),
            yaxis = dict(title='Y Axis', range=[-0.5, self.grid_size_y - 1]),
            zaxis = dict(title='Z Axis', range=[-0.5, self.grid_size_z - 1]),
                aspectmode='cube',
                camera=dict(
                    eye=camera_eye,  # Adjust the camera position
                    center=dict(x=0, y=0, z=0),
                    up=dict(x=0, y=0, z=1),  # Up the camera view
                ),
            ),
            title=f"Chip {self.chip_id}, Net {self.net_id}"
        )

        config = {
            'modeBarButtonsToRemove': ['orbitRotation', 'resetCameraDefault'],
            'displaylogo': False,
            'scrollZoom': True,
        }

        # Show the plot
        fig.show()

        if image_filename is not None:
            image_filename = add_missing_extension(image_filename, ".html")
            image_filepath = os.path.join(self.output_folder, "img", image_filename)

            pio.write_html(fig, file=image_filepath, config=config)



    def save_output(self, output_filename="output") -> None:
        netlist_tuple = [(gate1, gate2) for net_connection in self.netlist for gate1, gate2 in net_connection.items()]
        wire_list = [wire.coords for wire in self.wires]

        # put netlist and wire sequences in a pandas dataframe
        output_df = pd.DataFrame({"net": pd.Series(netlist_tuple), "wires": pd.Series(wire_list)})
        
        # add footer row
        files_used = f"chip_{self.chip_id}_net_{self.net_id}"
        total_cost = self.calc_total_wire_cost()

        output_df.loc[len(output_df)] = [files_used, total_cost]

        output_filename = add_missing_extension(output_filename, ".csv")
        output_filepath = os.path.join(self.output_folder, "csv", output_filename)

        # convert pandas dataframe to csv file
        output_df.to_csv(output_filepath, index=False) 