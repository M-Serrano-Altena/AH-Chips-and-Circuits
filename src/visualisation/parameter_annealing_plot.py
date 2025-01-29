import json
import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from src.algorithms.utils import load_object_from_json_file, extract_chip_id_net_id_from_file_name

def create_sim_anneal_heatmap(
    json_sim_anneal_data_filepath: str, 
    solution_input: str, 
    chip_id: int|None=None, 
    net_id: int|None=None, 
    plot_save_name: str|None=None, 
    plot_save_base_dir: str="results/latest/experiment_plots"     
) -> None:
    """
    Creates and saves a heatmap based on simulated annealing results, visualizing the relationship between 
    temperature and alpha values with corresponding median costs and standard deviation. The results are 
    plotted and saved as a PNG file.

    Args:
        json_sim_anneal_data_filepath (str): The path to the JSON file containing simulated annealing results.
        solution_input (str): The input solution type ('PR' for Pseudo Random or 'A*' for A* input to IRRA algorithm).
        chip_id (int, optional): The chip ID for the routing experiment. If not provided, it is extracted from the file name.
        net_id (int, optional): The netlist ID for the routing experiment. If not provided, it is extracted from the file name.
        plot_save_name (str, optional): The name of the file to save the heatmap plot as. If not provided, a default name is used.
        plot_save_base_dir (str, optional): The directory where the heatmap plot will be saved. Defaults to "results/latest/experiment_plots".

    Raises:
        ValueError: If the `solution_input` is not one of 'PR' or 'A*'.

    Returns:
        None: The function does not return any values. It saves the heatmap plot as a PNG file in the specified directory.
    """
    if chip_id is None or net_id is None:
        chip_id, net_id = extract_chip_id_net_id_from_file_name(json_sim_anneal_data_filepath)

    if solution_input not in ["PR", "A*"]:
        raise ValueError("solution_input must be either 'PR' or 'A*'")

    # load json
    data = load_object_from_json_file(json_sim_anneal_data_filepath)
    iterations = len(data[0]["all_costs"])

    # convert dataframe
    df = pd.DataFrame(data)

    # create pivot tables
    median_pivot = df.pivot(index="temperature", columns="alpha", values="median_cost")
    stdev_pivot  = df.pivot(index="temperature", columns="alpha", values="stdev_cost")

    median_pivot.sort_index(ascending=True, inplace=True)
    stdev_pivot.sort_index(ascending=True, inplace=True)

    # annotation
    annotation = np.empty(median_pivot.shape, dtype=object)
    for i in range(median_pivot.shape[0]):
        for j in range(median_pivot.shape[1]):
            median_value = median_pivot.iloc[i, j]
            stdev_value  = stdev_pivot.iloc[i, j]
            annotation[i, j] = (f"Median: {int(median_value)}\n"
                                f"Std: {stdev_value:.1f}\n")

    # plot
    plt.figure(figsize=(10, 7))
    sns.set_style("whitegrid")

    ax = sns.heatmap(
        median_pivot, 
        annot=annotation,
        fmt="",          
        cmap="flare", 
        cbar_kws={"label": "Median Cost"}
    )

    ax.invert_yaxis()

    # add labels
    plt.title(f"Simulated Annealing Heatmap ({solution_input} Input, Chip {chip_id} Net {net_id}, n={iterations})", fontsize=14)
    plt.xlabel("Alpha")
    plt.ylabel("Temperature")

    plt.tight_layout()

    solution_input = solution_input.replace("*", "star").lower()

    if plot_save_name is None:
        plot_save_name = f"chip{chip_id}w{net_id}_irra_{solution_input}_sim_anneal_heatmap.png"

    os.makedirs(plot_save_base_dir, exist_ok=True)
    output_image_path = os.path.join(plot_save_base_dir, plot_save_name)

    # save figure
    plt.savefig(output_image_path, dpi=300)
    plt.clf()
