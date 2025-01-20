from src.algorithms.utils import Coords_3D
from typing import TYPE_CHECKING, Iterable, Union
from collections import defaultdict

if TYPE_CHECKING:
    from src.classes.wire import Wire

class Occupancy:
    def __init__(self):
        # default dict avoids overhead of creating an empty set each time
        self.occupancy: defaultdict[Coords_3D, set[str|'Wire']] = defaultdict(set)
        self._occupancy_without_gates: defaultdict[Coords_3D, set['Wire']] = defaultdict(set)

    def __repr__(self):
        return f"Occupancy({self.occupancy})"

    def add_wire_segment(self, coords: Coords_3D, wire: 'Wire') -> None:
        self.occupancy[coords].add(wire)
        self._occupancy_without_gates[coords].add(wire)

    def add_wire(self, wire_segment_list: list[Coords_3D], wire: 'Wire') -> None:
        for wire_segment in wire_segment_list:
            self.add_wire_segment(wire_segment, wire=wire)
    
    def add_gate(self, coords: Coords_3D) -> None:
        self.occupancy[coords].add("GATE")

    def add_gates(self, all_gate_coords: Iterable):
        for gate_coords in all_gate_coords:
            self.add_gate(gate_coords)

    def get_coord_occupancy(self, coords: Coords_3D, exclude_gates: bool=False) -> set[str, 'Wire']:
        if exclude_gates:
            return self._occupancy_without_gates[coords]
        
        return self.occupancy[coords]
    
