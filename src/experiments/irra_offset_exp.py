from src.classes.chip import Chip
from src.algorithms import IRRA
import time
import copy
import statistics
from src.algorithms.utils import save_object_to_json_file
from typing import Iterable
import os

def offset_experiment(
    chip_id: int, 
    net_id: int, 
    offsets: Iterable[int], 
    solution_input: str = "PR", 
    time_in_seconds_per_offset: int = 300,
    iterations_per_offset: int = 0, 
    json_output_save_name: str | None = None,
    base_output_dir: str = "results/latest/parameter_research/"
) -> None:
    
    def continue_with_runs() -> bool:
        if iterations_per_offset != 0:
            return n_runs < iterations_per_offset
        
        return time.time() - start < time_in_seconds_per_offset

    chip0 = Chip(chip_id=chip_id, net_id=net_id, output_folder="output", padding=1)
    chip_og = copy.deepcopy(chip0)

    start = time.time()
    n_runs = 0
    all_costs = []
    short_circuit_count = []
    results = []
    solution_input_options = ["PR", "A*"]

    # best parameters we found for PR and A*
    temperature = 2000 if solution_input == "PR" else 750
    alpha = 0.9 if solution_input == "PR" else 0.99

    if solution_input not in solution_input_options:
        raise ValueError("solution_input must be either 'PR' or 'A*'")
    

    for offset in offsets:
        while continue_with_runs():
            print(f"Offset: {offset} | run: {n_runs}")
            chip = chip_og
            if solution_input == "PR":
                irra_irra = IRRA.IRRA_PR(chip=chip, iterations=1, intersection_limit=0, rerouting_offset=offset, simulated_annealing=True, start_temperature=temperature, temperature_alpha=alpha)
            else:
                irra_irra = IRRA.IRRA_A_star(chip=chip, iterations=1, intersection_limit=0, rerouting_offset=offset, simulated_annealing=True, start_temperature=temperature, temperature_alpha=alpha)
            
            best_chip = irra_irra.run()
            all_costs.append(best_chip.calc_total_grid_cost())
            short_circuit_count.append(best_chip.get_wire_intersect_amount())
            n_runs += 1

        results.append({
                "offset": offset,
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

    if solution_input == "A*":
        solution_input = "astar"

    solution_input = solution_input.lower()

    if json_output_save_name is None:
        json_output_save_name = f"chip{chip_id}w{net_id}_irra_{solution_input}_offset_experiment.json"

    json_output_save_path = os.path.join(base_output_dir, json_output_save_name)
    save_object_to_json_file(results, json_output_save_path)