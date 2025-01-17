from src.classes.chip import Chip
from src.algorithms.utils import Node, Coords_3D, INTERSECTION_COST, COLLISION_COST, manhattan_distance
from math import inf
import random
import copy

class A_star:
    """
    A* pathfinding algorithm implementation for routing wires in a chip
    """
    def __init__(self, chip: Chip, allow_intersections=True, max_cost: int|float=inf, random_seed: int|None=None, best_n_nodes: int|None = None):
        """
        Initialize the A_star solver.
        
        Args:
            chip (Chip): The chip layout containing grid information and netlist
            allow_intersections (bool): Whether intersections between wires are allowed
        """
        self.chip = chip
        self.chip_og = copy.deepcopy(chip)
        self.allow_intersections = allow_intersections
        self.max_cost = max_cost
        self.best_n_nodes = best_n_nodes
        
        if random_seed is not None:
            random.seed(random_seed)

        self.frontier: list[Node] = []
        self.all_wire_segments_list: list[list[Coords_3D]] = []
        self.all_wire_segments_set: list[set[Coords_3D]] = []
    
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
        manhattan_dist = manhattan_distance(current_node.state, goal_coords)
        exising_path_cost = self.get_existing_path_cost(current_node)
        extra_cost = self.get_extra_wire_cost(current_node)
        return manhattan_dist + exising_path_cost + extra_cost
    
    def solve_n_random_netlist_orders(self, random_netlist_order_amt: int) -> list[list[Coords_3D]]:
        best_wire_list = []
        lowest_cost = inf
        for i in range(random_netlist_order_amt):
            netlist = copy.deepcopy(self.chip.netlist)
            random.shuffle(netlist)
            self.chip = copy.deepcopy(self.chip_og)
            self.chip.netlist = netlist
            print(i, ":", self.chip.netlist)
            self.solve()
            self.chip.add_entire_wires(self.all_wire_segments_list)
            cost = self.chip.calc_total_grid_cost()
            is_fully_connected = self.chip.is_fully_connected()
            print("cost =", cost, "; fully connected:", is_fully_connected)
            if cost < lowest_cost and is_fully_connected:
                lowest_cost = cost
                # skip solutions with a higher cost than the lowest
                self.max_cost = lowest_cost
                print("lowest cost:", lowest_cost)
                best_wire_list = copy.deepcopy(self.all_wire_segments_list)

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
        self.all_wire_segments_list = []
        self.all_wire_segments_set = []

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

            sorted_frontier = sorted(self.frontier, key=lambda node: node.cost)
            node = sorted_frontier[0]

            if node.cost > self.max_cost:
                return None

            frontier_size = len(self.frontier)
            if self.best_n_nodes is not None and frontier_size > self.best_n_nodes:
                self.frontier = sorted_frontier[:self.best_n_nodes]

            self.frontier.remove(node)
                
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
        for neighbour_coords in self.chip.get_neighbours(node.state):

            # exclude neighbours that are already in the wire path
            if self.coord_in_node_path(neighbour_coords, node):
                continue

            neighbour_node = Node(state=neighbour_coords, parent=node)
            neighbour_node.cost = self.heuristic_function(neighbour_node, goal_coords=goal_coords)

            # don't add collisions to the frontier
            if neighbour_node.cost >= COLLISION_COST:
                continue
            
            # don't add gates other than start and goal gate to wire
            if neighbour_coords in self.chip.gate_coords - {self.start_gate.state, goal_coords}:
                continue
            
            # a bit crude because heuristic cost could be larger than 300 without intersection
            if not self.allow_intersections:
                if neighbour_node.cost >= 300:
                    continue
            
            # don't add nodes above the max cost
            if neighbour_node.cost > self.max_cost:
                continue

            self.frontier.append(neighbour_node)


    @staticmethod
    def coord_in_node_path(coord: Coords_3D, node: Node):
        cursor = node
        while cursor is not None:
            if coord == cursor.state:
                return True
            cursor = cursor.parent

        return False