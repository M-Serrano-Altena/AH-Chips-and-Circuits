from src.algorithms.utils import save_object_to_json_file, load_object_from_json_file, add_missing_extension
import matplotlib.pyplot as plt
import os

output_file = 'output/parameter_research/chip2w7_offset_test.json'
results = load_object_from_json_file(output_file)
offsets = []
median_cost = []

for result in results:
    offsets.append(result["offset"])
    median_cost.append(result["median_cost"])

print(offsets)
print(median_cost)

output_base_name, _ = os.path.splitext(output_file)
plot_save_path = add_missing_extension(output_base_name, '.png')

plt.title("Median cost with different offsets")
plt.plot(offsets, median_cost)
plt.savefig(plot_save_path)
