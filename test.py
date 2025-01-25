import csv
import re
import os
import tempfile
from src.classes.chip import load_chip_from_csv
from math import perm


file = "output/csv/optimized_output_chip_2_net_7.csv"
chip = load_chip_from_csv(file)

chip.show_grid()