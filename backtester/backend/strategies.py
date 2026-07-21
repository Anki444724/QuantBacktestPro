from __future__ import annotations
from engines.custom_strategy import CustomStrategy
from typing import Dict, Tuple

import pandas as pd
import vectorbt as vbt


class StrategyRunner:

    @staticmethod
    def sma(df: pd.DataFrame, params: Dict):

        fast = int(params.get("fast", 20))
        slow = int(params.get("slow", 50))

        fast_ma = vbt.MA.run(
            df["Close"],
            fast,
        )

        slow_ma = vbt.MA.run(
            df["Close"],
            slow,
        )

        entries = fast_ma.ma_crossed_above(
            slow_ma
        )

        exits = fast_ma.ma_crossed_below(
            slow_ma
        )

        return entries, exits

    @staticmethod
    def ema(df: pd.DataFrame, params: Dict):

        fast = int(params.get("fast", 20))
        slow = int(params.get("slow", 50))

        fast_ma = vbt.MA.run(
            df["Close"],
            fast,
            ewm=True,
        )

        slow_ma = vbt.MA.run(
            df["Close"],
            slow,
            ewm=True,
        )

        entries = fast_ma.ma_crossed_above(
            slow_ma
        )

        exits = fast_ma.ma_crossed_below(
            slow_ma
        )

        return entries, exits

    @staticmethod
    def rsi(df: pd.DataFrame, params: Dict):

        period = int(params.get("period", 14))

        buy = float(params.get("buy", 30))

        sell = float(params.get("sell", 70))

        rsi = vbt.RSI.run(
            df["Close"],
            window=period,
        )

        entries = rsi.rsi < buy

        exits = rsi.rsi > sell

        return entries, exits

    @staticmethod
    def run(
        strategy: str,
        df: pd.DataFrame,
        params: Dict,
    ) -> Tuple:

        if strategy == "sma_cross":
            return StrategyRunner.sma(df, params)

        if strategy == "ema_cross":
            return StrategyRunner.ema(df, params)

        if strategy == "rsi":
            return StrategyRunner.rsi(df, params)
        if strategy == "custom":
         return CustomStrategy.run(
        df=df,
        config=params,
    )

        raise ValueError(f"Unknown strategy: {strategy}")