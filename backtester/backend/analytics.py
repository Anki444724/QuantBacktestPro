"""
Professional analytics computations for backtest results.

All functions accept simple Python primitives / lists so they can be called
from either built-in or custom backtest results.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


def _to_series(daily_returns: List[Dict[str, Any]]) -> pd.Series:
    """Convert list of {date, return} dicts to a pandas Series."""
    if not daily_returns:
        return pd.Series(dtype=float)
    df = pd.DataFrame(daily_returns)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    return df["return"] / 100.0  # convert percent back to decimal


def _to_equity_series(equity_curve):
    if not equity_curve:
        return pd.Series(dtype=float)

    df = pd.DataFrame(equity_curve)

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()

    if "equity" in df.columns:
        return df["equity"]

    if "value" in df.columns:
        return df["value"]

    raise Exception(f"Columns found: {df.columns.tolist()}")


def compute_equity_curve(equity_curve: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return equity_curve


def compute_drawdown_curve(equity_curve: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    equity = _to_equity_series(equity_curve)
    if equity.empty:
        return []
    peak = equity.expanding(min_periods=1).max()
    dd = (equity - peak) / peak * 100
    return [{"date": d.strftime("%Y-%m-%d"), "value": float(v)} for d, v in dd.items()]


def compute_monthly_returns_heatmap(daily_returns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a year x month matrix suitable for a heatmap."""
    returns = _to_series(daily_returns)
    if returns.empty:
        return {"years": [], "months": [], "data": []}
    monthly = (1 + returns).resample("ME").prod() - 1
    monthly.index = monthly.index.to_period("M")
    years = sorted(monthly.index.year.unique().tolist())
    months = list(range(1, 13))
    data = []
    for year in years:
        row = []
        for month in months:
            mask = (monthly.index.year == year) & (monthly.index.month == month)
            vals = monthly[mask]
            row.append(float(vals.iloc[0]) * 100 if len(vals) else None)
        data.append(row)
    return {"years": [str(y) for y in years], "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], "data": data}


def compute_rolling_sharpe(daily_returns: List[Dict[str, Any]], window: int = 252) -> List[Dict[str, Any]]:
    returns = _to_series(daily_returns)
    if returns.empty:
        return []
    rolling_mean = returns.rolling(window=window).mean() * 252
    rolling_std = returns.rolling(window=window).std() * np.sqrt(252)
    sharpe = rolling_mean / rolling_std
    return [{"date": d.strftime("%Y-%m-%d"), "value": float(v) if not pd.isna(v) else None} for d, v in sharpe.items()]


def compute_rolling_returns(equity_curve: List[Dict[str, Any]], window: int = 90) -> List[Dict[str, Any]]:
    equity = _to_equity_series(equity_curve)
    if equity.empty:
        return []
    rolling = (equity / equity.shift(window) - 1) * 100
    return [{"date": d.strftime("%Y-%m-%d"), "value": float(v) if not pd.isna(v) else None} for d, v in rolling.items()]


def compute_annual_returns(daily_returns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    returns = _to_series(daily_returns)
    if returns.empty:
        return []
    annual = (1 + returns).resample("YE").prod() - 1
    return [{"year": str(d.year), "return": float(v) * 100} for d, v in annual.items()]


def compute_trade_distribution(trades: List[Dict[str, Any]]) -> Dict[str, int]:
    winning = sum(1 for t in trades if t.get("pnl", 0) >= 0)
    losing = len(trades) - winning
    return {"winning": winning, "losing": losing}


def compute_return_distribution(trades: List[Dict[str, Any]]) -> Dict[str, List]:
    returns = [t.get("return_pct", 0) for t in trades]
    if not returns:
        return {"labels": [], "values": []}
    bins = [-np.inf, -10, -7, -5, -3, -1, 1, 3, 5, 7, 10, np.inf]
    labels = ["<-10%", "-10% to -7%", "-7% to -5%", "-5% to -3%", "-3% to -1%", "-1% to 1%", "1% to 3%", "3% to 5%", "5% to 7%", "7% to 10%", ">10%"]
    series = pd.Series(returns)
    counts = pd.cut(series, bins=bins, labels=labels).value_counts().sort_index()
    return {"labels": labels, "values": [int(counts.get(l, 0)) for l in labels]}


def _parse_date(d: Any) -> Optional[datetime]:
    if isinstance(d, datetime):
        return d
    if isinstance(d, str):
        try:
            return datetime.strptime(d.split("T")[0], "%Y-%m-%d")
        except Exception:
            return None
    return None


def compute_holding_time_analysis(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    durations = []
    win_durations = []
    loss_durations = []
    for t in trades:
        entry = _parse_date(t.get("entry_date"))
        exit_d = _parse_date(t.get("exit_date"))
        if entry and exit_d:
            days = (exit_d - entry).days
            durations.append(days)
            if t.get("pnl", 0) >= 0:
                win_durations.append(days)
            else:
                loss_durations.append(days)

    if not durations:
        return {"avg": 0, "avg_win": 0, "avg_loss": 0, "max": 0, "min": 0, "distribution": {"labels": [], "values": []}}

    bins = [0, 1, 3, 5, 10, 20, 40, 60, 90, 180, 365, np.inf]
    labels = ["0-1d", "1-3d", "3-5d", "5-10d", "10-20d", "20-40d", "40-60d", "60-90d", "90-180d", "180-365d", ">365d"]
    counts = pd.cut(pd.Series(durations), bins=bins, labels=labels, right=False).value_counts().sort_index()

    return {
        "avg": round(float(np.mean(durations)), 1),
        "avg_win": round(float(np.mean(win_durations)) if win_durations else 0, 1),
        "avg_loss": round(float(np.mean(loss_durations)) if loss_durations else 0, 1),
        "max": int(max(durations)),
        "min": int(min(durations)),
        "distribution": {"labels": labels, "values": [int(counts.get(l, 0)) for l in labels]},
    }


def compute_win_loss_streak(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not trades:
        return {"longest_win": 0, "longest_loss": 0, "current_streak": 0, "current_type": "none"}

    outcomes = ["win" if t.get("pnl", 0) >= 0 else "loss" for t in trades]
    longest_win = 0
    longest_loss = 0
    current_win = 0
    current_loss = 0
    for o in outcomes:
        if o == "win":
            current_win += 1
            current_loss = 0
            longest_win = max(longest_win, current_win)
        else:
            current_loss += 1
            current_win = 0
            longest_loss = max(longest_loss, current_loss)

    current_type = "win" if current_win > 0 else ("loss" if current_loss > 0 else "none")
    current_streak = max(current_win, current_loss)

    return {
        "longest_win": longest_win,
        "longest_loss": longest_loss,
        "current_streak": current_streak,
        "current_type": current_type,
    }


def compute_risk_analysis(daily_returns: List[Dict[str, Any]]) -> Dict[str, Any]:
    returns = _to_series(daily_returns)
    if returns.empty:
        return {
            "volatility_annual": 0.0,
            "var_95": 0.0,
            "cvar_95": 0.0,
            "skewness": 0.0,
            "kurtosis": 0.0,
            "max_consecutive_loss_days": 0,
            "downside_deviation": 0.0,
        }

    var_95 = float(np.percentile(returns, 5)) * 100
    cvar_95 = float(returns[returns <= np.percentile(returns, 5)].mean()) * 100
    downside = returns[returns < 0]
    downside_dev = float(downside.std() * np.sqrt(252)) * 100 if len(downside) else 0.0

    # max consecutive loss days
    loss_days = returns < 0
    max_loss_streak = 0
    current = 0
    for is_loss in loss_days:
        if is_loss:
            current += 1
            max_loss_streak = max(max_loss_streak, current)
        else:
            current = 0

    return {
        "volatility_annual": float(returns.std() * np.sqrt(252)) * 100,
        "var_95": var_95,
        "cvar_95": cvar_95,
        "skewness": float(returns.skew()),
        "kurtosis": float(returns.kurtosis()),
        "max_consecutive_loss_days": max_loss_streak,
        "downside_deviation": downside_dev,
    }


def compute_all_analytics(
    equity_curve: List[Dict[str, Any]],
    daily_returns: List[Dict[str, Any]],
    trades: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute the full professional analytics suite."""
    return {
        "equity_curve": compute_equity_curve(equity_curve),
        "drawdown_curve": compute_drawdown_curve(equity_curve),
        "monthly_returns_heatmap": compute_monthly_returns_heatmap(daily_returns),
        "rolling_sharpe_252": compute_rolling_sharpe(daily_returns, window=252),
        "rolling_sharpe_90": compute_rolling_sharpe(daily_returns, window=90),
        "rolling_returns_90": compute_rolling_returns(equity_curve, window=90),
        "rolling_returns_252": compute_rolling_returns(equity_curve, window=252),
        "annual_returns": compute_annual_returns(daily_returns),
        "trade_distribution": compute_trade_distribution(trades),
        "return_distribution": compute_return_distribution(trades),
        "holding_time_analysis": compute_holding_time_analysis(trades),
        "win_loss_streak": compute_win_loss_streak(trades),
        "risk_analysis": compute_risk_analysis(daily_returns),
    }
