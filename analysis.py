"""
analysis.py
-----------
Pandas rewrite of the metrics pipeline from Financial_db.py.
Does the SAME calculations (returns, MA-50, MA-200, rolling vol,
Sharpe, Sortino, Max Drawdown, VaR 95%, Beta) but without
PySpark / Delta Lake, so it runs on a plain laptop.

Pulls live data from Yahoo Finance via yfinance for the past 3 years.
"""

from mimetypes import inited

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

BENCHMARK = "^NSEI"  # NIFTY 50

TICKER_NAMES = {
    "RELIANCE.NS": "Reliance Industries",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS":"ICICI Bank",
    "M&M.NS": "Mahindra And Mahindra Ltd",
    "SBIN.NS":     "State Bank of India",
}

TICKERS = list(TICKER_NAMES.keys())


def _date_range(years=3):
    end = datetime.now() - timedelta(days=1)
    start = end - timedelta(days=365 * years)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def fetch_prices(ticker: str, start: str, end: str) -> pd.DataFrame | None:
    """Download and normalize OHLCV data for one ticker."""
    raw = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
    if raw is None or raw.empty:
        return None

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = [c[0] for c in raw.columns]

    raw = raw.reset_index()
    raw.columns = [str(c).strip() for c in raw.columns]

    if "Adj Close" not in raw.columns and "Close" in raw.columns:
        raw["Adj Close"] = raw["Close"]

    keep = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    keep = [c for c in keep if c in raw.columns]
    df = raw[keep].copy()
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Daily return, MA-50, MA-200, 30-day rolling annualized volatility."""
    df = df.sort_values("Date").reset_index(drop=True)
    df["daily_return"] = df["Adj Close"].pct_change()
    df["ma_50"] = df["Adj Close"].rolling(50, min_periods=1).mean()
    df["ma_200"] = df["Adj Close"].rolling(200, min_periods=1).mean()
    df["rolling_vol_30"] = df["daily_return"].rolling(30, min_periods=2).std() * np.sqrt(252)
    return df


def compute_metrics(returns: pd.Series, benchmark_returns: pd.Series | None) -> dict:
    """Annual return/vol, Sharpe, Sortino, Max Drawdown, VaR 95%, Beta."""
    r = returns.dropna()

    annual_return_pct = r.mean() * 252 * 100
    annual_vol_pct = r.std() * np.sqrt(252) * 100

    downside = r[r < 0]
    mean_downside = downside.mean() if len(downside) else 0.0
    std_downside = downside.std() if len(downside) > 1 else 0.0

    sharpe_ratio = (annual_return_pct / annual_vol_pct) if annual_vol_pct else 0.0
    sortino_ratio = (
        (annual_return_pct / 100.0) / (std_downside * np.sqrt(252))
        if std_downside else 0.0
    )

    cum = (1 + r).cumprod()
    max_drawdown = float((cum / cum.cummax() - 1).min())
    var_95 = float(np.percentile(r, 5))

    beta = 1.0
    if benchmark_returns is not None:
        aligned = pd.concat([r, benchmark_returns], axis=1).dropna()
        aligned.columns = ["s", "m"]
        if len(aligned) >= 30 and aligned["m"].var() != 0:
            cov = np.cov(aligned["s"], aligned["m"])
            beta = float(cov[0, 1] / np.var(aligned["m"]))

    return {
        "annual_return_pct": round(annual_return_pct, 2),
        "annual_vol_pct": round(annual_vol_pct, 2),
        "sharpe_ratio": round(sharpe_ratio, 4),
        "sortino_ratio": round(sortino_ratio, 4),
        "max_drawdown": round(max_drawdown, 4),
        "var_95": round(var_95, 4),
        "beta": round(beta, 4),
        "mean_downside": round(float(mean_downside), 5),
        "std_downside": round(float(std_downside), 5),
    }


def analyze_ticker(ticker: str) -> dict:
    """
    Full pipeline for ONE ticker: fetch -> features -> metrics.
    Returns a dict ready to hand to the LLM report generator.
    """
    if ticker not in TICKERS:
        raise ValueError(f"Unknown ticker: {ticker}. Must be one of {TICKERS}")

    start, end = _date_range(years=3)

    stock_raw = fetch_prices(ticker, start, end)
    if stock_raw is None or len(stock_raw) < 100:
        raise RuntimeError(f"Not enough data returned for {ticker}")

    bench_raw = fetch_prices(BENCHMARK, start, end)

    stock_feat = compute_features(stock_raw)
    bench_returns = None
    if bench_raw is not None and len(bench_raw) > 30:
        bench_feat = compute_features(bench_raw)
        bench_returns = bench_feat.set_index("Date")["daily_return"]

    stock_returns = stock_feat.set_index("Date")["daily_return"]
    metrics = compute_metrics(stock_returns, bench_returns)

    latest = stock_feat.iloc[-1]

    return {
        "ticker": ticker,
        "name": TICKER_NAMES[ticker],
        "latest_price": round(float(latest["Adj Close"]), 2),
        "ma_50": round(float(latest["ma_50"]), 2),
        "ma_200": round(float(latest["ma_200"]), 2),
        "vol_30d": (
            round(float(latest["rolling_vol_30"]), 4)
            if pd.notna(latest["rolling_vol_30"]) else None
        ),
        "data_points": len(stock_feat),
        "date_range": [start, end],
        **metrics,
    }
