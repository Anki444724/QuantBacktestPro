from pathlib import Path
import pandas as pd

CSV_FILE = Path(__file__).parent / "data" / "nse_symbols.csv"

df = pd.read_csv(CSV_FILE)

ALL_SYMBOLS = df.to_dict(orient="records")