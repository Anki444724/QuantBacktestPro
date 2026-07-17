from pathlib import Path
import pandas as pd

CSV_FILE = Path(__file__).parent / "../data/nse_symbols.csv"
CSV_FILE = CSV_FILE.resolve()

print(CSV_FILE)

df = pd.read_csv(CSV_FILE)

ALL_SYMBOLS = df.to_dict(orient="records")