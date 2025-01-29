from src.classes.chip import Chip
from src.algorithms import IRRA
import time
import copy
import statistics
import os
from math import inf
from src.algorithms.utils import save_object_to_json_file

def IRRA_routing_comparison_both_inputs(
    chip_id: int, 
    net_id: int, 
    time_in_seconds_per_routing: int = 3600,
    iterations_per_routing: int = 0, 
    solution_input: str = "PR",
    specific_routing_only: str | None = None,
    json_output_save_name: str | None = None, 
    base_output_dir: str = "results/latest/parameter_research/"
) -> tuple[Chip, str]:
    """
    Conducts a comparison of different IRRA routing algorithms (BFS, Simulated Annealing and A* routing),
    to evaluate the total grid cost and short circuit count. 
    The results are saved to a JSON file. 

    Args:
        chip_id (int): The chip ID to be used for routing experiments.
        net_id (int): The netlist ID for the routing experiment.
        time_in_seconds_per_routing (int, optional): The maximum time to run the experiment for each routing type in seconds. Defaults to 3600 seconds.
        iterations_per_routing (int, optional): The number of iterations to run for each routing type. Defaults to 0, meaning the experiment will run for the specified time.
        solution_input (str, optional): The input solution type to use in the IRRA algorithm. Either 'PR' for Pseudo Random or 'A*' for A* routing. Defaults to 'PR'.
        specific_routing_only (str, optional): If provided, specifies which specific routing type to use ('BFS', 'Simulated Annealing', or 'A*'). Defaults to None, meaning all routing types will be tested.
        json_output_save_name (str, optional): The name of the output JSON file to save results. Defaults to None, in which case the default filename is used.
        base_output_dir (str, optional): The directory to save the output results. Defaults to "results/latest/parameter_research/".

    Returns:
        tuple[Chip, str]: The best chip found and the corresponding algorithm name that produced that best result.
    """

    def continue_with_runs() -> bool:
        """
        Determines whether the experiment should continue running based on the number of iterations or the elapsed time.

        Returns:
            bool: True if the experiment should continue, False otherwise.
        """
        if iterations_per_routing != 0:
            return n_runs < iterations_per_routing
        
        return time.time() - start < time_in_seconds_per_routing
    

    initial_chip = Chip(chip_id=chip_id, net_id=net_id, output_folder="output/Astar_vs_PR", padding=1)
    initial_chip_copy = copy.deepcopy(initial_chip)

    # set all the variables
    start = time.time()
    n_runs = 0
    all_costs = []
    short_circuit_count = []
    results = []
    rerouting_options = [
        {"simulated_annealing": False, "A*": False}, 
        {"simulated_annealing": True, "A*": False}, 
        {"simulated_annealing": False, "A*": True}
    ]
    best_chip = None
    lowest_cost = inf
    algorithm_names = [
        f"IRRA_{solution_input}_BFS", 
        f"IRRA_{solution_input}_Annealing", 
        f"IRRA_{solution_input}_A*"
    ]
    # best parameters we found for PR and A*
    temperature = 2000 if solution_input == "PR" else 750
    alpha = 0.9 if solution_input == "PR" else 0.99

    specific_routing_num = None

    if specific_routing_only is not None:
        routing_options = ["BFS", "Simulated Annealing", "A*"]
        if specific_routing_only not in routing_options:
            valid_options = "', '".join(routing_options.keys()).strip()
            raise ValueError(f"Routing option is invalid. Options: '{valid_options}'")
        
        else:
            specific_routing_num = routing_options.index(specific_routing_only)
                    

    # run for each reroute_type for an hour                     
    for i, reroute_type in enumerate(rerouting_options):
        # if specific routing is chosen, skip the other rerouting types
        if specific_routing_num is not None and i != specific_routing_num:
            continue

        while continue_with_runs():
            print(f"run: {n_runs}")
            initial_chip = initial_chip_copy

            # run the algorithm with the correct solution input
            if solution_input == "PR":
                irra_irra = IRRA.IRRA_PR(
                    chip=initial_chip, 
                    iterations=1, 
                    intersection_limit=0, 
                    acceptable_intersection=100, 
                    simulated_annealing=reroute_type["simulated_annealing"], 
                    temperature_alpha=alpha, 
                    start_temperature=temperature
                )
            elif solution_input == "A*":
                irra_irra = IRRA.IRRA_A_star(
                    chip=initial_chip, 
                    iterations=1, 
                    intersection_limit=0, 
                    acceptable_intersection=100, 
                    simulated_annealing=reroute_type["simulated_annealing"], 
                    A_star_rerouting=reroute_type["A*"], 
                    temperature_alpha=alpha, 
                    start_temperature=temperature
                )
            else:
                raise ValueError("Invalid solution input. Options: 'A*' or 'PR'")
            
            candidate_chip = irra_irra.run()
            chip_cost = candidate_chip.calc_total_grid_cost()
            short_circuit_count.append(candidate_chip.get_wire_intersect_amount())
            n_runs += 1
            # save cost, and keep chip of lowest cost
            if chip_cost < lowest_cost:
                best_chip = candidate_chip
                lowest_cost = chip_cost
                best_algorithm = algorithm_names[i]
            all_costs.append(chip_cost)

        # append data found to results and reset variables for next rerouting type experiment
        results.append({
            "simulated annealing": reroute_type["simulated_annealing"],
            "a_star_rerouting": reroute_type["A*"],
            "mean_cost": statistics.mean(all_costs),
            "median_cost": statistics.median(all_costs),
            "stdev_cost": statistics.stdev(all_costs),
            "best_cost found": min(all_costs),
            "median short circuit": statistics.median(short_circuit_count),
            "lowest short circuit": min(short_circuit_count),
            "n_runs": n_runs, 
            "all_costs": all_costs,
            "short_circuit_count": short_circuit_count
        })
        all_costs = []
        short_circuit_count = []
        start = time.time()
        n_runs = 0

    os.makedirs(base_output_dir, exist_ok=True)

    # save the results to a json file
    if json_output_save_name is not None:
        json_output_save_path = os.path.join(base_output_dir, json_output_save_name)
        save_object_to_json_file(results, json_output_save_path)
        return best_chip, best_algorithm

    # save the results to a json file with the correct name
    if solution_input == "A*":
        solution_input = "astar"

    solution_input = solution_input.lower()

    specific_routing_for_output = ["bfs", "sim_anneal", "astar"]

    if specific_routing_only is not None:
        specific_routing_only = specific_routing_for_output[specific_routing_num]
        json_output_save_name = f"chip{chip_id}w{net_id}_irra_{solution_input}_{specific_routing_only}_routing"
    else:
        json_output_save_name = f"chip{chip_id}w{net_id}_irra_{solution_input}_routing_comparison"

    if iterations_per_routing != 0:
        json_output_save_name += f"_{iterations_per_routing}_iterations.json"
    else:
        json_output_save_name += f"_{time_in_seconds_per_routing}_seconds.json"
    
    json_output_save_path = os.path.join(base_output_dir, json_output_save_name)
    save_object_to_json_file(results, json_output_save_path)

    return best_chip, best_algorithm