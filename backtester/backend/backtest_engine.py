from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from strategies import StrategyRunner
from portfolio import PortfolioBuilder
from trade_engine import TradeEngine
from typing import Tuple

import numpy as np
import pandas as pd
import vectorbt as vbt
import math

from data_service import fetch_data
DEFAULT_FEES = 0.001

DEFAULT_SLIPPAGE = 0.0005

DEFAULT_FREQ = "1D"
STRATEGIES = {
    "sma_cross": {
        "label": "SMA Crossover",
        "params": {
            "fast": 20,
            "slow": 50,
        },
    },
    "ema_cross": {
        "label": "EMA Crossover",
        "params": {
            "fast": 20,
            "slow": 50,
        },
    },
    "rsi": {
        "label": "RSI",
        "params": {
            "period": 14,
            "buy": 30,
            "sell": 70,
        },
    },
}
@dataclass
class BacktestResult:

    id: str

    strategy: str

    symbol: str

    start: str

    end: str

    interval: str

    initial_capital: float

    # =====================================================
    # PERFORMANCE
    # =====================================================

    total_return: float = 0.0

    annual_return: float = 0.0

    sharpe_ratio: float = 0.0

    max_drawdown: float = 0.0

    win_rate: float = 0.0

    total_trades: int = 0

    winning_trades: int = 0

    losing_trades: int = 0

    best_trade: float = 0.0

    worst_trade: float = 0.0

    avg_win: float = 0.0

    avg_loss: float = 0.0

    profit_factor: float = 0.0

    expectancy: float = 0.0

    avg_trade_duration: float = 0.0

    volatility: float = 0.0

    downside_deviation: float = 0.0

    sortino_ratio: float = 0.0

    omega_ratio: float = 0.0

    calmar_ratio: float = 0.0

    beta: float = 0.0

    alpha: float = 0.0

    benchmark_return: float = 0.0

    var_95: float = 0.0

    # =====================================================
    # CHARTS
    # =====================================================

    equity_curve: List = field(default_factory=list)

    benchmark_curve: List = field(default_factory=list)

    drawdown_curve: List = field(default_factory=list)

    daily_returns: List = field(default_factory=list)

    monthly_returns: List = field(default_factory=list)

    annual_returns: List = field(default_factory=list)

    price_with_indicators: List = field(default_factory=list)

    # =====================================================
    # TRADE ANALYTICS
    # =====================================================

    trades: List = field(default_factory=list)

    trade_distribution: Dict = field(
        default_factory=lambda: {
            "winning": 0,
            "losing": 0,
        }
    )

    return_distribution: Dict = field(
        default_factory=lambda: {
            "labels": [],
            "values": [],
        }
    )

    strategy_config: Dict = field(default_factory=dict)

    # =====================================================

    status: str = "completed"

    error: Optional[str] = None

    def to_dict(self):
        return asdict(self)
# ============================================================
# SMA CROSSOVER
# ============================================================

def _sma_strategy(
    df: pd.DataFrame,
    params: Dict[str, Any],
):

    fast = int(params.get("fast", 20))
    slow = int(params.get("slow", 50))

    sma_fast = vbt.MA.run(
        df["Close"],
        fast,
    )

    sma_slow = vbt.MA.run(
        df["Close"],
        slow,
    )

    entries = sma_fast.ma_crossed_above(
        sma_slow
    )

    exits = sma_fast.ma_crossed_below(
        sma_slow
    )

    return entries, exits


# ============================================================
# EMA CROSSOVER
# ============================================================

def _ema_strategy(
    df: pd.DataFrame,
    params: Dict[str, Any],
):

    fast = int(params.get("fast", 20))
    slow = int(params.get("slow", 50))

    ema_fast = vbt.MA.run(
        df["Close"],
        fast,
        ewm=True,
    )

    ema_slow = vbt.MA.run(
        df["Close"],
        slow,
        ewm=True,
    )

    entries = ema_fast.ma_crossed_above(
        ema_slow
    )

    exits = ema_fast.ma_crossed_below(
        ema_slow
    )

    return entries, exits
# ============================================================
# RSI STRATEGY
# ============================================================

def _rsi_strategy(
    df: pd.DataFrame,
    params: Dict[str, Any],
):

    period = int(
        params.get("period", 14)
    )

    buy = float(
        params.get("buy", 30)
    )

    sell = float(
        params.get("sell", 70)
    )

    rsi = vbt.RSI.run(
        df["Close"],
        window=period,
    )

    entries = rsi.rsi < buy

    exits = rsi.rsi > sell

    return entries, exits

# ============================================================
# RUN BACKTEST
# ============================================================

def run_backtest(
    strategy: str,
    symbol: str,
    start: str,
    end: str,
    initial_capital: float = 100000,
    interval: str = "1d",
    params: Optional[Dict[str, Any]] = None,
    backtest_id: str = "bt_test",
):

    params = params or {}

    df = fetch_data(
        symbol=symbol,
        start=start,
        end=end,
        interval=interval,
    )

    if len(df) < 20:
        raise ValueError("Not enough historical data.")

    entries, exits = StrategyRunner.run(
    strategy=strategy,
    df=df,
    params=params,
)
    df = df.copy()
    df.index = pd.DatetimeIndex(df.index)
    df.index.freq = None

    portfolio = PortfolioBuilder.build(
    df=df,
    entries=entries,
    exits=exits,
    initial_capital=initial_capital,
)

    trades = TradeEngine.extract_trades(portfolio)

    trade_stats = TradeEngine.statistics(trades)

    equity = PortfolioBuilder.equity_curve(portfolio)

    benchmark_curve = PortfolioBuilder.benchmark_curve(
    df=df,
    initial_capital=initial_capital,
)

    drawdown_curve = PortfolioBuilder.drawdown_curve(
    portfolio,
)
        

        # ===========================
    # SAFE METRICS
    # ===========================

    total_return = float(portfolio.total_return())
    if not math.isfinite(total_return):
        total_return = 0.0

    sharpe_ratio = float(portfolio.sharpe_ratio(freq="1D"))
    if not math.isfinite(sharpe_ratio):
        sharpe_ratio = 0.0

    max_drawdown = float(portfolio.max_drawdown())
    if not math.isfinite(max_drawdown):
        max_drawdown = 0.0

    win_rate = float(portfolio.trades.win_rate())
    if not math.isfinite(win_rate):
        win_rate = 0.0

    result = BacktestResult(
        id=backtest_id,
        strategy=strategy,
        symbol=symbol,
        start=start,
        end=end,
        interval=interval,
        initial_capital=initial_capital,
        total_return=total_return,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        total_trades=len(trades),
        winning_trades=trade_stats["winning_trades"],
        losing_trades=trade_stats["losing_trades"],
        best_trade=trade_stats["best_trade"],
        worst_trade=trade_stats["worst_trade"],
        avg_win=trade_stats["avg_win"],
        avg_loss=trade_stats["avg_loss"],
        profit_factor=trade_stats["profit_factor"],
        expectancy=trade_stats["expectancy"],
        equity_curve=equity,
        benchmark_curve=benchmark_curve,
        drawdown_curve=drawdown_curve,
        trades=trades,
        status="completed",
    )

    print("========== RESULT ==========")
    print(result.to_dict())
    print("Equity Length:", len(result.equity_curve))
    print("Trades Length:", len(result.trades))
    print("============================")

    return result