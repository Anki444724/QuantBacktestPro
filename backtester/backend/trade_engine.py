from __future__ import annotations

import math


class TradeEngine:

    @staticmethod
    def extract_trades(portfolio):

        trades = []

        records = portfolio.trades.records_readable

        for _, row in records.iterrows():

            trades.append(
                {
                    "entry_date": str(row["Entry Timestamp"]),
                    "exit_date": str(row["Exit Timestamp"]),
                    "entry_price": float(row["Avg Entry Price"]),
                    "exit_price": float(row["Avg Exit Price"]),
                    "pnl": float(row["PnL"]),
                    "return_pct": float(row["Return"]),
                }
            )

        return trades

    @staticmethod
    def statistics(trades):

        if len(trades) == 0:

            return {
                "winning_trades": 0,
                "losing_trades": 0,
                "best_trade": 0.0,
                "worst_trade": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "expectancy": 0.0,
            }

        wins = [t["pnl"] for t in trades if t["pnl"] > 0]
        losses = [t["pnl"] for t in trades if t["pnl"] < 0]

        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))

        profit_factor = (
            gross_profit / gross_loss
            if gross_loss > 0
            else 0.0
        )

        expectancy = (
            sum(t["pnl"] for t in trades)
            / len(trades)
        )

        return {
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "best_trade": max(wins) if wins else 0.0,
            "worst_trade": min(losses) if losses else 0.0,
            "avg_win": (
                sum(wins) / len(wins)
                if wins
                else 0.0
            ),
            "avg_loss": (
                sum(losses) / len(losses)
                if losses
                else 0.0
            ),
            "profit_factor": (
                profit_factor
                if math.isfinite(profit_factor)
                else 0.0
            ),
            "expectancy": expectancy,
        }