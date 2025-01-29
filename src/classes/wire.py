from src.algorithms.utils import Coords_3D, manhattan_distance

class Wire():
    """
    A class representing a wire that connects two gates in 3D space.
    It manages the wire segments between these gates and provides methods
    to manipulate and query the wire's properties.

    Attributes:
        gates (list[Coords_3D]): The coordinates of the two gates that the wire connects.
        coords_wire_segments (list[tuple]): The list of coordinates representing the wire segments.
    """
    def __init__(self, gate1: Coords_3D, gate2: Coords_3D) -> None:
        """
        Initializes the Wire instance with two gates and their corresponding wire segments.
        
        Args:
            gate1 (Coords_3D): The coordinates of the first gate.
            gate2 (Coords_3D): The coordinates of the second gate.
        """
        self.gates = [gate1, gate2]
        self.coords_wire_segments: list[tuple] = [gate1, gate2]

    def __len__(self) -> int:
        """
        Returns the length of the wire (number of segments)
        """
        return self.length
    
    def __repr__(self) -> str:
        """
        Returns a string representation of the Wire instance, showing its wire segments.
        
        Returns:
            str: A string representation of the wire's segments.
        """
        return f"Wire({self.coords_wire_segments})"
    
    def eq(self, other: 'Wire') -> bool:
        """
        Checks if two wires are equal by comparing their wire segments.

        Args:
            other (Wire): The other wire to compare against.
        
        Returns:
            bool: True if the wires have the same segments, False otherwise.
        """
        return self.coords_wire_segments == other.coords_wire_segments

    @property
    def length(self):
        """
        Returns the length of the wire (number of segments).
        """
        return len(self.coords_wire_segments) - 1
    
    def intersects_itself(self) -> bool:
        """
        Checks if the wire intersects itself by detecting duplicate coordinates in the wire's segments.

        Returns:
            bool: True if the wire has self-intersections, False otherwise.
        """
        # if this is the case we have duplicates in our coordinates, this a crossing
        return len(self.coords_wire_segments) != len(set(self.coords_wire_segments))
    
    @staticmethod
    def are_points_neighbours(coord1: Coords_3D, coord2: Coords_3D) -> bool:
        """
        Checks if two points are next to each other in 3D space, i.e., their coordinates differ by 1 in exactly one dimension
        by using their Manhattan distance.

        Args:
            coord1 (Coords_3D): The first coordinate.
            coord2 (Coords_3D): The second coordinate.
        
        Returns:
            bool: True if the points are neighbours, False otherwise.
        """
        return manhattan_distance(coord1, coord2) == 1
        
    def is_wire_connected(self) -> bool:
        """
        Checks if all wire segments are connected by verifying if adjacent segments are neighbours in 3D space.

        Returns:
            bool: True if all wire segments are connected, False otherwise.
        """
        for i in range(len(self.coords_wire_segments) - 1):
            if not self.are_points_neighbours(self.coords_wire_segments[i], self.coords_wire_segments[i + 1]):
                return False
               
        return True
    

    def append_wire_segment(self, coords: Coords_3D) -> None:
        """
        Adds a wire segment to the wire if it is adjacent to one of the wire's ends.

        Args:
            coords (Coords_3D): The coordinates of the new wire segment.
        
        If the coordinates match one of the wire gates, they are ignored.
        If the coordinates are adjacent to the second-last or second segment, it is added accordingly.
        """
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
        """
        Adds multiple wire segments to the wire.

        Args:
            coords_list (list[Coords_3D]): A list of coordinates representing wire segments to add.
        """
        for coords in coords_list:
            self.append_wire_segment(coords)

    def reset(self) -> None:
        """
        Resets the wire to its initial state by restoring its coordinates to the gate positions.
        """
        if len(self.coords_wire_segments) >= 2:
            self.coords_wire_segments = self.gates[:]