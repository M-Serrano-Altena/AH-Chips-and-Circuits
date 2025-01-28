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
    Creates and saves a heatmap based on simulated annealing results.
    
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

    output_image_path = os.path.join(plot_save_base_dir, plot_save_name)

    print(output_image_path)
    # save figure
    plt.savefig(output_image_path, dpi=300)
