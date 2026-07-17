import pandas as pd

symbols = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "SBIN.NS","LT.NS","BHARTIARTL.NS","ITC.NS","NTPC.NS",
    "POWERGRID.NS","BEL.NS","HAL.NS","COCHINSHIP.NS","PATELENG.NS",
    "ADANIPOWER.NS","NHPC.NS","TATAMOTORS.NS","TATASTEEL.NS",
    "AXISBANK.NS","KOTAKBANK.NS","BAJFINANCE.NS","HCLTECH.NS",
    "WIPRO.NS","ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS",
    "ULTRACEMCO.NS","TITAN.NS","ONGC.NS","BPCL.NS","INDIGO.NS",
    "PIDILITIND.NS","DLF.NS","LODHA.NS","IRCTC.NS","RVNL.NS",
    "IRFC.NS","BSE.NS","MCX.NS","PFC.NS","RECLTD.NS","CGPOWER.NS",
    "ABB.NS","SIEMENS.NS","CUMMINSIND.NS","POLYCAB.NS","KEI.NS"
]

rows = []

for symbol in symbols:
    rows.append({
        "ticker": symbol,
        "name": symbol.replace(".NS", "")
    })

df = pd.DataFrame(rows)
df.to_csv("nse_symbols.csv", index=False)

print(f"Saved {len(df)} symbols.")