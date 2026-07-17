from __future__ import annotations

import pandas as pd
import vectorbt as vbt


class PortfolioBuilder:

    @staticmethod
    def build(
        df: pd.DataFrame,
        entries,
        exits,
        initial_capital: float,
    ):

        portfolio = vbt.Portfolio.from_signals(
            close=df["Close"],
            entries=entries,
            exits=exits,
            init_cash=initial_capital,
            fees=0.001,
            slippage=0.0005,
            freq="1D",
        )

        return portfolio

    @staticmethod
    def equity_curve(portfolio):

        equity = []

        for idx, value in portfolio.value().items():

            equity.append(
                {
                    "date": str(idx.date()),
                    "equity": float(value),
                }
            )

        return equity

    @staticmethod
    def benchmark_curve(
        df: pd.DataFrame,
        initial_capital: float,
    ):

        shares = initial_capital / df["Close"].iloc[0]

        benchmark = df["Close"] * shares

        result = []

        for idx, value in benchmark.items():

            result.append(
                {
                    "date": str(idx.date()),
                    "value": float(value),
                }
            )

        return result

    @staticmethod
    def drawdown_curve(portfolio):

        running_max = portfolio.value().cummax()

        dd = (
            (
                portfolio.value()
                - running_max
            )
            / running_max
        ) * 100

        result = []

        for idx, value in dd.items():

            result.append(
                {
                    "date": str(idx.date()),
                    "value": float(value),
                }
            )

        return result