import argparse
from src.classes.chip import Chip, load_chip_from_csv

# Import algorithms
from src.algorithms.A_star import A_star, A_star_optimize
from src.algorithms.greed import Greed, Greed_random
from src.algorithms.random_algo import Pseudo_random, True_random
from src.algorithms.IRRA import IRRA_PR, IRRA_A_star
from src.algorithms.utils import run_algorithm, optimize_chip

# Import experiments
from src.experiments.annealing_parameter_exp import annealing_parameter_experiment
from src.experiments.irra_offset_exp import offset_experiment
from src.experiments.irra_routing_comparison import IRRA_routing_comparison_both_inputs
from src.experiments.solution_distribution import algorithm_solution_distribution

# Import visualisation
from src.visualisation.irra_offset_test_plot import create_offset_experiment_plot
from src.visualisation.parameter_annealing_plot import create_sim_anneal_heatmap
from src.visualisation.plot_astar_routing_irra_input_comparison import create_input_comparison_hist
from src.visualisation.plot_irra_all_comparisons import create_irra_all_comparisons_boxplot
from src.visualisation.plot_irra_astar_routing_comparison import create_routing_comparison_hist
from src.visualisation.plot_solution_distrib import create_solution_distribution_hist


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process optional command-line arguments.")

    parser.add_argument("-c", "--chip_id", type=int, choices=[0, 1, 2], default=0, 
                        help="Chip to use (default: 0)")
    parser.add_argument("-w", "--wire_config", type=int, choices=[1, 2, 3, 4, 5, 6, 7, 8, 9], default=1, 
                        help="Netlist to use (chip 0: {1,2,3}; chip 1: {4,5,6}; chip 2: {7,8,9} - default: 1)")
    parser.add_argument("-n", "--num_of_iterations", type=int, default=1, help="Number of iterations to repeat the algorithm (default: 1)")
    parser.add_argument("-p", "--padding", type=int, default=1, help="Extra space on all sides of the grid  (default: 1)")
    parser.add_argument("-a", "--algorithm", choices=[
        "Greed", "Greed Random", "GR", "Pseudo Random", "PR", "True Random", "TR", "A*", "IRRA_PR", "IRRA_A*"
    ], default="IRRA_A*", help="Algorithm to connect wires with (default: IRRA_A*)")
    parser.add_argument("-r", "--routing_type", choices=["BFS", "Simulated Annealing", "A*"], default="A*",
                        help="Routing type to use with IRRA algorithm (default: BFS)")
    parser.add_argument("--no_shuffle", action="store_true", help="Disable random wire order (default: False)")
    parser.add_argument("--no_plot", action="store_true", help="Disable plotting the chip after running the algorithm (default: False)")
    parser.add_argument("-o", "--optimize", action="store_true", help="Optimize the chip after running the algorithm")
    parser.add_argument("-l", "--load", type=str, default=None, help="Load a chip configuration from a given CSV file")
    parser.add_argument("-s", "--save", action="store_true", help="Save the wire configuration and interactive plot to the 'results/latest' folder")

    args = parser.parse_args()

    chip_id = args.chip_id
    net_id = args.wire_config
    iterations = args.num_of_iterations
    padding = args.padding
    algorithm_name = args.algorithm
    routing_type = args.routing_type
    shuffle_wires = not args.no_shuffle
    optimize = args.optimize
    load_file = args.load
    use_plot = not args.no_plot
    save_plot = args.save
    save_config = args.save

    if load_file is not None:
        chip = load_chip_from_csv(load_file, padding=padding)
    else:
        chip = Chip(chip_id=chip_id, net_id=net_id, padding=padding)

    #===========================================================================
    # Run chosen algorithm with just command-line arguments
    #===========================================================================

    run_algorithm(
        chip=chip,
        algorithm_name=algorithm_name,
        routing_type=routing_type,
        shuffle_wires=shuffle_wires,
        iterations=iterations,
        use_plot=use_plot and not optimize,
        save_plot=save_plot,
        # don't save wire config if we're optimizing
        save_wire_config=save_config if not optimize else False, 
    )

    #===========================================================================
    # Optimize chip after running algorithm
    #===========================================================================
    # we highly recommend using the optimize argument (-o) as it does 
    # help lower the cost a lot
    if optimize and chip.is_fully_connected():
        optimize_chip(
            chip,
            algo_used=algorithm_name,
            reroute_n_wires=10, 
            start_temperature=5, 
            alpha=0.99, 
            use_plot=use_plot,
            save_plot=save_plot, 
            save_wire_config=save_config,
            total_permutations_limit=20000,
            amount_of_random_iterations=500,
        )

    elif optimize:
        print("Chip is not fully connected, cannot optimize")

    #============================================================================
    # Tweak algorithm specific parameters
    #============================================================================

    # -------------------------------- Greedy -----------------------------------
    # used_algo_name = "Greed"
    # greed_algo = Greed(chip=chip, max_offset=50, allow_short_circuit=True, shuffle_wires=True, print_log_messages=True)

    ## choose 1 of the following 2 options
    # greed_algo.run()
    # greed_algo.run_random_netlist_orders(iterations=100)

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("output.csv")

    # ----------------------------- Greedy Random -------------------------------
    # used_algo_name = "Greed Random"
    # greed_random_algo = Greed_random(chip=chip, allow_short_circuit=True)

    ## choose 1 of the following 2 options
    # greed_random_algo.run()
    # greed_random_algo.run_random_netlist_orders(iterations=100)

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("output.csv")

    # --------------------------- Pseudo Random ---------------------------------
    # Note: this algorithm may take a minute to generate a solution
    # for a harder chip

    # used_algo_name = "Pseudo Random"
    # pseudo_random_algo = Pseudo_random(chip=chip, allow_short_circuit=True)

    ## choose 1 of the following 2 options
    # pseudo_random_algo.run()
    # pseudo_random_algo.run_random_netlist_orders(iterations=5)

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("output.csv")

    # --------------------------- True Random ------------------------------------
    # Note: we recommend keeping the max_offset small and running this 
    # with chip 0, net 1. Otherwise the algorithm will be running for way too long.
    # The point of this algorithm is to show that a general (almost) unconstraint 
    # algorithm doesn't work for this case (which is why we use Pseudo Random)

    # used_algo_name = "True Random"
    # true_random_algo = True_random(chip=chip, allow_short_circuit=True, max_offset=5)

    ## choose 1 of the following 2 options
    # true_random_algo.run()
    # true_random_algo.run_random_netlist_orders(iterations=100)

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("output.csv")


    # --------------------------- A* --------------------------------------------
    # used_algo_name = "A*"
    # A_star_algo = A_star(chip=chip, sort_wires=False, shuffle_wires=True)

    ## choose 1 of the following 2 options
    # A_star_algo.run()
    # # A_star_algo.run_random_netlist_orders(iterations=100)

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("output.csv")


    # ------------------------- IRRA PR (BFS routing) ---------------------------
    # Note: uses Pseudo Random as input solution, so for harder chips may take 
    # a minute to get going

    # used_algo_name = "IRRA PR (BFS)"
    # irra_pr_bfs_routing_algo = IRRA_PR(
    #     chip=chip, 
    #     iterations=1, 
    #     acceptable_intersection=1000, 
    #     simulated_annealing=False, 
    #     A_star_rerouting=False
    # )
    # irra_pr_bfs_routing_algo.run()

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("output.csv")


    # ------------------ IRRA PR (Simulated Annealing routing) ------------------
    # used_algo_name = "IRRA PR (Simulated Annealing)"
    # irra_pr_sim_anneal_routing_algo = IRRA_PR(
    #     chip=chip, 
    #     iterations=1, 
    #     acceptable_intersection=1000, 
    #     simulated_annealing=True, 
    #     A_star_rerouting=False
    # )
    # irra_pr_sim_anneal_routing_algo.run()

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("output.csv")

    # ------------------------ IRRA PR (A* routing) -----------------------------
    # used_algo_name = "IRRA PR (A* routing)"
    # irra_pr_a_star_routing_algo = IRRA_PR(
    #     chip=chip, 
    #     iterations=10, 
    #     acceptable_intersection=1000, 
    #     simulated_annealing=False, 
    #     A_star_rerouting=True
    # )
    # irra_pr_a_star_routing_algo.run()

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("output.csv")

    # --------------------- IRRA A* (BFS routing)--------------------------------
    # used_algo_name = "IRRA A* (BFS)"
    # irra_a_star_bfs_routing_algo = IRRA_A_star(
    #     chip=chip, 
    #     iterations=10, 
    #     acceptable_intersection=1000, 
    #     simulated_annealing=False, 
    #     A_star_rerouting=False
    # )
    # irra_a_star_bfs_routing_algo.run()

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("output.csv")

    # --------------- IRRA A* (Simulated Annealing routing) ---------------------
    # used_algo_name = "IRRA A* (Simulated Annealing)"
    # irra_a_star_sim_anneal_routing_algo = IRRA_A_star(
    #     chip=chip, 
    #     iterations=10, 
    #     acceptable_intersection=1000, 
    #     simulated_annealing=True, 
    #     A_star_rerouting=False
    # )
    # irra_a_star_sim_anneal_routing_algo.run()

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("output.csv")

    # ---------------------- IRRA A* (A* routing) -------------------------------
    # used_algo_name = "IRRA A* (A* routing)"
    # irra_a_star_a_star_routing_algo = IRRA_A_star(
    #     chip=chip, 
    #     iterations=10, 
    #     acceptable_intersection=1000, 
    #     simulated_annealing=False, 
    #     A_star_rerouting=True
    # )
    # irra_a_star_a_star_routing_algo.run()

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("output.csv")

    #============================================================================
    # Optimize chip after running algorithm
    #============================================================================

    # optimize_chip(
    #     chip,
    #     algo_used=used_algo_name,
    #     reroute_n_wires=2,
    #     start_temperature=5,
    #     alpha=0.99,
    #     save_plot=False,
    #     save_wire_config=False
    # )

    #============================================================================

    #============================================================================
    # Experiments
    #============================================================================

    # ------------------- Annealing Parameter Experiment ------------------------
    # you can change the temperature_candidates and alpha_candidates to test
    # different values. Changing solution inptut to "A*" will test the A* solution
    # instead of the Pseudo Random solution as input for the IRRA algorithm

    # temperature_candidates = [500, 750, 1000, 1500, 2000]
    # alpha_candidates = [0.9, 0.925, 0.95, 0.975, 0.99]
    # annealing_parameter_experiment(
    #     chip_id=chip_id,
    #     net_id=net_id,
    #     solution_input="PR",
    #     iterations=250,
    #     temperature_candidates=temperature_candidates,
    #     alpha_candidates=alpha_candidates,
    #     json_output_save_name=None,
    #     base_output_dir="results/latest/parameter_research/"
    # )

    # ------------------- IRRA Routing Comparison -------------------------------
    # You can add specific_routing_only to only run the algorithm on a specific
    # routing type. For example, specific_routing_only="A*" will only run the IRRA
    # algorithm with A* routing. If you want to run each routing type for
    # an amount of iterations instead of a time limit, you can set
    # iterations_per_routing to a positive integer

    # IRRA_routing_comparison_both_inputs(
    #     chip_id=chip_id,
    #     net_id=net_id,
    #     solution_input="A*",
    #     iterations_per_routing=10000,
    #     time_in_seconds_per_routing=0,
    #     json_output_save_name=None,
    #     specific_routing_only=None,
    #     base_output_dir="results/latest/parameter_research/"
    # )

    # ------------------- IRRA Offset Experiment --------------------------------
    # Same logic for arguments as IRRA Routing Comparison experiment.
    # You can avoid all uneven offsets, because a wire will never have an uneven
    # extra length compared to the minimum length of the wire.
    # (each extra direction must eventually be compensated by
    # the opposite direction to arrive at the same target coordinates)
    
    # offset_experiment(
    #     chip_id=chip_id,
    #     net_id=net_id,
    #     offsets=range(10, 100, 2),
    #     solution_input="BFS",
    #     iterations_per_offset=0,
    #     time_in_seconds_per_offset=300,
    #     json_output_save_name=None,
    #     base_output_dir="results/latest/parameter_research/"
    # )

    # ------------------- Solution Distribution ---------------------------------
    # algorithm_solution_distribution(
    #     chip_id=chip_id,
    #     net_id=net_id,
    #     algorithm_name="PR",
    #     iterations=1000,
    #     json_output_save_name=None,
    #     base_output_dir="results/latest/solution_distributions/"
    # )

    #============================================================================

    #============================================================================
    # Visualisation
    #============================================================================

    # ------------------- Offset Experiment Plot --------------------------------
    # if the file name includes some mention of the chip and net id, you can 
    # also leave the chip_id and net_id arguments as None
    # create_offset_experiment_plot(
    #     json_offset_results_file="results/experiments/parameter_research/chip2w7_irra_PR_offset_experiment.json",
    #     chip_id=None,
    #     net_id=None,
    #     plot_save_name=None,
    #     plot_save_base_dir="results/latest/experiment_plots"
    # )

    # ------------------- Parameter Annealing heatmap ----------------------------
    # create_sim_anneal_heatmap(
    #     json_sim_anneal_data_filepath="results/experiments/parameter_research/chip2w7_annealing_pr.json",
    #     solution_input="PR",
    #     chip_id=None,
    #     net_id=None,
    #     plot_save_name=None,
    #     plot_save_base_dir="results/latest/experiment_plots"
    # )

    # ------------------- Input Comparison Histogram ----------------------------
    # create_input_comparison_hist(
    #     json_astar_path="results/experiments/irra_routing_comparisons/chip2w7_irra_astar_routing_comparison_10000_iterations.json",
    #     json_pr_path="results/experiments/irra_routing_comparisons/chip2w7_irra_PR_astar_routing_1000_iterations.json",
    #     routing_type="A*", # "BFS", "Simulated Annealing", "A*"
    #     chip_id=None,
    #     net_id=None,
    #     plot_save_name=None,
    #     plot_save_base_dir="results/latest/experiment_plots"
    # )

    # ------------------- Routing Comparison Histogram --------------------------
    # create_routing_comparison_hist(
    #     json_data_filepath="results/experiments/irra_routing_comparisons/chip2w7_irra_astar_routing_comparison_10000_iterations.json",
    #     chip_id=None,
    #     net_id=None,
    #     solution_input="A*",
    #     plot_save_name=None,
    #     plot_save_base_dir="results/latest/experiment_plots"
    # )

    # ------------------- All Comparisons Boxplot -------------------------------
    # create_irra_all_comparisons_boxplot(
    #     json_routing_comparison_astar_path="results/experiments/irra_routing_comparisons/chip2w7_irra_astar_routing_comparison_3600_seconds.json",
    #     json_routing_comparison_pr_path="results/experiments/irra_routing_comparisons/chip2w7_irra_pr_routing_comparison_3600_seconds.json",
    #     chip_id=None,
    #     net_id=None,
    #     add_baseline=True,
    #     json_astar_solution_distrib_filepath="results/experiments/solution_distributions/chip2w7_astar_solution_distrib.json",
    #     json_pr_solution_distrib_filepath="results/experiments/solution_distributions/chip2w7_pr_solution_distrib.json",
    #     plot_save_name=None,
    #     plot_save_base_dir="results/latest/experiment_plots"
    # )

    # ------------------- Solution Distribution Histogram -----------------------
    # create_solution_distribution_hist(
    #     json_solution_distrib_filepath="results/experiments/solution_distributions/chip2w7_pr_solution_distrib.json",
    #     chip_id=None,
    #     net_id=None,
    #     algorithm_name="PR",
    #     bins=39,
    #     plot_costs_save_name=None,
    #     plot_intersections_save_name=None,
    #     plot_save_base_dir="results/latest/experiment_plots"
    # )

    #============================================================================
    
