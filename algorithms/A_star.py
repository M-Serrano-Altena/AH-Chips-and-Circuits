from classes.chip import Chip
from algorithms.utils import Node, cost_function, Coords_3D, INTERSECTION_COST, COLLISION_COST
import itertools

class A_star:
    def __init__(self, chip: Chip, allow_intersections=True):
        self.chip = chip
        self.allow_intersections = allow_intersections

        self.frontier: list[Node] = []
        self.all_wire_segments_list: list[list[Coords_3D]] = []
        self.all_wire_segments_set: list[set[Coords_3D]] = []

    @staticmethod
    def manhattan_distance(coord1, coord2) -> int:
        return sum(abs(coord1[i] - coord2[i]) for i in range(len(coord1)))
    
    def get_existing_path_cost(self, node: Node) -> int:
        cost = 0
        cursor = node
        while cursor is not None:
            cost += 1
            cursor = cursor.parent

        return cost
    
    def get_extra_wire_cost(self, current_node) -> int:
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
                if current_coords_index == 0 and wire_segment_list[current_coords_index - 1] == parent_coords:
                    return COLLISION_COST
                
                if current_coords_index == len(wire_segment_list) and wire_segment_list[current_coords_index + 1] == parent_coords:
                    return COLLISION_COST

        return extra_cost

    
    def heuristic_function(self, current_node: Node, goal_coords: Coords_3D) -> int:
        manhattan_distance = self.manhattan_distance(current_node.state, goal_coords)
        exising_path_cost = self.get_existing_path_cost(current_node)
        extra_cost = self.get_extra_wire_cost(current_node)
        return manhattan_distance + exising_path_cost + extra_cost
    

    def solve(self) -> list[list[Coords_3D]]:
        for connection in self.chip.netlist:
            gate_1_id, gate_2_id = list(connection.items())[0]
            gate_1_coords = self.chip.gates[gate_1_id]

            # temporary goal node
            gate_2_coords = self.chip.gates[gate_2_id]

            wire_segment_list = self.solve_single_wire(start_coords=gate_1_coords, goal_coords=gate_2_coords)
            self.all_wire_segments_list.append(wire_segment_list)
            self.all_wire_segments_set.append(set(wire_segment_list))

        return self.all_wire_segments_list

            
    def solve_single_wire(self, start_coords: Coords_3D, goal_coords: Coords_3D) -> list[Coords_3D]:
        self.frontier = []
        self.start_gate = Node(start_coords, parent=None)
        self.frontier.append(self.start_gate)

        print_counter = 0

        while True:
            if len(self.frontier) == 0:
                raise Exception("No solution")

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


    def add_neighbours_to_frontier(self, node: Node, goal_coords: Coords_3D) -> None:
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
            
            # don't add gates other than start and goal gate to wire
            # if neighbour_coords in self.chip.gate_coords and neighbour_coords not in {self.start_gate.state, goal_coords}:
            #     continue

            if not self.allow_intersections:
                if neighbour_node.cost >= 300:
                    continue

            self.frontier.append(neighbour_node)