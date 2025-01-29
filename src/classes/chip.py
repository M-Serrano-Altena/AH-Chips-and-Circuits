import numpy as np
import plotly.graph_objs as go
import plotly.io as pio
import pandas as pd
import os
from src.classes.wire import Wire
from src.classes.occupancy import Occupancy
from src.algorithms.utils import cost_function, Coords_3D, manhattan_distance, add_missing_extension, clean_np_int64
from functools import lru_cache
import itertools

class Chip:
    """
    A class representing a chip with gates and wire connections, managing the layout of gates and wiring within a 3D grid.

    Attributes:
        chip_id (int): The unique identifier for the chip.
        net_id (int): The unique identifier for the netlist.
        output_folder (str): The folder path where results are saved.
        padding (int): The padding used for grid boundaries.
        all_offset_combos (np.ndarray): The possible offsets for neighboring coordinates.
        gates (dict): A dictionary mapping gate IDs to 3D coordinates.
        coords_to_gate_map (dict): A dictionary mapping 3D coordinates to gate IDs.
        gate_coords (set): A set of all gate coordinates.
        occupancy (Occupancy): The occupancy grid for the chip, tracking wire and gate placements.
        wires (list): A list of Wire objects representing the wires on the chip.
        netlist (list): A list of net connections between gates.
        manhatten_distance_sum (int): The sum of Manhattan distances between connected gates in the netlist.
        grid_range_x (tuple): The x-coordinate range for the grid.
        grid_range_y (tuple): The y-coordinate range for the grid.
        grid_range_z (tuple): The z-coordinate range for the grid.
        grid_shape (tuple): The shape of the grid based on the x, y, and z ranges.
    """
    def __init__(self, base_data_path: str=r"data/", chip_id: int=0, net_id: int=1, padding: int=1, output_folder="results/latest"):
        """
        Initializes a Chip object with the given parameters and sets up its grid and wire connections.

        Args:
            base_data_path (str): The base path where chip data is stored.
            chip_id (int): The chip ID for the specific chip being initialized.
            net_id (int): The net ID for the chip's netlist.
            padding (int): The padding used to define the grid boundaries.
            output_folder (str): The folder where the results will be saved.
        """
        
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

        self.set_grid_size(padding)

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

        # initiate the wires with gate coords
        for connection in self.netlist:
            gate_1, gate_2 = list(connection.items())[0]
            gate_1_coords = self.gates[gate_1]
            gate_2_coords = self.gates[gate_2]

            wire_in_system = Wire(gate_1_coords, gate_2_coords)
            self.wires.append(wire_in_system)

    def set_grid_size(self, padding: int):
        self.grid_range_x = (-padding + 1, max(coords[0] for coords in self.gates.values()) + padding)
        self.grid_range_y = (-padding + 1, max(coords[1] for coords in self.gates.values()) + padding)
        self.grid_range_z = (0, 7)
        self.grid_shape = (self.grid_range_x[1] - self.grid_range_x[0], self.grid_range_y[1] - self.grid_range_y[0], self.grid_range_z[1] - self.grid_range_z[0])


    @property
    def wire_segment_list(self) -> list[list[Coords_3D]]:
        """
        Returns a list of wire segments for all the wires in the chip.

        Returns:
            list[list[Coords_3D]]: A list of wire segment coordinates for each wire.
        """
        return [wire.coords_wire_segments for wire in self.wires]

    def add_entire_wire(self, wire_segment_list: list[Coords_3D]) -> None:
        """
        Creates a complete wire from a list of wire segments and adds it to the chip.

        Args:
            wire_segment_list (list[Coords_3D]): The list of coordinates that form the wire's segments.
        """
        gate_1_coords = wire_segment_list[0]
        gate_2_coords = wire_segment_list[-1]
        wire_segment_list = wire_segment_list[1:-1]

        wire = Wire(gate_1_coords, gate_2_coords)
        wire.append_wire_segment_list(wire_segment_list)

        for i, existing_wire in enumerate(self.wires):
            if {existing_wire.coords_wire_segments[0], existing_wire.coords_wire_segments[-1]} == {gate_1_coords, gate_2_coords}:
                self.wires[i] = wire
                self.add_wire_segment_list_to_occupancy(wire_segment_list, wire)
                return

    def add_entire_wires(self, list_all_wire_segments: list[list[Coords_3D]]) -> None:
        """
        Creates multiple complete wires from a list of wire segments.

        Args:
            list_all_wire_segments (list[list[Coords_3D]]): A list of wire segment lists to create the wires.
        """
        for wire_segment_list in list_all_wire_segments:
            self.add_entire_wire(wire_segment_list)

    def reset_wire(self, wire: Wire) -> None:
        """
        Resets a given wire by removing it from the occupancy grid and resetting the wire object.

        Args:
            wire (Wire): The wire object to be reset.
        """
        self.remove_wire_from_occupancy(wire)
        wire.reset()

    def reset_wires(self, wire_list: list[Wire]) -> None:
        """
        Resets a list of wires by removing them from the occupancy grid and resetting each wire.

        Args:
            wire_list (list[Wire]): A list of Wire objects to be reset.
        """
        for wire in wire_list:
            self.reset_wire(wire)

    def reset_all_wires(self) -> None:
        """
        Resets all wires by removing them from the occupancy grid and resetting each wire.
        """
        for wire in self.wires:
            self.reset_wire(wire)

    def is_fully_connected(self) -> bool:
        """
        Checks if all wires in the chip are fully connected.

        Returns:
            bool: True if all wires are fully connected, False otherwise.
        """
        for wire in self.wires:
            if not wire.is_wire_connected():
                return False

        return True
    
    def coord_within_boundaries(self, coord: Coords_3D) -> bool:
        """
        Checks if a given coordinate is within the chip's grid boundaries.

        Args:
            coord (Coords_3D): The 3D coordinate to be checked.

        Returns:
            bool: True if the coordinate is within the boundaries, False otherwise.
        """
        return (self.grid_range_x[0] <= coord[0] <= self.grid_range_x[1] 
                and self.grid_range_y[0] <= coord[1] <= self.grid_range_y[1] 
                and self.grid_range_z[0] <= coord[2] <= self.grid_range_z[1])

    @lru_cache(maxsize=None) 
    def get_neighbours(self, coord: Coords_3D) -> list[Coords_3D]:
        """
        Returns the valid neighboring coordinates (±x, ±y, ±z) of a given coordinate within the grid.

        Args:
            coord (Coords_3D): The coordinate for which to find neighbors.

        Returns:
            list[Coords_3D]: A list of valid neighboring coordinates.
        """
        coord_array = np.array(coord, dtype=int)
        all_neighbours = coord_array + self.all_offset_combos
        return [
            tuple(neighbour) for neighbour in all_neighbours
            if self.coord_within_boundaries(tuple(neighbour))
        ]
    

    def coord_occupied_by_gate(self, coord: Coords_3D, own_gates: set[Coords_3D]|None = None) -> bool:
        """
        Checks if a given coordinate is occupied by any gate, except for the provided own gates.

        Args:
            coord (Coords_3D): The coordinate to check.
            own_gates (set[Coords_3D] | None): A set of gate coordinates to be excluded from the check.

        Returns:
            bool: True if the coordinate is occupied by a gate, False otherwise.
        """
        # if coord is own_gate return false
        if own_gates and (coord in own_gates): 
            return False
        
        # if gate is in general gate coords, return true else false
        return coord in self.gate_coords
    
    def coord_is_occupied(self, coord: Coords_3D, own_gates: set[Coords_3D]|None = None) -> bool:
        """
        Checks if a coordinate is occupied by any wire or gate (except for the provided own gates).

        Args:
            coord (Coords_3D): The coordinate to check.
            own_gates (set[Coords_3D] | None): A set of gate coordinates to be excluded from the check.

        Returns:
            bool: True if the coordinate is occupied, False otherwise.
        """

        # return False if the coordinate is one of its own gates
        if own_gates and coord in own_gates:
            return False
        
        coord_occupancy = self.get_coord_occupancy(coord)

        # return true if the coordinate is occupied, otherwise false
        return len(coord_occupancy) != 0 


    def get_intersection_coords(self) -> set[Coords_3D]:
        """
        Returns the coordinates of all wire intersections where two or more wires overlap.

        Returns:
            set[Coords_3D]: A set of coordinates where wire intersections occur.
        """

        occupancy = self.occupancy.occupancy
        output = set()

        for coordinates in occupancy.keys():
            occupancy_set = occupancy[coordinates]
            
            # we will never have an intersection at a gate
            if "GATE" in occupancy_set:
                continue

            # if the set is larger than 1, we have multiple wiring in coordinates thus intersection    
            if len(occupancy_set) > 1:
                output.add(coordinates)
        
        return output


    def get_wire_intersect_amount(self) -> int:
        """
        Get the amount of intersections (2 wire segments crossing) between all wires.
        If 3 wires intersect at 1 point, it counts as 2 intersections.
        
        Returns:
            int: The total number of wire intersections.
        """
        
        occupancy = self.occupancy.occupancy
        intersection_counter = 0

        for intersection_coords in self.get_intersection_coords():

            occupancy_set = occupancy[intersection_coords]

            # if more than two coordinates in set we have 3 wires intersecting
            if len(occupancy_set) > 2:
                intersection_counter += 2

            # otherwise we have 2 wires intersecting
            else:
                intersection_counter += 1
                
        return intersection_counter
    
    @staticmethod
    def wires_in_collision(wire1: Wire, wire2: Wire):
        """
        Checks if two wires are in collision (i.e., if they occupy the same wire segment).

        Args:
            wire1 (Wire): The first wire to check.
            wire2 (Wire): The second wire to check.

        Returns:
            bool: True if the wires are in collision, False otherwise.
        """
        # condition so that coordinate order of segment is consistent
        wire1_segments_set: set[tuple[Coords_3D, Coords_3D]] = {
            (wire1.coords_wire_segments[i], wire1.coords_wire_segments[i + 1])
            if wire1.coords_wire_segments[i] < wire1.coords_wire_segments[i + 1]
            else (wire1.coords_wire_segments[i + 1], wire1.coords_wire_segments[i])
            for i in range(wire1.length - 1)
        }

        wire2_segments_set: set[tuple[Coords_3D, Coords_3D]] = {
            (wire2.coords_wire_segments[i], wire2.coords_wire_segments[i + 1])
            if wire2.coords_wire_segments[i] < wire2.coords_wire_segments[i + 1]
            else (wire2.coords_wire_segments[i + 1], wire2.coords_wire_segments[i])
            for i in range(wire2.length - 1)
        }
        
        # True if set intersection, False if no intersection
        # .isdisjoint is efficient because it stops as soon as it finds an overlapping segment
        return not wire1_segments_set.isdisjoint(wire2_segments_set)
    
    def wire_segment_causes_collision(self, neighbour: Coords_3D, current: Coords_3D) -> bool:
        """
        Checks if a wire segment between two coordinates causes a collision in the chip.

        Args:
            neighbour (Coords_3D): The neighboring coordinate of the wire segment.
            current (Coords_3D): The current coordinate of the wire segment.

        Returns:
            bool: True if the wire segment causes a collision, False otherwise.
        """

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
        """
        Checks if there are any collisions between wires on the grid.

        Args:
            boolean_output (bool): If True, returns a boolean indicating the presence of a collision; otherwise, returns the total count of collisions.

        Returns:
            int | bool: The number of collisions if `boolean_output` is False, or a boolean indicating the presence of a collision if True.
        """
        collision_counter = 0
        # only check intersecting wires
        intersection_coords = self.get_intersection_coords() # gate coords excluded
        all_intersecting_wires = [tuple(self.get_coord_occupancy(coord)) for coord in intersection_coords]

        for wires in all_intersecting_wires:
            for wire1, wire2 in itertools.combinations(wires, r=2):
                if self.wires_in_collision(wire1, wire2):
                    if boolean_output:
                        return True
                        
                    collision_counter += 1
        
        if boolean_output:
            return False
        
        return collision_counter
    
    def add_gate_to_occupancy(self, gate_coords: Coords_3D) -> None:
        """
        Adds a gate to the occupancy at the specified coordinates.

        Args:
            gate_coords (Coords_3D): The coordinates of the gate to be added.
        """
        self.occupancy.add_gate(gate_coords)
    
    def add_wire_segment_to_occupancy(self, coord: Coords_3D, wire: Wire) -> None:
        """
        Adds a wire segment to the occupancy at the specified coordinates.

        Args:
            coord (Coords_3D): The coordinate of the wire segment to be added.
            wire (Wire): The wire associated with the segment.
        """
        self.occupancy.add_wire_segment(coord, wire)

    def add_wire_segment_list_to_occupancy(self, wire_segment_list: list[Coords_3D], wire: Wire) -> None:
        """
        Adds a list of wire segments to the occupancy grid.

        Args:
            wire_segment_list (list[Coords_3D]): A list of wire segments to be added.
            wire (Wire): The wire associated with the segments.
        """
        self.occupancy.add_wire(wire_segment_list, wire)

    def get_coord_occupancy(self, coords: Coords_3D, exclude_gates: bool=False) -> set[Wire, str]:
        """
        Returns the occupancy at a given coordinate.

        Args:
            coords (Coords_3D): The coordinate for which to retrieve occupancy.
            exclude_gates (bool): If True, excludes gates from the occupancy check.
        """
        return self.occupancy.get_coord_occupancy(coords, exclude_gates)
    
    def remove_wire_from_occupancy(self, wire: Wire) -> None:
        """
        Removes a wire from the occupancy grid.

        Args:
            wire (Wire): The wire to be removed.
        """
        self.occupancy.remove_wire_from_occupancy(wire)
                
    def calc_total_grid_cost(self, ignore_collision_cost: bool=False) -> int:
        """
        Calculates the total cost of the grid configuration based on wire length, intersections, and collisions.

        Args:
            ignore_collision_cost (bool): If True, ignores the cost of wire collisions.

        Returns:
            int: The total cost of the grid configuration.
        """
        tot_wire_length = sum(wire.length for wire in self.wires)
        intersection_amount = self.get_wire_intersect_amount()
        if not ignore_collision_cost:
            collision_amount = self.get_grid_wire_collision()
        return cost_function(wire_length=tot_wire_length, intersect_amount=intersection_amount, collision_amount=collision_amount)


    def show_grid(self, image_filename: str|None=None, algorithm_name: str|None=None) -> None:
        """
        Visualizes the chip grid with gates and wires using Plotly.

        Args:
            image_filename (str, optional): The name of the image file to save the plot if a name is provided. Defaults to None.
            algorithm_name (str, optional): The name of the algorithm used for the plot title if provided. Defaults to None.
        """
        total_cost = self.calc_total_grid_cost()
        intersect_amount = self.get_wire_intersect_amount()
        collision_amount = self.get_grid_wire_collision(boolean_output=False)
        camera_eye = dict(x=-1.3, y=-1.3, z=0.6)
        title = (
            f"Chip {self.chip_id}, Net {self.net_id}"
            + (f" - {algorithm_name} " if algorithm_name is not None else " ")
            + f"(Cost = {total_cost}, Intersections = {intersect_amount}, Collisions = {collision_amount}, Fully Connected: {self.is_fully_connected()}, theoretical min = {self.manhatten_distance_sum})"
        )

        padding = 1 - min(component for wire in self.wires for coord in wire.coords_wire_segments for component in coord)
        self.set_grid_size(padding)

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
            title=title
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
            image_output_folder = os.path.join(self.output_folder, "chip_config_plots")
            image_filepath = os.path.join(image_output_folder, image_filename)
            os.makedirs(image_output_folder, exist_ok=True)
            pio.write_html(fig, file=image_filepath, config=config)



    def save_output(self, output_filename: str="output") -> None:
        """
        Saves the chip configuration to a CSV file with the wire segments and netlist connections.

        Args:
            output_filename (str): The name of the output file to save.
        """
        netlist_tuple = [(gate1, gate2) for net_connection in self.netlist for gate1, gate2 in net_connection.items()]

        # put netlist and wire sequences in a pandas dataframe
        output_df = pd.DataFrame({"net": pd.Series(netlist_tuple), "wires": pd.Series(self.wire_segment_list)})
        
        # add footer row
        files_used = f"chip_{self.chip_id}_net_{self.net_id}"
        total_cost = self.calc_total_grid_cost()

        output_df.loc[len(output_df)] = [files_used, total_cost]

        csv_output_folder = os.path.join(self.output_folder, "chip_config_csv")
        os.makedirs(csv_output_folder, exist_ok=True)

        output_filename = add_missing_extension(output_filename, ".csv")
        output_filepath = os.path.join(csv_output_folder, output_filename)

        # remove whitespace for check50
        output_df = output_df.map(lambda x: str(x).replace(" ", ""))
        print(output_df)

        # convert pandas dataframe to csv file
        output_df.to_csv(output_filepath, index=False)

        # remove any np.int64 around coordinates
        clean_np_int64(output_filepath)


def load_chip_from_csv(path_to_csv: str, padding: int=1) -> Chip:
    """
    Loads a chip configuration from a CSV file containing gate and wire data.

    Args:
        path_to_csv (str): The path to the CSV file containing the chip configuration.
        padding (int): The padding to use for grid boundaries.

    Returns:
        Chip: A Chip object with the configuration loaded from the CSV file.
    """
    from ast import literal_eval
    df = pd.read_csv(path_to_csv)
    chip_net_string = df["net"].iloc[-1]
    chip_id = int(chip_net_string[5])
    net_id = int(chip_net_string[-1])

    all_wire_segments_list: list[list[Coords_3D]] = [
        literal_eval(string_list) for string_list in df["wires"].tolist()
    ]
    all_wire_segments_list.pop()

    chip = Chip(chip_id=chip_id, net_id=net_id, padding=padding)
    chip.add_entire_wires(all_wire_segments_list)

    # make sure the padding isn't too small
    minimum_required_padding = 1 - min(component for wire in chip.wires for coord in wire.coords_wire_segments for component in coord)
    padding = max(padding, minimum_required_padding)
    chip.set_grid_size(padding)

    return chip