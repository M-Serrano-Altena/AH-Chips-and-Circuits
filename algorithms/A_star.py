from classes.chip import Chip
from algorithms.utils import Node, Coords_3D, INTERSECTION_COST, COLLISION_COST
import itertools
from math import inf
import random

class A_star:
    """
    A* pathfinding algorithm implementation for routing wires in a chip
    """
    def __init__(self, chip: Chip, allow_intersections=True, max_cost: int|float=inf, random_seed: int=0):
        """
        Initialize the A_star solver.
        
        Args:
            chip (Chip): The chip layout containing grid information and netlist
            allow_intersections (bool): Whether intersections between wires are allowed
        """
        self.chip = chip
        self.allow_intersections = allow_intersections
        self.max_cost = max_cost
        
        random.seed(random_seed)

        self.frontier: list[Node] = []
        self.all_wire_segments_list: list[list[Coords_3D]] = []
        self.all_wire_segments_set: list[set[Coords_3D]] = []

    @staticmethod
    def manhattan_distance(coord1, coord2) -> int:
        """
        Calculate the Manhattan distance between two coordinates
        
        Args:
            coord1 (Coords_3D): The first coordinate
            coord2 (Coords_3D): The second coordinate
        
        Returns:
            int: The Manhattan distance between the two coordinates
        """
        return sum(abs(coord1[i] - coord2[i]) for i in range(len(coord1)))
    
    def get_existing_path_cost(self, node: Node) -> int:
        """
        Calculate the cost of the existing path from the start to the given node
        
        Args:
            node (Node): The current node
        
        Returns:
            int: The path cost from the start node to the current node
        """
        cost = 0
        cursor = node
        while cursor is not None:
            cost += 1
            cursor = cursor.parent

        return cost
    
    def get_extra_wire_cost(self, current_node) -> int:
        """
        Calculate the extra cost for the current node due to intersections or collisions
        
        Args:
            current_node (Node): The node being evaluated
        
        Returns:
            int: The extra cost due to intersections or collisions
        """
        extra_cost = 0

        # gate can't intersect or have a collision
        if current_node.state in self.chip.gate_coords:
            return extra_cost

        current_coords = current_node.state
        parent_coords = current_node.parent.state

        for wire_segment_list, wire_segment_set in zip(self.all_wire_segments_list, self.all_wire_segments_set):
            if current_coords in wire_segment_set and current_coords not in self.chip.gate_coords:
                extra_cost += INTERSECTION_COST

                # check for collision
                current_coords_index = wire_segment_list.index(current_coords)
                if current_coords_index != 0 and wire_segment_list[current_coords_index - 1] == parent_coords:
                    return COLLISION_COST
                
                if current_coords_index != len(wire_segment_list) and wire_segment_list[current_coords_index + 1] == parent_coords:
                    return COLLISION_COST

        return extra_cost

    
    def heuristic_function(self, current_node: Node, goal_coords: Coords_3D) -> int:
        """
        Calculate the heuristic cost for the current node
        
        Args:
            current_node (Node): The current node
            goal_coords (Coords_3D): The goal coordinates
        
        Returns:
            int: The total heuristic cost including: manhattan distance, path cost, and extra cost
        """
        manhattan_distance = self.manhattan_distance(current_node.state, goal_coords)
        exising_path_cost = self.get_existing_path_cost(current_node)
        extra_cost = self.get_extra_wire_cost(current_node)
        return manhattan_distance + exising_path_cost + extra_cost
    
    def solve_multiple_netlist_orders(self) -> list[list[Coords_3D]]:
        best_wire_list = []
        lowest_cost = inf
        for netlist in itertools.permutations(self.chip.netlist):
            self.chip.netlist = netlist
            self.solve()
            self.chip.add_entire_wires(self.all_wire_segments_list)
            cost = self.chip.calc_total_grid_cost()
            if cost < lowest_cost:
                lowest_cost = cost
                best_wire_list = self.all_wire_segments_list

            # if the lowest found cost is the lowest theoretical cost then the optimal solution has been found
            if lowest_cost == self.chip.manhatten_distance_sum:
                return best_wire_list

        return best_wire_list
            
    

    def solve(self) -> list[list[Coords_3D]]:
        """
        Solve the routing problem for all connections in the chip's netlist
        
        Returns:
            list[list[Coords_3D]]: A list of wire segments for each connection
        """
        for connection in self.chip.netlist:
            gate_1_id, gate_2_id = list(connection.items())[0]
            gate_1_coords = self.chip.gates[gate_1_id]

            # goal node
            gate_2_coords = self.chip.gates[gate_2_id]

            wire_segment_list = self.solve_single_wire(start_coords=gate_1_coords, goal_coords=gate_2_coords)
            if wire_segment_list is None:
                return []
            
            self.all_wire_segments_list.append(wire_segment_list)
            self.all_wire_segments_set.append(set(wire_segment_list))

        return self.all_wire_segments_list

            
    def solve_single_wire(self, start_coords: Coords_3D, goal_coords: Coords_3D) -> list[Coords_3D]|None:
        """
        Solve the routing problem for a single wire between two gates
        
        Args:
            start_coords (Coords_3D): The starting gate coordinates
            goal_coords (Coords_3D): The goal gate coordinates
        
        Returns:
            list[Coords_3D]: A list of coordinates representing the path for the wire
        """
        self.frontier = []
        self.start_gate = Node(start_coords, parent=None)
        self.frontier.append(self.start_gate)

        print_counter = 0

        while len(self.frontier) < 100000:
            # no solution
            if len(self.frontier) == 0:
                return None

            node = sorted(self.frontier, key=lambda node: node.cost)[0]
            self.frontier.remove(node)

            frontier_size = len(self.frontier)
            if frontier_size / 10000 > print_counter:
                print("frontier size:", frontier_size)
                print_counter += 1

            if node.state == goal_coords:
                wire_segment_list = []
                while node is not None:
                    wire_segment_list.append(node.state)
                    node = node.parent

                wire_segment_list = list(reversed(wire_segment_list))
                return wire_segment_list

            
            self.add_neighbours_to_frontier(node, goal_coords)

        # no found solution
        return None


    def add_neighbours_to_frontier(self, node: Node, goal_coords: Coords_3D) -> None:
        """
        Add the neighbours of the current node to the frontier for evaluation
        
        Args:
            node (Node): The current node
            goal_coords (Coords_3D): The goal coordinates
        """
        coords_dim = len(node.state)
        all_offset_combos = itertools.product([-1, 0, 1], repeat=coords_dim)
        all_neighbour_coords = [
            tuple(node.state[i] + offset_coords[i] for i in range(coords_dim))
            for offset_coords in all_offset_combos
            if sum(offset_coords[i] != 0 for i in range(coords_dim)) == 1 # ensures only 1 dimension is non-zero
        ]

        for neighbour_coords in all_neighbour_coords:
            # skip out of bounds neighbours
            if any(neighbour_coords[i] < 0 or neighbour_coords[i] >= self.chip.grid_shape[i] for i in range(coords_dim)):
                continue

            neighbour_node = Node(state=neighbour_coords, parent=node)
            neighbour_node.cost = self.heuristic_function(neighbour_node, goal_coords=goal_coords)

            # don't add collisions to the frontier
            if neighbour_node.cost >= COLLISION_COST:
                continue
            
            # # don't add gates other than start and goal gate to wire
            # if neighbour_coords in self.chip.gate_coords and neighbour_coords not in {self.start_gate.state, goal_coords}:
            #     continue

            if not self.allow_intersections:
                if neighbour_node.cost >= 300:
                    continue
            
            # don't add nodes above the max cost
            if neighbour_node.cost > self.max_cost:
                continue

            self.frontier.append(neighbour_node)