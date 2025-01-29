from src.algorithms.utils import Coords_3D
from typing import TYPE_CHECKING, Iterable, Union
from collections import defaultdict

if TYPE_CHECKING:
    from src.classes.wire import Wire

class Occupancy:
    """
    Class to manage occupancy of 3D coordinates by wire segments and gates.
    Tracks which wires occupy specific coordinates and provides functionality
    for adding, removing, and getting occupancy.

    Attributes:
        occupancy (defaultdict): A mapping of coordinates to a set of wires and gates occupying those coordinates.
        occupancy_without_gates (defaultdict): A mapping of coordinates to a set of wires occupying those coordinates, excluding gates.
    """
    def __init__(self) -> None:
        """
        Initializes the Occupancy instance with empty default dictionaries
        for occupancy with and without gates.
        """

        # default dict avoids overhead of creating an empty set each time
        self.occupancy: defaultdict[Coords_3D, set[str|'Wire']] = defaultdict(set)
        self.occupancy_without_gates: defaultdict[Coords_3D, set['Wire']] = defaultdict(set)

    def __repr__(self) -> str:
        """
        Returns a string representation of the Occupancy instance.
        
        Returns:
            str: A string representation of the occupancy dictionary.
        """
        return f"Occupancy({self.occupancy})"
    
    def reset(self) -> None:
        """
        Resets the occupancy information by clearing all stored data.
        """
        self.occupancy.clear()
        self.occupancy_without_gates.clear()
    
    def remove_from_occupancy(self, coord: Coords_3D, wire: 'Wire') -> None:
        """
        Removes a wire from the occupancy data for a given coordinate.
        If the coordinate is a gate, it does not remove the wire.

        Args:
            coord (Coords_3D): The 3D coordinates to remove the wire from.
            wire (Wire): The wire to remove from the occupancy.
        """
        if coord not in self.occupancy or not self.occupancy[coord]:
            return
        
        # we do not remove cordinates if gate coords
        if "GATE" in self.occupancy[coord]:
            return
        
        self.occupancy[coord].remove(wire)
        self.occupancy_without_gates[coord].remove(wire)

    def remove_wire_from_occupancy(self, wire: 'Wire') -> None:
        """
        Removes a wire from the occupancy data for all its segments.

        Args:
            wire (Wire): The wire to remove from all coordinates it occupies.
        """
        for coord in wire.coords_wire_segments:
            self.remove_from_occupancy(coord, wire)

    def add_wire_segment(self, coords: Coords_3D, wire: 'Wire') -> None:
        """
        Adds a wire segment to the occupancy data for a given coordinate.
        
        Args:
            coords (Coords_3D): The 3D coordinates where the wire segment is located.
            wire (Wire): The wire to add at the given coordinates.
        """
        self.occupancy[coords].add(wire)
        self.occupancy_without_gates[coords].add(wire)

    def add_wire(self, wire_segment_list: list[Coords_3D], wire: 'Wire') -> None:
        """
        Adds a wire consisting of multiple segments to the occupancy data.

        Args:
            wire_segment_list (list[Coords_3D]): A list of coordinates representing the wire segments.
            wire (Wire): The wire to add.
        """
        for wire_segment in wire_segment_list:
            self.add_wire_segment(wire_segment, wire=wire)
    
    def add_gate(self, coords: Coords_3D) -> None:
        """
        Adds a gate at a specific coordinate.

        Args:
            coords (Coords_3D): The 3D coordinates where the gate should be added.
        """
        self.occupancy[coords].add("GATE")

    def add_gates(self, all_gate_coords: Iterable[Coords_3D]) -> None:
        """
        Adds multiple gates at the specified coordinates.

        Args:
            all_gate_coords (Iterable[Coords_3D]): An iterable of coordinates where gates should be added.
        """
        for gate_coords in all_gate_coords:
            self.add_gate(gate_coords)

    def get_coord_occupancy(self, coords: Coords_3D, exclude_gates: bool=False) -> set[str, 'Wire']:
        """
        Retrieves the set of occupiers for a specific coordinate, optionally excluding gates.

        Args:
            coords (Coords_3D): The 3D coordinates to query.
            exclude_gates (bool, optional): Whether to exclude gates from the result. Defaults to False.

        Returns:
            set[str | 'Wire']: A set of strings (for a gate) and wires occupying the given coordinates.
        """
        if exclude_gates:
            return self.occupancy_without_gates[coords]
        
        return self.occupancy[coords]
