from src.algorithms.utils import Coords_3D
from typing import TYPE_CHECKING, Iterable, Union

if TYPE_CHECKING:
    from src.classes.wire import Wire

class Occupancy:
    def __init__(self):
        self.occupancy: dict[Coords_3D, set[str|'Wire']] = {}

    def __repr__(self):
        return f"Occupancy({self.occupancy})"
    
    def reset(self) -> None:
        self.occupancy.clear()

    def add_to_occupancy(self, coord: Coords_3D, addition: Union[str, 'Wire']) -> None:
        if coord in self.occupancy:
            self.occupancy[coord].add(addition)
            return
        
        self.occupancy[coord] = set([addition])
    
    def remove_from_occupancy(self, coord: Coords_3D, wire: 'Wire') -> None:
        if coord in self.occupancy:
            # we do not remove cordinates if GATE
            if "GATE" in self.occupancy[coord]:
                return
            self.occupancy[coord].remove(wire)
            return

    def add_wire_segment(self, coords: Coords_3D, wire: 'Wire') -> None:
        self.add_to_occupancy(coords, wire)
    
    def add_gate(self, gate_coords: Coords_3D) -> None:
        self.add_to_occupancy(gate_coords, "GATE")

    def add_gates(self, all_gate_coords: Iterable):
        for gate_coords in all_gate_coords:
            self.add_gate(gate_coords)

    def get_coord_occupancy(self, coords: Coords_3D, exclude_gates: bool=False) -> set[str, 'Wire']:
        coord_occupancy = self.occupancy.get(coords, set())
        if exclude_gates:
            return coord_occupancy - {"GATE"}
        
        return coord_occupancy
    
