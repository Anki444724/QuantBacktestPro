from __future__ import annotations

import numpy as np
import pandas as pd


# ==========================================================
# BASIC RETURNS
# ==========================================================

def calculate_total_return(initial_capital: float, final_capital: float) -> float:
    """
    Total return in percentage.
    """

    if initial_capital <= 0:
        return 0.0

    return ((final_capital / initial_capital) - 1) * 100


# ==========================================================
# CAGR
# ==========================================================

def calculate_cagr(
    initial_capital: float,
    final_capital: float,
    years: float,
) -> float:

    if initial_capital <= 0:
        return 0.0

    if years <= 0:
        return 0.0

    return ((final_capital / initial_capital) ** (1 / years) - 1) * 100


# ==========================================================
# DAILY RETURNS
# ==========================================================

def calculate_daily_returns(equity_curve: pd.Series) -> pd.Series:

    if len(equity_curve) == 0:
        return pd.Series(dtype=float)

    return equity_curve.pct_change().fillna(0)


# ==========================================================
# VOLATILITY
# ==========================================================

def calculate_volatility(
    daily_returns: pd.Series,
    trading_days: int = 252,
) -> float:

    if len(daily_returns) == 0:
        return 0.0

    return float(
        daily_returns.std() * np.sqrt(trading_days) * 100
    )


# ==========================================================
# DRAWDOWN CURVE
# ==========================================================

def calculate_drawdown_curve(
    equity_curve: pd.Series,
) -> pd.Series:

    if len(equity_curve) == 0:
        return pd.Series(dtype=float)

    running_max = equity_curve.cummax()

    drawdown = (
        equity_curve - running_max
    ) / running_max

    return drawdown * 100


# ==========================================================
# MAX DRAWDOWN
# ==========================================================

def calculate_max_drawdown(
    equity_curve: pd.Series,
) -> float:

    dd = calculate_drawdown_curve(
        equity_curve
    )

    if len(dd) == 0:
        return 0.0

    return float(dd.min())


# ==========================================================
# RECOVERY FACTOR
# ==========================================================

def calculate_recovery_factor(
    total_return: float,
    max_drawdown: float,
) -> float:

    if max_drawdown == 0:
        return 0.0

    return abs(total_return / max_drawdown)


# ==========================================================
# ULCER INDEX
# ==========================================================

def calculate_ulcer_index(
    equity_curve: pd.Series,
) -> float:

    dd = calculate_drawdown_curve(
        equity_curve
    )

    if len(dd) == 0:
        return 0.0

    return float(
        np.sqrt(
            np.mean(
                np.square(dd)
            )
        )
    )


# ==========================================================
# YEARS FROM DATES
# ==========================================================

def calculate_years(
    start_date,
    end_date,
) -> float:

    days = (
        end_date - start_date
    ).days

    return days / 365.25
# ==========================================================
# SHARPE RATIO
# ==========================================================

def calculate_sharpe(
    daily_returns: pd.Series,
    risk_free_rate: float = 0.0,
    trading_days: int = 252,
) -> float:

    if len(daily_returns) == 0:
        return 0.0

    excess = daily_returns - (risk_free_rate / trading_days)

    std = excess.std()

    if std == 0:
        return 0.0

    return float(
        (excess.mean() / std) * np.sqrt(trading_days)
    )


# ==========================================================
# SORTINO RATIO
# ==========================================================

def calculate_sortino(
    daily_returns: pd.Series,
    risk_free_rate: float = 0.0,
    trading_days: int = 252,
) -> float:

    if len(daily_returns) == 0:
        return 0.0

    downside = daily_returns[daily_returns < 0]

    if len(downside) == 0:
        return 0.0

    downside_std = downside.std()

    if downside_std == 0:
        return 0.0

    excess = daily_returns.mean() - (risk_free_rate / trading_days)

    return float(
        (excess / downside_std) * np.sqrt(trading_days)
    )


# ==========================================================
# CALMAR RATIO
# ==========================================================

def calculate_calmar(
    annual_return: float,
    max_drawdown: float,
) -> float:

    if max_drawdown == 0:
        return 0.0

    return abs(
        annual_return / max_drawdown
    )


# ==========================================================
# BETA
# ==========================================================

def calculate_beta(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> float:

    if len(strategy_returns) == 0:
        return 0.0

    if len(benchmark_returns) == 0:
        return 0.0

    aligned = pd.concat(
        [
            strategy_returns,
            benchmark_returns,
        ],
        axis=1,
    ).dropna()

    if len(aligned) == 0:
        return 0.0

    cov = aligned.iloc[:, 0].cov(
        aligned.iloc[:, 1]
    )

    var = aligned.iloc[:, 1].var()

    if var == 0:
        return 0.0

    return float(cov / var)


# ==========================================================
# ALPHA
# ==========================================================

def calculate_alpha(
    strategy_return: float,
    benchmark_return: float,
    beta: float,
    risk_free_rate: float = 0.0,
) -> float:

    expected = risk_free_rate + beta * (
        benchmark_return - risk_free_rate
    )

    return float(
        strategy_return - expected
    )


# ==========================================================
# TRACKING ERROR
# ==========================================================

def calculate_tracking_error(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> float:

    aligned = pd.concat(
        [
            strategy_returns,
            benchmark_returns,
        ],
        axis=1,
    ).dropna()

    if len(aligned) == 0:
        return 0.0

    diff = (
        aligned.iloc[:, 0]
        - aligned.iloc[:, 1]
    )

    return float(
        diff.std() * np.sqrt(252)
    )


# ==========================================================
# INFORMATION RATIO
# ==========================================================

def calculate_information_ratio(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> float:

    aligned = pd.concat(
        [
            strategy_returns,
            benchmark_returns,
        ],
        axis=1,
    ).dropna()

    if len(aligned) == 0:
        return 0.0

    diff = (
        aligned.iloc[:, 0]
        - aligned.iloc[:, 1]
    )

    te = diff.std()

    if te == 0:
        return 0.0

    return float(
        diff.mean() / te
    )


# ==========================================================
# TREYNOR RATIO
# ==========================================================

def calculate_treynor(
    annual_return: float,
    beta: float,
    risk_free_rate: float = 0.0,
) -> float:

    if beta == 0:
        return 0.0

    return float(
        (annual_return - risk_free_rate)
        / beta
    )
# ==========================================================
# WIN RATE
# ==========================================================

def calculate_win_rate(trades) -> float:

    if len(trades) == 0:
        return 0.0

    wins = sum(1 for t in trades if t.pnl > 0)

    return (wins / len(trades)) * 100


# ==========================================================
# PROFIT FACTOR
# ==========================================================

def calculate_profit_factor(trades) -> float:

    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)

    gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))

    if gross_loss == 0:
        return 0.0

    return gross_profit / gross_loss


# ==========================================================
# EXPECTANCY
# ==========================================================

def calculate_expectancy(trades) -> float:

    if len(trades) == 0:
        return 0.0

    return np.mean([t.pnl for t in trades])


# ==========================================================
# AVERAGE WIN
# ==========================================================

def calculate_average_win(trades) -> float:

    wins = [t.pnl for t in trades if t.pnl > 0]

    if len(wins) == 0:
        return 0.0

    return float(np.mean(wins))


# ==========================================================
# AVERAGE LOSS
# ==========================================================

def calculate_average_loss(trades) -> float:

    losses = [t.pnl for t in trades if t.pnl < 0]

    if len(losses) == 0:
        return 0.0

    return float(np.mean(losses))


# ==========================================================
# MONTHLY RETURNS
# ==========================================================

def calculate_monthly_returns(equity: pd.Series):

    if len(equity) == 0:
        return pd.Series(dtype=float)

    return (1 + equity.pct_change()).resample("ME").prod() - 1


# ==========================================================
# ANNUAL RETURNS
# ==========================================================

def calculate_annual_returns(equity: pd.Series):

    if len(equity) == 0:
        return pd.Series(dtype=float)

    return (1 + equity.pct_change()).resample("YE").prod() - 1


# ==========================================================
# ROLLING RETURNS
# ==========================================================

def calculate_rolling_returns(
    equity: pd.Series,
    window: int = 90,
):

    if len(equity) == 0:
        return pd.Series(dtype=float)

    return (equity / equity.shift(window) - 1) * 100


# ==========================================================
# ROLLING SHARPE
# ==========================================================

def calculate_rolling_sharpe(
    daily_returns: pd.Series,
    window: int = 252,
):

    rolling_mean = daily_returns.rolling(window).mean() * 252

    rolling_std = daily_returns.rolling(window).std() * np.sqrt(252)

    return rolling_mean / rolling_std


# ==========================================================
# CONVERT SERIES
# ==========================================================

def series_to_points(series):

    result = []

    for idx, value in series.items():

        if pd.isna(value):
            continue

        result.append(
            {
                "date": str(idx.date()),
                "value": float(value),
            }
        )

    return result