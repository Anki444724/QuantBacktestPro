from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# ==========================================================
# STRATEGY
# ==========================================================

@dataclass
class IndicatorConfig:
    name: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionConfig:
    left: Any
    operator: str
    right: Any


@dataclass
class StrategyConfig:
    name: str
    indicators: List[IndicatorConfig] = field(default_factory=list)
    entry_rules: List[ConditionConfig] = field(default_factory=list)
    exit_rules: List[ConditionConfig] = field(default_factory=list)


# ==========================================================
# CURVES
# ==========================================================

@dataclass
class EquityPoint:
    date: str
    value: float


@dataclass
class BenchmarkPoint:
    date: str
    value: float


@dataclass
class DrawdownPoint:
    date: str
    value: float


# ==========================================================
# RETURNS
# ==========================================================

@dataclass
class DailyReturn:
    date: str
    return_pct: float


@dataclass
class MonthlyReturn:
    month: str
    return_pct: float


@dataclass
class AnnualReturn:
    year: int
    return_pct: float


# ==========================================================
# TRADE
# ==========================================================

@dataclass
class Trade:
    entry_date: str
    exit_date: str

    entry_price: float
    exit_price: float

    quantity: float = 1

    pnl: float = 0.0

    return_pct: float = 0.0

    duration: int = 0

    side: str = "LONG"


# ==========================================================
# PERFORMANCE
# ==========================================================

@dataclass
class PerformanceMetrics:

    total_return: float = 0.0

    annual_return: float = 0.0

    cagr: float = 0.0

    sharpe_ratio: float = 0.0

    sortino_ratio: float = 0.0

    calmar_ratio: float = 0.0

    max_drawdown: float = 0.0

    volatility: float = 0.0

    beta: float = 0.0

    alpha: float = 0.0


# ==========================================================
# TRADE METRICS
# ==========================================================

@dataclass
class TradeMetrics:

    total_trades: int = 0

    winning_trades: int = 0

    losing_trades: int = 0

    win_rate: float = 0.0

    best_trade: float = 0.0

    worst_trade: float = 0.0

    average_win: float = 0.0

    average_loss: float = 0.0

    profit_factor: float = 0.0

    expectancy: float = 0.0

    average_trade_duration: float = 0.0


# ==========================================================
# RISK
# ==========================================================

@dataclass
class RiskMetrics:

    value_at_risk: float = 0.0

    conditional_var: float = 0.0

    downside_deviation: float = 0.0

    ulcer_index: float = 0.0

    recovery_factor: float = 0.0


# ==========================================================
# ANALYTICS
# ==========================================================

@dataclass
class Analytics:

    monthly_returns: List[MonthlyReturn] = field(default_factory=list)

    annual_returns: List[AnnualReturn] = field(default_factory=list)

    daily_returns: List[DailyReturn] = field(default_factory=list)


# ==========================================================
# COMPLETE BACKTEST
# ==========================================================

@dataclass
class BacktestResult:

    id: str

    strategy: str

    symbol: str

    start: str

    end: str

    interval: str

    initial_capital: float

    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)

    trades_metrics: TradeMetrics = field(default_factory=TradeMetrics)

    risk: RiskMetrics = field(default_factory=RiskMetrics)

    analytics: Analytics = field(default_factory=Analytics)

    equity_curve: List[EquityPoint] = field(default_factory=list)

    benchmark_curve: List[BenchmarkPoint] = field(default_factory=list)

    drawdown_curve: List[DrawdownPoint] = field(default_factory=list)

    trades: List[Trade] = field(default_factory=list)

    strategy_config: Optional[StrategyConfig] = None

    status: str = "completed"

    error: Optional[str] = None

    def to_dict(self):
        return asdict(self)