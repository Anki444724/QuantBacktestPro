# QuantBacktest Pro

A full-stack backtesting platform with a **FastAPI** backend powered by **vectorbt**, a real **no-code strategy builder**, professional analytics, and a responsive **HTML/CSS/JS** frontend.

## Quick Start

```bash
cd /home/user/backtester
./start.sh
```

Then open **http://localhost:8000/** in your browser.

> **Note for Arena users:** The in-app file preview runs in a sandboxed iframe without network access, so the backend status will show **OFFLINE** inside the preview. Run `./start.sh` and open `http://localhost:8000/` in a regular browser tab (or use port forwarding) to use the full application.

## Features

### No-Code Strategy Builder
- Build strategies without writing code
- Add **unlimited indicators**: SMA, EMA, RSI, MACD, Supertrend, VWAP, Bollinger Bands, ATR, ADX
- Create **Entry Rules** and **Exit Rules** with AND/OR condition groups
- Crossover operators: `crosses above`, `crosses below`
- Configure **Stop Loss**, **Take Profit**, and **Trailing Stop**
- Save strategies and reload them later
- Strategies are automatically converted into executable vectorbt logic

### Backtesting Engine & Analytics
- **Real backtesting engine** using `vectorbt` + `yfinance`
- **Yahoo Finance data support** with disk caching and interval support (1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo)
- **Synthetic data fallback** when Yahoo Finance is unreachable (offline/sandboxed environments)
- Performance metrics: total/annual/benchmark return, Sharpe, Sortino, Calmar, Omega, max drawdown, volatility, VaR 95%, CVaR 95%, alpha, beta, profit factor, expectancy, win rate, best/worst trade
- Professional analytics: equity curve, drawdown curve, monthly returns heatmap, rolling Sharpe, rolling returns, annual returns, trade distribution, return distribution, holding time analysis, win/loss streak, risk analysis (skewness, kurtosis, max consecutive loss days)
- Trade history with paginated API and CSV export

## Project Structure

```
backtester/
├── start.sh                 # One-command startup script
├── backend/
│   ├── main.py              # FastAPI app & routes + static frontend serving
│   ├── backtest_engine.py   # Built-in vectorbt strategies
│   ├── strategy_builder.py  # No-code strategy builder engine
│   ├── analytics.py         # Professional analytics suite
│   ├── data_service.py      # Yahoo Finance + cache + synthetic fallback
│   └── requirements.txt
└── frontend/
    └── index.html           # Single-page frontend
```

## Manual Setup

### 1. Install dependencies

```bash
cd backtester/backend
pip install -r requirements.txt
```

> Note: `vectorbt` pulls in `numpy`, `pandas`, `numba`, and `scipy`. Installation may take a few minutes.

### 2. Start the backend

The backend serves both the API and the static frontend files on port `8000`.

```bash
cd backtester/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API docs will be available at: `http://localhost:8000/docs`

### 3. Open the app

```bash
# The frontend is served directly by the backend:
open http://localhost:8000/
```

Or serve it separately on port `8080`:

```bash
cd /home/user/backtester
python -m http.server 8080
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/strategies` | List built-in strategies and their parameters |
| GET | `/api/strategies/custom` | List saved custom strategies |
| POST | `/api/strategies/custom` | Save a custom strategy |
| GET | `/api/strategies/custom/{id}` | Fetch a custom strategy |
| DELETE | `/api/strategies/custom/{id}` | Delete a custom strategy |
| GET | `/api/symbols` | List popular ticker symbols |
| GET | `/api/data/info` | Get data info for a symbol/period |
| POST | `/api/data/clear-cache` | Clear market data cache |
| POST | `/api/backtest` | Run a built-in backtest |
| POST | `/api/backtest/custom` | Run a custom strategy backtest |
| GET | `/api/backtests` | List recent backtest summaries |
| GET | `/api/backtest/{id}` | Get a single backtest result |
| GET | `/api/backtest/{id}/analytics` | Professional analytics suite |
| GET | `/api/backtest/{id}/trades` | Paginated trade history |

## Notes

- Market data is downloaded on-demand from Yahoo Finance and cached to `backend/.cache/market_data/`. If Yahoo Finance is unreachable, the engine automatically falls back to realistic synthetic OHLCV data so backtests still run end-to-end.
- Backtest history and saved strategies are stored in memory and reset when the server restarts.
- The `data_source` field in each backtest result indicates whether real (`yahoo`) or fallback (`synthetic`) data was used.
