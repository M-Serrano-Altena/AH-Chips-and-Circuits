from src.classes.chip import Chip
from src.algorithms import IRRA
import copy
import statistics
from src.algorithms.utils import save_object_to_json_file
from math import inf
import os

def annealing_parameter_experiment(
    chip_id: int, 
    net_id: int, 
    temperature_candidates: list[int], 
    alpha_candidates: list[int], 
    solution_input: str = "A*", 
    iterations: int = 250, 
    json_output_save_name: str | None = None,
    base_output_dir: str = "results/latest/parameter_research/"
) -> tuple[Chip, str]:
    """
    Runs an annealing parameter experiment on different chip configurations, testing different temperature
    and alpha parameters for simulated annealing with either the A* or PR input with the IRRA algorithm.
    Saves the results to a JSON file and returns the chip with the lowest cost found during the experiment.

    Args:
        chip_id (int): The ID of the chip to experiment with.
        net_id (int): The ID of the netlist for the chip.
        temperature_candidates (list[int]): A list of candidate temperature values for the simulated annealing.
        alpha_candidates (list[int]): A list of candidate alpha values for the simulated annealing.
        solution_input (str): The input solution to use for the IRRA algorithm, either "A*" or "PR" (default is "A*").
        iterations (int): The number of iterations for the annealing algorithm (default is 250).
        json_output_save_name (str | None): A custom filename to save the JSON output (default is None, meaning a general name is chosen based on the parameters).
        base_output_dir (str): The base directory where results will be saved (default is "results/latest/parameter_research/").

    Returns:
        tuple[Chip, str]: A tuple containing the best chip found and the algorithm used for the experiment.

    Raises:
        ValueError: If an invalid solution_input is provided (not "A*" or "PR").
    """

    print("Starting annealing parameter experiment...")
    lowest_cost = inf
    chip = Chip(chip_id=chip_id, net_id=net_id, output_folder="output", padding=1)
    chip_og = copy.deepcopy(chip)
    best_chip = None
    algorithm = f"IRRA_{solution_input}_Annealing"
    results = []

    # running over each parameter candidate
    for temperature in temperature_candidates:
        for alpha in alpha_candidates:
            print(f"temperature = {temperature}; alpha = {alpha}")
            chip = chip_og
            if solution_input == "A*":
                irra_algo = IRRA.IRRA_A_star(
                    chip=chip, 
                    iterations=iterations, 
                    intersection_limit=0, 
                    acceptable_intersection=1000, 
                    simulated_annealing=True, 
                    temperature_alpha=alpha, 
                    start_temperature=temperature
                )
            elif solution_input == "PR":
                irra_algo = IRRA.IRRA_PR(
                    chip=chip, 
                    iterations=iterations, 
                    intersection_limit=0, 
                    acceptable_intersection=1000, 
                    simulated_annealing=True, 
                    temperature_alpha=alpha, 
                    start_temperature=temperature
                )
            else:
                raise ValueError("Invalid solution input. Options: 'A*' or 'PR'")

            candidate_chip = irra_algo.run()
            chip_cost = candidate_chip.calc_total_grid_cost()
            all_costs = irra_algo.all_costs
            # save cost, and keep chip of lowest cost
            if chip_cost < lowest_cost:
                best_chip = candidate_chip
                lowest_cost = chip_cost

            # appending the data to the results
            results.append({
                "temperature": temperature,
                "alpha": alpha,
                "mean_cost": statistics.mean(all_costs),
                "median_cost": statistics.median(all_costs),
                "stdev_cost": statistics.stdev(all_costs) if len(all_costs) > 1 else 0,
                "best_cost found": min(all_costs),
                "all_costs": all_costs
            })

    os.makedirs(base_output_dir, exist_ok=True)

    # saving output as json file
    if json_output_save_name is not None:
        json_output_save_path = os.path.join(base_output_dir, json_output_save_name)
        save_object_to_json_file(results, json_output_save_path)
        return best_chip, algorithm

    if solution_input == "A*":
        solution_input = "astar"

    solution_input = solution_input.lower()
    
    json_output_save_name = f"chip{chip_id}w{net_id}_annealing_{solution_input}.json"
    json_output_save_path = os.path.join(base_output_dir, json_output_save_name)
    save_object_to_json_file(results, json_output_save_path)

    return best_chip, algorithm
    


