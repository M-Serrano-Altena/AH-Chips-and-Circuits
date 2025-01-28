import argparse
from src.classes.chip import Chip, load_chip_from_csv
from src.algorithms.A_star import A_star, A_star_optimize
from src.algorithms.greed import Greed, Greed_random
from src.algorithms.random_algo import Pseudo_random
from src.algorithms.IRRA import IRRA_PR, IRRA_A_star
from src.algorithms.utils import run_algorithm, optimize_chip


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process optional command-line arguments.")

    parser.add_argument("-c", "--chip_id", type=int, choices=[0, 1, 2], default=0, 
                        help="Chip to use (default: 0)")
    parser.add_argument("-n", "--net_id", type=int, choices=[1, 2, 3, 4, 5, 6, 7, 8, 9], default=1, 
                        help="Netlist to use (chip 0: {1,2,3}; chip 1: {4,5,6}; chip 2: {7,8,9} - default: 1)")
    parser.add_argument("-i", "--iterations", type=int, default=1, help="Number of iterations (default: 1)")
    parser.add_argument("-p", "--padding", type=int, default=1, help="Padding to use (default: 1)")
    parser.add_argument("-a", "--algorithm", choices=[
        "Greed", "Greed Random", "Pseudo Random", "A*", "IRRA_PR", "IRRA_A*"
    ], default="IRRA_A*", help="Algorithm to use (default: IRRA_A*)")
    parser.add_argument("-r", "--routing_type", choices=["BFS", "Simulated Annealing", "A*"], default="A*",
                        help="Routing type to use with IRRA algorithm (default: BFS)")
    parser.add_argument("--no_shuffle", action="store_false", help="Disable random wire order (default: True)")
    parser.add_argument("-o", "--optimize", action="store_true", help="Optimize the chip after running the algorithm")
    parser.add_argument("-l", "--load", type=str, default=None, help="Load a chip from a given CSV file")
    parser.add_argument("-s", "--save", action="store_true", help="Save the wire configuration and plot to the 'output' folder")

    args = parser.parse_args()

    chip_id = args.chip_id
    net_id = args.net_id
    iterations = args.iterations
    padding = args.padding
    algorithm_name = args.algorithm
    routing_type = args.routing_type
    shuffle_wires = not args.no_shuffle
    optimize = args.optimize
    load_file = args.load
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
        plot=not optimize,
        save_plot=save_plot,
        # don't save wire config if we're optimizing
        save_wire_config=save_config if not optimize else False, 
    )

    #===========================================================================
    # Optimize chip after running algorithm
    #===========================================================================
    if optimize and chip.is_fully_connected():
        optimize_chip(
            chip,
            algo_used=algorithm_name,
            reroute_n_wires=2, 
            start_temperature=5, 
            alpha=0.99, 
            save_plot=save_plot, 
            save_wire_config=save_config
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
    # chip.save_output("final_output.csv")

    # ----------------------------- Greedy Random -------------------------------
    # used_algo_name = "Greed Random"
    # greed_random_algo = Greed_random(chip=chip, allow_short_circuit=True)

    ## choose 1 of the following 2 options
    # greed_random_algo.run()
    # greed_random_algo.run_random_netlist_orders(iterations=100)

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("final_output.csv")

    # --------------------------- Pseudo Random ---------------------------------
    # used_algo_name = "Pseudo Random"
    # pseudo_random_algo = Pseudo_random(chip=chip, allow_short_circuit=True)

    ## choose 1 of the following 2 options
    # pseudo_random_algo.run()
    # pseudo_random_algo.run_random_netlist_orders(iterations=100)

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("final_output.csv")

    # --------------------------- A* --------------------------------------------
    # used_algo_name = "A*"
    # A_star_algo = A_star(chip=chip, sort_wires=False, shuffle_wires=True)

    ## choose 1 of the following 2 options
    # A_star_algo.run()
    # A_star_algo.run_random_netlist_orders(iterations=100)

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("final_output.csv")


    # ------------------------- IRRA PR (BFS routing) ---------------------------
    # used_algo_name = "IRRA PR (BFS)"
    # irra_pr_bfs_routing_algo = IRRA_PR(chip=chip, iterations=10, simulated_annealing=False, A_star_rerouting=False)
    # irra_pr_bfs_routing_algo.run()

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("final_output.csv")


    # ------------------ IRRA PR (Simulated Annealing routing) ------------------
    # used_algo_name = "IRRA PR (Simulated Annealing)"
    # irra_pr_sim_anneal_routing_algo = IRRA_PR(chip=chip, iterations=10, simulated_annealing=True, A_star_rerouting=False)
    # irra_pr_sim_annea_routing_algo.run()

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("final_output.csv")

    # ------------------------ IRRA PR (A* routing) -----------------------------
    # used_algo_name = "IRRA PR (A* routing)"
    # irra_pr_a_star_routing_algo = IRRA_PR(chip=chip, iterations=10, simulated_annealing=False, A_star_rerouting=True)
    # irra_pr_a_star_routing_algo.run()

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("final_output.csv")

    # --------------------- IRRA A* (BFS routing)--------------------------------
    # used_algo_name = "IRRA A* (BFS)"
    # irra_a_star_bfs_routing_algo = IRRA_A_star(chip=chip, iterations=10, simulated_annealing=False, A_star_rerouting=False)
    # irra_a_star_bfs_routing_algo.run()

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("final_output.csv")

    # --------------- IRRA A* (Simulated Annealing routing) ---------------------
    # used_algo_name = "IRRA A* (Simulated Annealing)"
    # irra_a_star_sim_anneal_routing_algo = IRRA_A_star(chip=chip, iterations=10, simulated_annealing=True, A_star_rerouting=False)
    # irra_a_star_sim_anneal_routing_algo.run()

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("final_output.csv")

    # ---------------------- IRRA A* (A* routing) -------------------------------
    # used_algo_name = "IRRA A* (A* routing)"
    # irra_a_star_a_star_routing_algo = IRRA_A_star(chip=chip, iterations=10, simulated_annealing=False, A_star_rerouting=True)
    # irra_a_star_a_star_routing_algo.run()

    # chip.show_grid(image_filename=None, algorithm_name=used_algo_name)
    # chip.save_output("final_output.csv")

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