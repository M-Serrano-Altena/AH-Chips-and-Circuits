import json
import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

def create_sa_heatmap(input_json_path, output_image_path="output/img/heatmap.png", input = "Method"):
    """
    Creates and saves a heatmap based on simulated annealing results.
    
    """

    os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
    
    # load json
    with open(input_json_path, "r") as f:
        data = json.load(f)

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
    plt.title(f"Simulated Annealing Heatmap ({input} Input, Chip 2w7, n=250)", fontsize=14)
    plt.xlabel("Alpha")
    plt.ylabel("Temperature")

    plt.tight_layout()

    # save figure
    plt.savefig(output_image_path, dpi=300)
    plt.close() 

create_sa_heatmap("../output/parameter_research/chip2w7_annealing_PseudoRandom.json", "output/chip2w7_annealing_PseudoRandom_heatmap.png", input="PR")
create_sa_heatmap("../output/parameter_research/chip2w7_annealing_Astar.json", "output/chip2w7_annealing_Astar_heatmap.png", input="A*")