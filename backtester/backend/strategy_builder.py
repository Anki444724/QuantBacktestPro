"""
No-code strategy builder engine.

Users define strategies as JSON:
- A list of indicators (SMA, EMA, RSI, MACD, Supertrend, VWAP, Bollinger, ATR, ADX)
- Entry/exit rules built from AND/OR condition groups
- Risk management: stop loss, take profit, trailing stop

The engine compiles this into vectorbt signals and runs a backtest.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
import vectorbt as vbt
from pydantic import BaseModel, Field, field_validator, model_validator

from data_service import fetch_data


# ---------------------------------------------------------------------------
# Pydantic schema
# ---------------------------------------------------------------------------

class IndicatorConfig(BaseModel):
    type: Literal["sma", "ema", "rsi", "macd", "supertrend", "vwap", "bbands", "atr", "adx"]
    name: str = Field(..., pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    params: Dict[str, Any] = Field(default_factory=dict)


class Operand(BaseModel):
    type: Literal["indicator", "value", "ohlc"]
    name: Optional[str] = None  # indicator output name or ohlc field
    value: Optional[float] = None

    @model_validator(mode="after")
    def check_consistency(self):
        if self.type == "value" and self.value is None:
            raise ValueError("Value operand must have a value")
        if self.type in ("indicator", "ohlc") and not self.name:
            raise ValueError(f"{self.type} operand must have a name")
        return self


class Condition(BaseModel):
    left: Operand
    op: Literal[">", "<", ">=", "<=", "==", "crosses_above", "crosses_below"]
    right: Operand


class ConditionGroup(BaseModel):
    operator: Literal["AND", "OR"]
    conditions: List[Condition]


class RiskConfig(BaseModel):
    type: Literal["percent"] = "percent"
    value: float = Field(0.0, ge=0)


class CustomStrategy(BaseModel):
    name: str = Field(..., min_length=1)
    indicators: List[IndicatorConfig] = Field(..., min_length=1)
    entry_rules: List[ConditionGroup] = Field(..., min_length=1)
    exit_rules: List[ConditionGroup] = Field(default_factory=list)
    stop_loss: Optional[RiskConfig] = None
    take_profit: Optional[RiskConfig] = None
    trailing_stop: Optional[RiskConfig] = None
    initial_capital: float = Field(100_000.0, ge=1_000)

    @field_validator("indicators")
    @classmethod
    def unique_indicator_names(cls, v):
        names = [ind.name for ind in v]
        if len(names) != len(set(names)):
            raise ValueError("Indicator names must be unique")
        return v


# ---------------------------------------------------------------------------
# Indicator computation
# ---------------------------------------------------------------------------

def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    return pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    return _true_range(high, low, close).rolling(window=period, min_periods=1).mean()


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    tr = _true_range(high, low, close)
    atr = tr.rolling(window=period, min_periods=1).mean()
    plus_di = 100 * plus_dm.rolling(window=period, min_periods=1).mean() / atr
    minus_di = 100 * minus_dm.rolling(window=period, min_periods=1).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.rolling(window=period, min_periods=1).mean()


def _supertrend(high: pd.Series, low: pd.Series, close: pd.Series, period: int, multiplier: float) -> Dict[str, pd.Series]:
    hl2 = (high + low) / 2
    atr = _atr(high, low, close, period)
    upper = hl2 + multiplier * atr
    lower = hl2 - multiplier * atr

    st = pd.Series(np.nan, index=close.index)
    direction = pd.Series(1, index=close.index)

    for i in range(len(close)):
        if i == 0:
            st.iloc[i] = upper.iloc[i]
            direction.iloc[i] = -1
            continue
        if close.iloc[i] > st.iloc[i - 1]:
            direction.iloc[i] = 1
            st.iloc[i] = max(lower.iloc[i], st.iloc[i - 1]) if not pd.isna(st.iloc[i - 1]) else lower.iloc[i]
        else:
            direction.iloc[i] = -1
            st.iloc[i] = min(upper.iloc[i], st.iloc[i - 1]) if not pd.isna(st.iloc[i - 1]) else upper.iloc[i]

    return {"value": st, "direction": direction}


def compute_indicators(df: pd.DataFrame, indicators: List[IndicatorConfig]) -> Dict[str, pd.Series]:
    """Compute all configured indicators and return a flat map of output series."""
    outputs: Dict[str, pd.Series] = {}
    outputs["open"] = df["Open"]
    outputs["high"] = df["High"]
    outputs["low"] = df["Low"]
    outputs["close"] = df["Close"]
    outputs["volume"] = df["Volume"]

    for ind in indicators:
        params = ind.params
        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        if ind.type == "sma":
            outputs[ind.name] = close.rolling(window=int(params.get("period", 20)), min_periods=1).mean()
        elif ind.type == "ema":
            outputs[ind.name] = close.ewm(span=int(params.get("period", 20)), adjust=False).mean()
        elif ind.type == "rsi":
            rsi = vbt.RSI.run(close, window=int(params.get("period", 14)))
            outputs[ind.name] = rsi.rsi
        elif ind.type == "macd":
            macd = vbt.MACD.run(
                close,
                fast_window=int(params.get("fast", 12)),
                slow_window=int(params.get("slow", 26)),
                signal_window=int(params.get("signal", 9)),
            )
            outputs[f"{ind.name}_macd"] = macd.macd
            outputs[f"{ind.name}_signal"] = macd.signal
            outputs[f"{ind.name}_hist"] = macd.hist
        elif ind.type == "bbands":
            bb = vbt.BBANDS.run(close, window=int(params.get("period", 20)), alpha=float(params.get("std", 2.0)))
            outputs[f"{ind.name}_upper"] = bb.upper
            outputs[f"{ind.name}_middle"] = bb.middle
            outputs[f"{ind.name}_lower"] = bb.lower
        elif ind.type == "atr":
            atr = vbt.ATR.run(high, low, close, window=int(params.get("period", 14)))
            outputs[ind.name] = atr.atr
        elif ind.type == "adx":
            outputs[ind.name] = _adx(high, low, close, int(params.get("period", 14)))
        elif ind.type == "supertrend":
            st = _supertrend(high, low, close, int(params.get("period", 10)), float(params.get("multiplier", 3.0)))
            outputs[f"{ind.name}"] = st["value"]
            outputs[f"{ind.name}_direction"] = st["direction"]
        elif ind.type == "vwap":
            outputs[ind.name] = (close * volume).cumsum() / volume.cumsum()

    return outputs


# ---------------------------------------------------------------------------
# Condition evaluation
# ---------------------------------------------------------------------------

def _resolve_operand(op: Operand, outputs: Dict[str, pd.Series], index: pd.Index) -> pd.Series:
    if op.type == "value":
        return pd.Series(op.value, index=index)
    if op.type == "ohlc":
        field = op.name.lower()
        if field not in outputs:
            raise ValueError(f"Unknown OHLC field: {op.name}")
        return outputs[field]
    # indicator
    if op.name not in outputs:
        raise ValueError(f"Unknown indicator output: {op.name}")
    return outputs[op.name]


def _crosses_above(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a > b) & (a.shift(1) <= b.shift(1))


def _crosses_below(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a < b) & (a.shift(1) >= b.shift(1))


def evaluate_condition(condition: Condition, outputs: Dict[str, pd.Series], index: pd.Index) -> pd.Series:
    left = _resolve_operand(condition.left, outputs, index)
    right = _resolve_operand(condition.right, outputs, index)

    if condition.op == ">":
        return left > right
    if condition.op == "<":
        return left < right
    if condition.op == ">=":
        return left >= right
    if condition.op == "<=":
        return left <= right
    if condition.op == "==":
        return np.isclose(left, right)
    if condition.op == "crosses_above":
        return _crosses_above(left, right)
    if condition.op == "crosses_below":
        return _crosses_below(left, right)
    raise ValueError(f"Unknown operator: {condition.op}")


def evaluate_group(group: ConditionGroup, outputs: Dict[str, pd.Series], index: pd.Index) -> pd.Series:
    if not group.conditions:
        return pd.Series(True, index=index)
    result = evaluate_condition(group.conditions[0], outputs, index)
    for condition in group.conditions[1:]:
        next_cond = evaluate_condition(condition, outputs, index)
        if group.operator == "AND":
            result = result & next_cond
        else:
            result = result | next_cond
    return result


def evaluate_rules(groups: List[ConditionGroup], outputs: Dict[str, pd.Series], index: pd.Index) -> pd.Series:
    if not groups:
        return pd.Series(False, index=index)
    result = evaluate_group(groups[0], outputs, index)
    for group in groups[1:]:
        result = result & evaluate_group(group, outputs, index)
    return result


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

@dataclass
class BuiltStrategyResult:
    id: str
    name: str
    symbol: str
    start: str
    end: str
    interval: str
    status: str
    error: Optional[str] = None
    total_return: float = 0.0
    annual_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    trades: List[Dict[str, Any]] = field(default_factory=list)


def run_custom_strategy(
    strategy: CustomStrategy,
    symbol: str,
    start: str,
    end: str,
    interval: str = "1d",
    backtest_id: Optional[str] = None,
) -> Dict[str, Any]:
    result_id = backtest_id or datetime.utcnow().strftime("bt_%Y%m%d%H%M%S")

    result = {
        "id": result_id,
        "name": strategy.name,
        "symbol": symbol.upper(),
        "start": start,
        "end": end,
        "interval": interval,
        "status": "completed",
        "error": None,
        "strategy_config": strategy.model_dump(),
    }

    try:
        df = fetch_data(symbol, start, end, interval)
        close = df["Close"]
        result["data_source"] = "synthetic" if getattr(df, "_synthetic", False) else "yahoo"

        outputs = compute_indicators(df, strategy.indicators)
        entries = evaluate_rules(strategy.entry_rules, outputs, close.index)
        exits = evaluate_rules(strategy.exit_rules, outputs, close.index)

        # Remove conflicts
        conflict = entries & exits
        entries = entries & ~conflict
        exits = exits & ~conflict

        freq_map = {"1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min", "1h": "1H", "1d": "1D", "1wk": "1W", "1mo": "1M"}
        freq = freq_map.get(interval, "1D")

        # Risk management (percent only)
        sl_stop = strategy.stop_loss.value / 100 if strategy.stop_loss and strategy.stop_loss.value > 0 else None
        tp_stop = strategy.take_profit.value / 100 if strategy.take_profit and strategy.take_profit.value > 0 else None
        sl_trail = strategy.trailing_stop.value / 100 if strategy.trailing_stop and strategy.trailing_stop.value > 0 else None

        pf = vbt.Portfolio.from_signals(
            close,
            entries=entries,
            exits=exits,
            init_cash=strategy.initial_capital,
            fees=0.001,
            slippage=0.001,
            freq=freq,
            direction="longonly",
            sl_stop=sl_stop,
            tp_stop=tp_stop,
            sl_trail=sl_trail,
        )

        result["total_return"] = float(pf.total_return()) * 100
        result["annual_return"] = float(pf.annualized_return()) * 100
        result["max_drawdown"] = float(pf.max_drawdown()) * 100
        result["sharpe_ratio"] = float(pf.sharpe_ratio())
        result["total_trades"] = int(pf.trades.count())
        result["winning_trades"] = int(pf.trades.winning.count())
        result["losing_trades"] = int(pf.trades.losing.count())
        result["win_rate"] = float(pf.trades.win_rate()) * 100
        result["profit_factor"] = float(pf.trades.profit_factor()) if result["total_trades"] > 0 else 0.0
        result["avg_trade_duration"] = float(pf.trades.duration.mean()) if result["total_trades"] > 0 else 0.0
        result["avg_win"] = float(pf.trades.winning.returns.mean()) * 100 if result["winning_trades"] > 0 else 0.0
        result["avg_loss"] = float(pf.trades.losing.returns.mean()) * 100 if result["losing_trades"] > 0 else 0.0
        result["expectancy"] = float(pf.trades.expectancy()) if result["total_trades"] > 0 else 0.0

        equity = pf.value()
        result["equity_curve"] = [
            {"date": d.strftime("%Y-%m-%d"), "value": float(v)}
            for d, v in equity.items()
        ]

        # Benchmark = buy & hold
        norm_close = close / close.iloc[0] * strategy.initial_capital
        result["benchmark_curve"] = [
            {"date": d.strftime("%Y-%m-%d"), "value": float(v)}
            for d, v in norm_close.items()
        ]

        # Drawdown
        dd = pf.drawdown() * 100
        result["drawdown_curve"] = [
            {"date": d.strftime("%Y-%m-%d"), "value": float(v)}
            for d, v in dd.items()
        ]

        # Daily returns
        result["daily_returns"] = [
            {"date": d.strftime("%Y-%m-%d"), "return": float(v) * 100}
            for d, v in pf.returns().items()
        ]

        # Monthly returns
        returns = pf.returns()
        monthly = (1 + returns).resample("ME").prod() - 1
        result["monthly_returns"] = [
            {"month": d.strftime("%Y-%m"), "return": float(v) * 100}
            for d, v in monthly.items()
        ]

        # Trade distribution
        result["trade_distribution"] = {
            "winning": result["winning_trades"],
            "losing": result["losing_trades"],
        }

        # Return distribution bins
        if result["total_trades"] > 0:
            trade_returns_arr = pf.trades.returns.values
            trade_returns_series = pd.Series(trade_returns_arr).dropna() * 100
            bins = [-np.inf, -5, -3, -1, 1, 3, 5, np.inf]
            labels = ["<-5%", "-5% to -3%", "-3% to -1%", "-1% to 1%", "1% to 3%", "3% to 5%", ">5%"]
            counts = pd.cut(trade_returns_series, bins=bins, labels=labels).value_counts().sort_index()
            result["return_distribution"] = {
                "labels": labels,
                "values": [int(counts.get(l, 0)) for l in labels],
            }

        # Price chart data (price only; indicator overlays are strategy-specific)
        result["price_with_indicators"] = [
            {"date": d.strftime("%Y-%m-%d"), "price": float(v)}
            for d, v in close.items()
        ]

        trades_df = pf.trades.records_readable
        result["trades"] = []
        if not trades_df.empty:
            for _, row in trades_df.iterrows():
                entry_idx = row.get("Entry Timestamp", None)
                exit_idx = row.get("Exit Timestamp", None)
                result["trades"].append({
                    "entry_date": entry_idx.strftime("%Y-%m-%d") if isinstance(entry_idx, pd.Timestamp) else str(entry_idx),
                    "exit_date": exit_idx.strftime("%Y-%m-%d") if isinstance(exit_idx, pd.Timestamp) else str(exit_idx),
                    "side": str(row.get("Direction", "Long")).capitalize(),
                    "status": str(row.get("Status", "Closed")).capitalize(),
                    "size": float(row.get("Size", 0)),
                    "entry": float(row.get("Avg Entry Price", 0)),
                    "exit": float(row.get("Avg Exit Price", 0)) if not pd.isna(row.get("Avg Exit Price")) else None,
                    "pnl": float(row.get("PnL", 0)),
                    "return_pct": float(row.get("Return", 0)) * 100,
                })

    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)

    return result
