import vectorbt as vbt
import pandas as pd


class IndicatorEngine:

    @staticmethod
    def sma(df: pd.DataFrame, period: int):
        return vbt.MA.run(df["Close"], period).ma

    @staticmethod
    def ema(df: pd.DataFrame, period: int):
        return vbt.MA.run(
            df["Close"],
            period,
            ewm=True
        ).ma

    @staticmethod
    def rsi(df: pd.DataFrame, period: int):
        return vbt.RSI.run(
            df["Close"],
            window=period
        ).rsi