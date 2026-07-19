from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "EQUITY_L.csv"
OUTPUT_FILE = DATA_DIR / "nse_symbols.csv"

def generate_symbols():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"{INPUT_FILE} not found!")

    df = pd.read_csv(INPUT_FILE)

    # NSE symbol column
    symbol_col = "SYMBOL"
    name_col = "NAME OF COMPANY"

    if symbol_col not in df.columns:
        raise Exception(f"Column '{symbol_col}' not found.")

    symbols = pd.DataFrame({
        "symbol": df[symbol_col].astype(str) + ".NS",
        "name": df[name_col].astype(str)
    })

    symbols = symbols.sort_values("symbol")

    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    symbols.to_csv(OUTPUT_FILE, index=False)

    print(f"✅ Generated {len(symbols)} symbols")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_symbols()