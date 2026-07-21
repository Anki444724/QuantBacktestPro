from typing import Dict, Tuple
import pandas as pd

from backtester.backend.engines.indicator_engine import IndicatorEngine
from backtester.backend.engines.rule_engine import RuleEngine


class CustomStrategy:

    @staticmethod
    def run(
        df: pd.DataFrame,
        config: Dict,
    ) -> Tuple[pd.Series, pd.Series]:

        indicator_values = {}

        # Calculate indicators
        for indicator in config.get("indicators", []):

            indicator_type = indicator["type"]
            indicator_name = indicator["name"]
            params = indicator.get("params", {})

            if indicator_type == "sma":
                indicator_values[indicator_name] = IndicatorEngine.sma(
                    df,
                    int(params["period"])
                )

            elif indicator_type == "ema":
                indicator_values[indicator_name] = IndicatorEngine.ema(
                    df,
                    int(params["period"])
                )

            elif indicator_type == "rsi":
                indicator_values[indicator_name] = IndicatorEngine.rsi(
                    df,
                    int(params["period"])
                )

        # Entry Rules
        entry_groups = config.get("entry_rules", [])

        if entry_groups:

            group = entry_groups[0]

            if group["conditions"]:

                condition = group["conditions"][0]

                entries = RuleEngine.evaluate_condition(
                    condition,
                    indicator_values,
                    df,
                )

            else:
                entries = pd.Series(False, index=df.index)

        else:
            entries = pd.Series(False, index=df.index)

        exits = pd.Series(False, index=df.index)

        return entries, exits