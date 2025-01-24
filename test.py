from src.algorithms.utils import save_object_to_json_file, load_object_from_json_file
import matplotlib.pyplot as plt

output_file = 'output/parameter_research/chip2w7_offset_test.json'
results = load_object_from_json_file(output_file)
offsets = []
median_cost = []

for result in results:
    offsets.append(result["offset"])
    median_cost.append(result["median_cost"])

print(offsets)
print(median_cost)

plt.title("Median cost with different offsets")
plt.plot(offsets, median_cost)
plt.savefig("test.png")
