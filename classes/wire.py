from algorithms.utils import Coords_3D

class Wire():
    def __init__(self, gate1: Coords_3D, gate2: Coords_3D):
        self.gates = [gate1, gate2]
        self.coords: list[tuple] = [gate1, gate2]

    def __len__(self):
        return self.length

    @property
    def length(self):
        """gets the length of the wire"""
        return len(self.coords) - 1
    
    def is_circular(self) -> bool:
        """checks if the wire touches itself"""   
        # if this is the case we have duplicates in our coordinates, this a crossing
        return len(self.coords) != len(set(self.coords))
    
    @staticmethod
    def are_points_neighbours(coord1: Coords_3D, coord2: Coords_3D) -> bool:
        """Checks if points are next to each other in 3D space
        """
        return sum(abs(coord1[i] - coord2[i]) for i in range(len(coord1))) == 1
        
    def is_wire_connected(self) -> bool:
        """Checks is all wire segments are neighbours (and thus connected)"""
        for i in range(len(self.coords) - 1):
            if not self.are_points_neighbours(self.coords[i], self.coords[i + 1]):
                return False
               
        return True
    

    def append_wire_segment(self, coords: Coords_3D) -> None:
        """Adds a wire segment to a wire if it's a neighbour with one of the wire ends"""

        # don't add gate coords to the wire again
        if coords in self.gates:
            return

        if self.are_points_neighbours(coords, self.coords[-2]):
            self.coords.insert(-1, coords)
        
        elif self.are_points_neighbours(coords, self.coords[1]):
            self.coords.insert(1, coords)

        return
    
    def append_wire_segment_list(self, coords_list: list[Coords_3D]) -> None:
        """Add multiple wire segments to a wire"""
        for coords in coords_list:
            self.append_wire_segment(coords)