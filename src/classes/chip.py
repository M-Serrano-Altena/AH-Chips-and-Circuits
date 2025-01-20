import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly.io as pio
import pandas as pd
import os
from src.classes.wire import Wire
from src.classes.occupancy import Occupancy
from src.algorithms.utils import cost_function, Coords_3D, manhattan_distance
from functools import lru_cache

def add_missing_extension(filename: str, extension: str):
    """Add an extension to a filename if the extension is missing"""
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

class Chip:
    def __init__(self, base_data_path, chip_id, net_id, padding: int=1, output_folder="output/"):
        self.chip_id = chip_id
        self.net_id = net_id
        self.output_folder = output_folder
        self.padding = padding

        self.all_offset_combos = np.array([
            [1, 0, 0], [-1, 0, 0],
            [0, 1, 0], [0, -1, 0],
            [0, 0, 1], [0, 0, -1]
        ], dtype=int)

        chip_path = os.path.join(base_data_path, f"chip_{self.chip_id}")
        filepath_print = os.path.join(chip_path, f"print_{self.chip_id}.csv")
        filepath_netlist = os.path.join(chip_path, f"netlist_{self.net_id}.csv")

        self.gates = pd.read_csv(filepath_print)
        self.gates = self.gates.set_index("chip").to_dict(orient='split')

        # dict with gate number as key, and coords as values
        self.gates: dict[int, Coords_3D] = {
            gate_id: tuple(coords) + (0,) for gate_id, coords in zip(self.gates["index"], self.gates["data"])
        }

        self.coords_to_gate_map = {coords: gate_id for gate_id, coords in self.gates.items()}
        self.gate_coords = set(self.gates.values())

        # grid size
        self.grid_range_x = (-padding + 1, max(coords[0] for coords in self.gates.values()) + padding)
        self.grid_range_y = (-padding + 1, max(coords[1] for coords in self.gates.values()) + padding)
        self.grid_range_z = (0, 7)
        self.grid_shape = (self.grid_range_x[1] - self.grid_range_x[0], self.grid_range_y[1] - self.grid_range_y[0], self.grid_range_z[1] - self.grid_range_z[0])

        # initate occupancy grid self.occupancy[x][y][z] is empty set for free item
        self.occupancy =  Occupancy()
        
        # we add the coordinates of the gates as identifiers in grid
        self.occupancy.add_gates(self.gate_coords)
        self.wires: list[Wire] = []

        # read netlist
        self.netlist = pd.read_csv(filepath_netlist).to_dict(orient="records")
        self.netlist: list[dict[int, int]] = [{list(dicts.values())[0]: list(dicts.values())[1]} for dicts in self.netlist]

        # sort netlist by ascending manhattan distance
        self.netlist = list(
            sorted(
                self.netlist, key=lambda connection: 
                manhattan_distance(self.gates[list(connection.keys())[0]], self.gates[list(connection.values())[0]])
            )
        )

        self.manhatten_distance_sum = sum(manhattan_distance(self.gates[list(connection.keys())[0]], self.gates[list(connection.values())[0]]) for connection in self.netlist)

        
        # reverse all netlist connections
        netlist_reverse = [{value: key for key, value in dicts.items()} for dicts in self.netlist]
        self.netlist_double_sided = self.netlist + netlist_reverse

        # initiate the wires with gate coords
        for connection in self.netlist:
            gate_1, gate_2 = list(connection.items())[0]
            gate_1_coords = self.gates[gate_1]
            gate_2_coords = self.gates[gate_2]

            wire_in_system = Wire(gate_1_coords, gate_2_coords)
            self.wires.append(wire_in_system)

    def add_entire_wire(self, wire_segment_list: list[Coords_3D]) -> None:
        """Create an entire wire from a wire segment list"""
        gate_1_coords = wire_segment_list[0]
        gate_2_coords = wire_segment_list[-1]
        wire_segment_list = wire_segment_list[1:-1]

        wire = Wire(gate_1_coords, gate_2_coords)
        wire.append_wire_segment_list(wire_segment_list)

        for i, existing_wire in enumerate(self.wires):
            if {existing_wire.coords_wire_segments[0], existing_wire.coords_wire_segments[-1]} == {gate_1_coords, gate_2_coords}:
                self.wires[i] = wire
                self.add_wire_to_occupancy(wire_segment_list, wire)
                return

    def add_entire_wires(self, list_all_wire_segments: list[list[Coords_3D]]) -> None:
        """Create multiple entire wires from a list of wire segments"""
        for wire_segment_list in list_all_wire_segments:
            self.add_entire_wire(wire_segment_list)

    def is_fully_connected(self) -> bool:
        for wire in self.wires:
            if not wire.is_wire_connected():
                return False

        return True
    
    def coord_within_boundaries(self, coord: Coords_3D) -> bool:
        return (self.grid_range_x[0] <= coord[0] <= self.grid_range_x[1] 
                and self.grid_range_y[0] <= coord[1] <= self.grid_range_y[1] 
                and self.grid_range_z[0] <= coord[2] <= self.grid_range_z[1])

    @lru_cache(maxsize=None) 
    def get_neighbours(self, coord: Coords_3D) -> list[Coords_3D]:
        """
        Return valid neighboring coordinates in 3D (±x, ±y, ±z), 
        ensuring we stay within the grid boundaries.
        """
        coord_array = np.array(coord, dtype=int)
        all_neighbours = coord_array + self.all_offset_combos
        return [
            tuple(neighbour) for neighbour in all_neighbours
            if self.coord_within_boundaries(tuple(neighbour))
        ]
    

    def coord_occupied_by_gate(self, coord: Coords_3D, own_gates: set[Coords_3D]|None = None) -> bool:
        """
        Checks if 'coord' is occupied by any gate, except its own
        """
        # if coord is own_gate return false
        if own_gates and (coord in own_gates): 
            return False
        
        # if gate is in general gate coords, return true else false
        return coord in self.gate_coords
    
    def coord_is_occupied(self, coord: Coords_3D, own_gates: set[Coords_3D]|None = None) -> bool:
        """ 
        Checks if `coord` is already occupied by any wire or gate (except its own)
        """

        # return False if the coordinate is one of its own gates
        if own_gates and (coord in own_gates):
            return False
        
        coord_occupancy = self.get_coord_occupancy(coord)

        # return true if the coordinate is occupied, otherwise false
        return len(coord_occupancy) != 0 


    def get_intersection_coords(self) -> set[Coords_3D]:
        """Get the coordinates of all wire intersections"""

        wires_coords_set = [set(wire.coords_wire_segments) for wire in self.wires]
        shared_coords = set()

        for i in range(len(wires_coords_set)):
            for j in range(i):
                wire_segment_set_1 = wires_coords_set[i]
                wire_segment_set_2 = wires_coords_set[j]
                
                # add all wire segments that are shared between different wires
                shared_coords |= wire_segment_set_1 & wire_segment_set_2

        # exclude shared coords that correspond to gates
        shared_coords -= self.gate_coords
        return shared_coords

    def get_wire_intersect_amount(self) -> int:
        """
        Get the amount of intersections (2 wire segments crossing) between all wires.
        If 3 wires intersect at 1 point, it counts as 2 intersections.
        
        """
        wires_coords_set = [set(wire.coords_wire_segments) for wire in self.wires]
        intersection_coords = self.get_intersection_coords()
        intersection_counter = 0

        # check how many cables are involved in intersection
        for intersection_coord in intersection_coords:
            amount_of_intersections = sum(intersection_coord in wire_segment_set for wire_segment_set in wires_coords_set) - 1
            if amount_of_intersections > 0:
                intersection_counter += amount_of_intersections

        return intersection_counter
    
    
    @staticmethod
    def wires_in_collision(wire1: Wire, wire2: Wire):
        """
        Checks if a wire is in collision with another wire
        (2 wires occupying the same wire segment)
        """
        for i in range(wire1.length - 1):
            for j in range(wire2.length - 1):
                wire1_coords1 = wire1.coords_wire_segments[i]
                wire1_coords2 = wire1.coords_wire_segments[i + 1]

                wire2_coords1 = wire2.coords_wire_segments[j]
                wire2_coords2 = wire2.coords_wire_segments[j + 1]

                # checks if subsequent coordinates in both wires are the same
                if {wire1_coords1, wire1_coords2} == {wire2_coords1, wire2_coords2}:
                    return True
                
        return False
    
    def wire_segment_causes_collision(self, neighbour: Coords_3D, current: Coords_3D) -> bool:
        """Checks if wiresegment causes a collision in chip"""

        neighbour_occupancy = self.get_coord_occupancy(neighbour, exclude_gates=True)
        current_occupancy = self.get_coord_occupancy(current, exclude_gates=True)

        # if one of both is empty, we can never have wire collision
        if not neighbour_occupancy or not current_occupancy:
            return False

        shared_wire = neighbour_occupancy & current_occupancy
         
        # we have a wire collison if the coordinates in the wire class are subsequent and the wires match
        if shared_wire:
            for wire_piece in shared_wire:
                for i in range(len(wire_piece.coords_wire_segments) - 1):
                    if {current, neighbour} == {wire_piece.coords_wire_segments[i], wire_piece.coords_wire_segments[i + 1]}:
                        return True

        return False

    
    def get_grid_wire_collision(self, boolean_output=True) -> int|bool:
        """Checks if a grid has a collision between any wires"""
        collision_counter = 0

        for i in range(len(self.wires)):
            for j in range(i):
                wire1 = self.wires[i]
                wire2 = self.wires[j]
                if i == j:
                    continue

                if self.wires_in_collision(wire1, wire2):
                    if boolean_output:
                        return True
                        
                    collision_counter += 1
        
        if boolean_output:
            return False
        
        return collision_counter
    
    def add_gate_to_occupancy(self, gate_coords: Coords_3D) -> None:
        self.occupancy.add_gate(gate_coords)
    
    def add_wire_segment_to_occupancy(self, coord: Coords_3D, wire: Wire) -> None:
        self.occupancy.add_wire_segment(coord, wire)

    def add_wire_to_occupancy(self, wire_segment_list: list[Coords_3D], wire: Wire) -> None:
        self.occupancy.add_wire(wire_segment_list, wire)

    def get_coord_occupancy(self, coords: Coords_3D, exclude_gates: bool=False) -> set[Wire, str]:
        return self.occupancy.get_coord_occupancy(coords, exclude_gates)
                

    def calc_total_grid_cost(self) -> int:
        """Calculate the total wire cost of a given grid configuration"""
        tot_wire_length = sum(wire.length for wire in self.wires)
        intersection_amount = self.get_wire_intersect_amount()
        collision_amount = self.get_grid_wire_collision()
        return cost_function(wire_length=tot_wire_length, intersect_amount=intersection_amount, collision_amount=collision_amount)


    def show_grid(self, image_filename: str|None = None) -> None:
        """Show (and save) a 3D interactive plot of a given grid configuration"""
        total_cost = self.calc_total_grid_cost()
        intersect_amount = self.get_wire_intersect_amount()
        collision_amount = self.get_grid_wire_collision(boolean_output=False)
        camera_eye = dict(x=-1.3, y=-1.3, z=0.6)

        gates_x, gates_y, gates_z = zip(*self.gates.values())
        gates_plot = go.Scatter3d(x=gates_x, y=gates_y, z=gates_z, mode='markers', marker=dict(color='red', size=8), text=list(self.gates.keys()), textposition='top center', textfont=dict(size=100, color='black'), hovertemplate='Gate %{text}: (%{x}, %{y}, %{z})<extra></extra>', name='Gates')
        data = [gates_plot]

        # Plot the wires
        for i, wire in enumerate(self.wires):
            gate_1_coords = wire.coords_wire_segments[0]
            gate_2_coords = wire.coords_wire_segments[-1]

            gate_1_id = self.coords_to_gate_map[gate_1_coords]
            gate_2_id = self.coords_to_gate_map[gate_2_coords]

            wire_x, wire_y, wire_z = zip(*wire.coords_wire_segments)
            wire_plot = go.Scatter3d(x=wire_x, y=wire_y, z=wire_z, mode='lines', line=dict(width=3), name='Wires', showlegend=i == 0, hovertemplate=f'Wire {gate_1_id} -> {gate_2_id}: ' + '(%{x}, %{y}, %{z})<extra></extra>')
            data.append(wire_plot)

        fig = go.Figure(data=data)

        fig.update_layout(
            scene=dict(
            xaxis = dict(title='X Axis', range=[self.grid_range_x[0], self.grid_range_x[1]]),
            yaxis = dict(title='Y Axis', range=[self.grid_range_y[0], self.grid_range_y[1]]),
            zaxis = dict(title='Z Axis', range=[-0.5 + self.grid_range_z[0], self.grid_range_z[1]]),
                aspectmode='cube',
                camera=dict(
                    eye=camera_eye,  # Adjust the camera position
                    center=dict(x=0, y=0, z=0),
                    up=dict(x=0, y=0, z=1),  # Up the camera view
                ),
            ),
            title=f"Chip {self.chip_id}, Net {self.net_id} (Cost = {total_cost}, Intersect Amount = {intersect_amount}, Collision Amount = {collision_amount}, Fully Connected: {self.is_fully_connected()})"
        )

        config = {
            'modeBarButtonsToRemove': ['orbitRotation', 'resetCameraDefault'],
            'displaylogo': False,
            'scrollZoom': True,
        }

        # Show the plot
        fig.show()

        # save the file as an html file
        if image_filename is not None:
            image_filename = add_missing_extension(image_filename, ".html")
            image_filepath = os.path.join(self.output_folder, "img", image_filename)
            pio.write_html(fig, file=image_filepath, config=config)



    def save_output(self, output_filename="output") -> None:
        """Save a given grid configuration as a csv file"""
        netlist_tuple = [(gate1, gate2) for net_connection in self.netlist for gate1, gate2 in net_connection.items()]
        wire_list = [wire.coords_wire_segments for wire in self.wires]

        # put netlist and wire sequences in a pandas dataframe
        output_df = pd.DataFrame({"net": pd.Series(netlist_tuple), "wires": pd.Series(wire_list)})
        
        # add footer row
        files_used = f"chip_{self.chip_id}_net_{self.net_id}"
        total_cost = self.calc_total_grid_cost()

        output_df.loc[len(output_df)] = [files_used, total_cost]

        output_filename = add_missing_extension(output_filename, ".csv")
        output_filepath = os.path.join(self.output_folder, "csv", output_filename)

        # remove whitespace for check50
        output_df = output_df.map(lambda x: str(x).replace(" ", ""))
        print(output_df)

        # convert pandas dataframe to csv file
        output_df.to_csv(output_filepath, index=False)
