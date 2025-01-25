import csv
import re
import os
import tempfile
from src.classes.chip import load_chip_from_csv


csv_file = r"output/csv/output_chip_1_net_4.csv"
chip = load_chip_from_csv(csv_file)
chip.show_grid()