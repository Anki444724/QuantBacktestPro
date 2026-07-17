import pandas as pd

# NSE वाली original file
df = pd.read_csv("EQUITY_L.csv")

# नया dataframe
new_df = pd.DataFrame({
    "ticker": df["SYMBOL"] + ".NS",
    "name": df["NAME OF COMPANY"]
})

# Save
new_df.to_csv("nse_symbols.csv", index=False)

print("Done! Total Stocks:", len(new_df))