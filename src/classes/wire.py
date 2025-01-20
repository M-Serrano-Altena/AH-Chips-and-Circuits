from src.algorithms.utils import Coords_3D

class Wire():
    def __init__(self, gate1: Coords_3D, gate2: Coords_3D):
        self.gates = [gate1, gate2]
        self.coords_wire_segments: list[tuple] = [gate1, gate2]

    def __len__(self):
        return self.length
    
    def __repr__(self):
        return f"Wire({self.coords_wire_segments})"

    @property
    def length(self):
        """gets the length of the wire"""
        return len(self.coords_wire_segments) - 1
    
    def is_circular(self) -> bool:
        """checks if the wire touches itself"""   
        # if this is the case we have duplicates in our coordinates, this a crossing
        return len(self.coords_wire_segments) != len(set(self.coords_wire_segments))
    
    @staticmethod
    def are_points_neighbours(coord1: Coords_3D, coord2: Coords_3D) -> bool:
        """Checks if points are next to each other in 3D space
        """
        return sum(abs(coord1[i] - coord2[i]) for i in range(len(coord1))) == 1
        
    def is_wire_connected(self) -> bool:
        """Checks is all wire segments are neighbours (and thus connected)"""
        for i in range(len(self.coords_wire_segments) - 1):
            if not self.are_points_neighbours(self.coords_wire_segments[i], self.coords_wire_segments[i + 1]):
                return False
               
        return True
    

    def append_wire_segment(self, coords: Coords_3D) -> None:
        """Adds a wire segment to a wire if it's a neighbour with one of the wire ends"""
        # don't add gate coords to the wire again
        if coords in self.gates:
            return
        
        # if next to second last coord, add before it
        if self.are_points_neighbours(coords, self.coords_wire_segments[-2]):
            self.coords_wire_segments.insert(-1, coords)
        
        # if next to second coord, add after it
        elif self.are_points_neighbours(coords, self.coords_wire_segments[1]):
            self.coords_wire_segments.insert(1, coords)

        return
    
    def append_wire_segment_list(self, coords_list: list[Coords_3D]) -> None:
        """Add multiple wire segments to a wire"""
        for coords in coords_list:
            self.append_wire_segment(coords)