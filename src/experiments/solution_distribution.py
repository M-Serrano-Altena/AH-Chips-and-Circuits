import os
from src.classes.chip import Chip
from src.algorithms.utils import save_object_to_json_file, run_algorithm

def algorithm_solution_distribution(
    algorithm_name: str, 
    chip_id: int, 
    net_id: int, 
    iterations: int, 
    json_output_save_name: str, 
    base_output_dir: str="results/latest/solution_distributions"
) -> None:
    total_costs = []
    total_intersections = []

    chip = Chip(chip_id=chip_id, net_id=net_id, padding=1)

    for i in range(iterations):
        run_algorithm(
            chip=chip,
            algorithm_name=algorithm_name,
            iterations=1,
            shuffle_wires=True,
            use_plot=False,
            save_plot=False,
            save_wire_config=False
        )

        if not chip.is_fully_connected():
            chip.reset_all_wires()
            continue

        cost = chip.calc_total_grid_cost()
        total_costs.append(cost)

        intersections = chip.get_wire_intersect_amount()
        total_intersections.append(intersections)

        print(f"iteration {i}: cost={cost}")

        chip.reset_all_wires()

    results = {
        "all_costs": total_costs,
        "short_circuit_count": total_intersections
    }

    algorithm_name = algorithm_name.replace(" ", "_")
    algorithm_name = algorithm_name.replace("A*", "astar").lower()

    if json_output_save_name is None:
        json_output_save_name = f"chip{chip_id}w{net_id}_{algorithm_name}_solution_distrib.json"

    save_path = os.path.join(base_output_dir, json_output_save_name)
    save_object_to_json_file(results, save_path)