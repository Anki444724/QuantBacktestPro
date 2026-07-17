"""
Market Data Service

Priority
1. Cache
2. Yahoo Finance
3. Synthetic Fallback
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


# ============================================================
# CACHE
# ============================================================

CACHE_DIR = Path(__file__).parent / ".cache" / "market_data"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(symbol: str, start: str, end: str, interval: str):
    return hashlib.md5(
        f"{symbol.upper()}|{start}|{end}|{interval}".encode()
    ).hexdigest()


def _cache_path(key):
    return CACHE_DIR / f"{key}.parquet"


def _meta_path(key):
    return CACHE_DIR / f"{key}.json"


# ============================================================
# SYNTHETIC DATA
# ============================================================

def _generate_synthetic_data(symbol, start, end, interval="1d"):

    freq_map = {
        "1d": "B",
        "1wk": "W",
        "1mo": "ME",
        "1h": "H",
        "30m": "30min",
        "15m": "15min",
        "5m": "5min",
        "1m": "min",
    }

    freq = freq_map.get(interval, "B")

    dates = pd.date_range(
        start=start,
        end=end,
        freq=freq,
    )

    np.random.seed(abs(hash(symbol)) % (2 ** 32))

    price = 100 * np.exp(
        np.cumsum(
            np.random.normal(
                0.0003,
                0.015,
                len(dates),
            )
        )
    )

    high = price * (
        1 + np.random.rand(len(dates)) * 0.02
    )

    low = price * (
        1 - np.random.rand(len(dates)) * 0.02
    )

    open_price = (high + low) / 2

    volume = np.random.randint(
        500000,
        5000000,
        len(dates),
    )

    df = pd.DataFrame(
        {
            "Open": open_price,
            "High": high,
            "Low": low,
            "Close": price,
            "Volume": volume,
        },
        index=dates,
    )

    df._synthetic = True

    return df
# ============================================================
# FETCH DATA
# ============================================================

def fetch_data(
    symbol: str,
    start: str,
    end: str,
    interval: str = "1d",
    use_cache: bool = True,
):

    print("=== fetch_data called ===")

    symbol = symbol.upper().strip()

    key = _cache_key(symbol, start, end, interval)

    cache_file = _cache_path(key)
    meta_file = _meta_path(key)

    # --------------------------------------------------------
    # LOAD CACHE
    # --------------------------------------------------------

    if use_cache and cache_file.exists() and meta_file.exists():

        try:

            df = pd.read_parquet(cache_file)

            with open(meta_file, "r") as f:
                meta = json.load(f)

            df.index = pd.to_datetime(df.index)

            df._synthetic = meta.get("synthetic", False)

            print("Loaded From Cache")

            return df

        except Exception:
            pass

    df = None
    is_synthetic = False

    # --------------------------------------------------------
    # YAHOO FINANCE
    # --------------------------------------------------------

    try:

        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "60m",
            "1d": "1d",
            "1wk": "1wk",
            "1mo": "1mo",
        }

        yf_interval = interval_map.get(interval, "1d")

        yahoo_symbol = symbol

        if not yahoo_symbol.endswith(".NS") and not yahoo_symbol.endswith(".BO"):
            yahoo_symbol += ".NS"

        print("Downloading:", yahoo_symbol)

        df = yf.download(
            yahoo_symbol,
            start=start,
            end=end,
            interval=yf_interval,
            auto_adjust=True,
            progress=False,
            threads=False,
            group_by="column",
            multi_level_index=False,
        )

        if df is not None and not df.empty:

            print("Yahoo Download Success")

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df[
                [
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                ]
            ].copy()

            df.index = pd.to_datetime(df.index)

            try:
                df.index = df.index.tz_localize(None)
            except Exception:
                pass

            print("Rows:", len(df))

        else:

            print("Yahoo returned empty dataframe")

            df = None

    except Exception as e:

        print("Yahoo Error:", e)

        df = None
            # --------------------------------------------------------
    # SYNTHETIC FALLBACK
    # --------------------------------------------------------

    if df is None or df.empty:

        print("Using Synthetic Data")

        df = _generate_synthetic_data(
            symbol,
            start,
            end,
            interval,
        )

        is_synthetic = True

    # --------------------------------------------------------
    # SAVE CACHE
    # --------------------------------------------------------

    try:

        df.to_parquet(cache_file)

        with open(meta_file, "w") as f:

            json.dump(
                {
                    "synthetic": is_synthetic,
                    "cached_at": datetime.utcnow().isoformat(),
                },
                f,
            )

    except Exception as e:

        print("Cache Save Error:", e)

    df._synthetic = is_synthetic

    return df


# ============================================================
# CLEAR CACHE
# ============================================================

def clear_cache():

    removed = 0

    for file in CACHE_DIR.glob("*"):

        try:
            file.unlink()
            removed += 1
        except Exception:
            pass

    return removed


# ============================================================
# DATA INFO
# ============================================================

def get_data_info(
    symbol: str,
    start: str,
    end: str,
    interval: str = "1d",
):

    df = fetch_data(
        symbol=symbol,
        start=start,
        end=end,
        interval=interval,
    )

    return {
        "symbol": symbol.upper(),
        "start": str(df.index[0].date()) if len(df) else None,
        "end": str(df.index[-1].date()) if len(df) else None,
        "rows": len(df),
        "columns": list(df.columns),
        "source": (
            "synthetic"
            if getattr(df, "_synthetic", False)
            else "yahoo"
        ),
    }