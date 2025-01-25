from src.classes.chip import load_chip_from_csv

output_csv_file = r"output/csv/output.csv"
chip = load_chip_from_csv(output_csv_file)

chip.show_grid()