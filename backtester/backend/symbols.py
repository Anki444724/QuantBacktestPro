from pathlib import Path
import os
import pandas as pd

print("CURRENT DIR:", os.getcwd())
print("__FILE__:", __file__)

CSV_FILE = (Path(__file__).parent / "../data/nse_symbols.csv").resolve()
print("CSV PATH:", CSV_FILE)
print("CSV EXISTS:", CSV_FILE.exists())

df = pd.read_csv(CSV_FILE)
ALL_SYMBOLS = df.to_dict(orient="records")