class Wire():

    def __init__(self, gate1: tuple[int, int], gate2: tuple[int, int]):
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
    def are_points_neighbours(coord1, coord2) -> bool:
        """Checks if points are next to each other
        """
        return abs(coord1[0] - coord2[0]) + abs(coord1[1] - coord2[1]) == 1
        
    def is_wire_connected(self) -> bool:
        for i in range(len(self.coords) - 1):
            if not self.are_points_neighbours(self.coords[i], self.coords[i + 1]):
                return False
            
        return True
    

    def append_coords(self, coords: tuple[int, int]) -> None:
        # don't add gate coords to the wire again
        if coords in self.gates:
            return

        if self.are_points_neighbours(coords, self.coords[-2]):
            self.coords.insert(-1, coords)
        
        elif self.are_points_neighbours(coords, self.coords[1]):
            self.coords.insert(1, coords)

        return
    
    def extend_coords(self, coords_list: list[tuple[int, int]]) -> None:
        for coords in coords_list:
            self.append_coords(coords)