import os
from src.classes.chip import Chip
from src.algorithms.utils import save_object_to_json_file, run_algorithm

def algorithm_solution_distribution(
    algorithm_name: str, 
    chip_id: int, 
    net_id: int, 
    iterations: int, 
    json_output_save_name: str|None=None, 
    base_output_dir: str="results/latest/solution_distributions"
) -> None:
    """
    Runs a specified algorithm for a given number of iterations, collecting the total grid cost
    and wire intersection count for each iteration. The results are saved in a JSON file.

    Args:
        algorithm_name (str): The name of the algorithm to be used (e.g., 'A*', 'PR', 'Greedy', etc.).
        chip_id (int): The chip ID to be used.
        net_id (int): The netlist ID to be used.
        iterations (int): The number of iterations to run the experiment.
        json_output_save_name (str, optional): The name of the output JSON file to save results. if None, a default name is used. Defaults to None.
        base_output_dir (str, optional): The directory to save the output results. Defaults to "results/latest/solution_distributions".

    Returns:
        None: The function does not return any values. It saves the results in a JSON file.
    """

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

    os.makedirs(base_output_dir, exist_ok=True)
    save_path = os.path.join(base_output_dir, json_output_save_name)
    save_object_to_json_file(results, save_path)