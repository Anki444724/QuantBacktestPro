"""
FastAPI backend for the QuantBacktest Pro web application.

Endpoints:
- GET  /api/health                   Health check
- GET  /api/strategies               List built-in strategies and their parameters
- GET  /api/strategies/custom        List saved custom strategies
- POST /api/strategies/custom        Save a custom strategy
- GET  /api/strategies/custom/{id}   Fetch a custom strategy
- DELETE /api/strategies/custom/{id} Delete a custom strategy
- POST /api/backtest                 Run a built-in backtest
- POST /api/backtest/custom          Run a custom strategy backtest
- GET  /api/backtests                List recent backtest summaries
- GET  /api/backtest/{id}            Fetch a single backtest result
- GET  /api/backtest/{id}/trades     Paginated trade history
- GET  /api/symbols                  List popular ticker symbols
- GET  /api/data/info                Get data info for a symbol/period
- POST /api/data/clear-cache         Clear market data cache
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from symbols import ALL_SYMBOLS
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backtest_engine import STRATEGIES as BUILT_IN_STRATEGIES, run_backtest
from data_service import clear_cache, get_data_info
from strategy_builder import CustomStrategy, run_custom_strategy
from analytics import compute_all_analytics

import os

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="QuantBacktest Pro API",
    description="FastAPI backend with vectorbt backtesting engine and no-code strategy builder.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static frontend files
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

@app.get("/")
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "QuantBacktest Pro API is running. Visit /frontend/index.html"}

# In-memory stores
backtests_db: Dict[str, Dict[str, Any]] = {}
custom_strategies_db: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class BacktestRequest(BaseModel):
    strategy: str = Field(..., description="Built-in strategy key, e.g. sma_cross")
    symbol: str = Field(..., description="Yahoo Finance ticker symbol")
    start: str = Field(..., description="Start date YYYY-MM-DD")
    end: str = Field(..., description="End date YYYY-MM-DD")
    initial_capital: float = Field(100_000.0, ge=1_000, le=10_000_000)
    interval: str = Field("1d", description="Price interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CustomBacktestRequest(BaseModel):
    strategy: CustomStrategy
    symbol: str = Field(..., description="Yahoo Finance ticker symbol")
    start: str = Field(..., description="Start date YYYY-MM-DD")
    end: str = Field(..., description="End date YYYY-MM-DD")
    interval: str = Field("1d", description="Price interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo")


class BacktestSummary(BaseModel):
    id: str
    strategy: str
    symbol: str
    start: str
    end: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    status: str
    created_at: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "engine": "vectorbt"}


@app.get("/api/strategies")
def list_strategies() -> Dict[str, Any]:
    return {"strategies": BUILT_IN_STRATEGIES}


@app.get("/api/strategies/custom")
def list_custom_strategies() -> List[Dict[str, Any]]:
    items = sorted(custom_strategies_db.values(), key=lambda x: x.get("created_at", ""), reverse=True)
    return [
        {
            "id": item["id"],
            "name": item["name"],
            "symbol": item.get("symbol"),
            "created_at": item.get("created_at"),
        }
        for item in items
    ]


@app.post("/api/strategies/custom")
def save_custom_strategy(strategy: CustomStrategy) -> Dict[str, Any]:
    strategy_id = datetime.utcnow().strftime("cs_%Y%m%d%H%M%S")
    payload = {
        "id": strategy_id,
        "name": strategy.name,
        "config": strategy.model_dump(),
        "created_at": datetime.utcnow().isoformat(),
    }
    custom_strategies_db[strategy_id] = payload
    return payload


@app.get("/api/strategies/custom/{strategy_id}")
def get_custom_strategy(strategy_id: str) -> Dict[str, Any]:
    if strategy_id not in custom_strategies_db:
        raise HTTPException(status_code=404, detail="Custom strategy not found")
    return custom_strategies_db[strategy_id]


@app.delete("/api/strategies/custom/{strategy_id}")
def delete_custom_strategy(strategy_id: str) -> Dict[str, str]:
    if strategy_id not in custom_strategies_db:
        raise HTTPException(status_code=404, detail="Custom strategy not found")
    del custom_strategies_db[strategy_id]
    return {"status": "deleted"}


@app.get("/api/symbols")
def list_symbols():
    return {
        "symbols": ALL_SYMBOLS
    }


@app.get("/api/data/info")
def data_info(symbol: str, start: str, end: str, interval: str = "1d") -> Dict[str, Any]:
    try:
        return get_data_info(symbol, start, end, interval)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/api/data/clear-cache")
def clear_data_cache() -> Dict[str, int]:
    return {"removed": clear_cache()}


@app.post("/api/backtest")
def create_backtest(request: BacktestRequest) -> Dict[str, Any]:
    if request.strategy not in BUILT_IN_STRATEGIES:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {request.strategy}")

    backtest_id = datetime.utcnow().strftime("bt_%Y%m%d%H%M%S")
    result = run_backtest(
        strategy=request.strategy,
        symbol=request.symbol,
        start=request.start,
        end=request.end,
        initial_capital=request.initial_capital,
        interval=request.interval,
        params=request.params or {},
        backtest_id=backtest_id,
    )

    payload = result.to_dict()
    payload["created_at"] = datetime.utcnow().isoformat()
    payload["analytics"] = compute_all_analytics(
        equity_curve=payload.get("equity_curve", []),
        daily_returns=payload.get("daily_returns", []),
        trades=payload.get("trades", []),
    )
    backtests_db[backtest_id] = payload
    print("=" * 60)
    print("BACKTEST SAVED")
    print("ID:", backtest_id)
    print("TOTAL:", len(backtests_db))
    print("KEYS:", list(backtests_db.keys()))
    print("=" * 60)

    if result.status == "error":
        raise HTTPException(status_code=422, detail=result.error)

    return payload


@app.post("/api/backtest/custom")
def create_custom_backtest(request: CustomBacktestRequest) -> Dict[str, Any]:
    backtest_id = datetime.utcnow().strftime("bt_%Y%m%d%H%M%S")
    result = run_custom_strategy(
        strategy=request.strategy,
        symbol=request.symbol,
        start=request.start,
        end=request.end,
        interval=request.interval,
        backtest_id=backtest_id,
    )

    result["created_at"] = datetime.utcnow().isoformat()
    result["analytics"] = compute_all_analytics(
        equity_curve=result.get("equity_curve", []),
        daily_returns=result.get("daily_returns", []),
        trades=result.get("trades", []),
    )
    backtests_db[backtest_id] = result
    print("=" * 60)
    print("CUSTOM BACKTEST SAVED")
    print("ID:", backtest_id)
    print("TOTAL:", len(backtests_db))
    print("KEYS:", list(backtests_db.keys()))
    print("=" * 60) 

    if result["status"] == "error":
        raise HTTPException(status_code=422, detail=result["error"])

    return result


@app.get("/api/backtests")
def list_backtests(limit: int = 20) -> List[Dict[str, Any]]:
    items = sorted(
        backtests_db.values(),
        key=lambda x: x["created_at"],
        reverse=True,
    )

    return items[:limit]


@app.get("/api/backtest/{backtest_id}")
def get_backtest(backtest_id: str) -> Dict[str, Any]:
    if backtest_id not in backtests_db:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return backtests_db[backtest_id]


@app.get("/api/backtest/{backtest_id}/analytics")
def get_analytics(backtest_id: str) -> Dict[str, Any]:
    if backtest_id not in backtests_db:
        raise HTTPException(status_code=404, detail="Backtest not found")
    item = backtests_db[backtest_id]
    if "analytics" in item:
        return item["analytics"]
    return compute_all_analytics(
        equity_curve=item.get("equity_curve", []),
        daily_returns=item.get("daily_returns", []),
        trades=item.get("trades", []),
    )


@app.get("/api/backtest/{backtest_id}/trades")
def get_trades(
    backtest_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    side: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    if backtest_id not in backtests_db:
        raise HTTPException(status_code=404, detail="Backtest not found")

    trades = backtests_db[backtest_id].get("trades", [])
    if side:
        trades = [t for t in trades if t.get("side", "").lower() == side.lower()]
    if status:
        trades = [t for t in trades if t.get("status", "").lower() == status.lower()]

    total = len(trades)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_trades = trades[start_idx:end_idx]

    return {
        "backtest_id": backtest_id,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": (total + page_size - 1) // page_size,
        "trades": page_trades,
    }
