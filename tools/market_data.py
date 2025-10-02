# streamlit_app/tools/market_data.py
from typing import Dict, List, Optional
import time
import warnings
import pandas as pd

try:
    import yfinance as yf
except Exception:  # pragma: no cover - optional dependency
    yf = None


def _try_history_price(ticker: str, attempts: int = 3, pause: float = 1.0) -> Optional[float]:
    """Try to fetch recent price using history/download with a small retry loop.

    Returns last adjusted close as float, or None on failure.
    """
    if yf is None:
        return None
    for i in range(attempts):
        try:
            # explicit auto_adjust to silence FutureWarning and threads=False for single-ticker
            df = yf.download(ticker, period="5d", interval="1m", progress=False, auto_adjust=True, threads=False)
            # prefer Adj Close if present
            if df is None or df.empty:
                raise RuntimeError("no data")
            # If yfinance returned a Series (single column), handle it
            if isinstance(df, pd.Series):
                ser = df.dropna()
                last_val = float(ser.iat[-1])
                return last_val
            # If DataFrame, try to pick the Adj Close / Close column
            if isinstance(df, pd.DataFrame):
                if "Adj Close" in df.columns:
                    ser = df["Adj Close"].dropna()
                elif "Close" in df.columns:
                    ser = df["Close"].dropna()
                else:
                    # handle MultiIndex columns (e.g., ('Adj Close', 'TICKER'))
                    if df.columns.nlevels > 1:
                        try:
                            ser = df.xs("Adj Close", axis=1, level=0)
                            # if this returns a DataFrame (multiple tickers), pick first column
                            if isinstance(ser, pd.DataFrame):
                                ser = ser.iloc[:, 0].dropna()
                            else:
                                ser = ser.dropna()
                        except Exception:
                            raise RuntimeError("no Close/Adj Close column")
                    else:
                        raise RuntimeError("no Close/Adj Close column")
                # ser may still be a DataFrame if multiple tickers; pick first column
                if isinstance(ser, pd.DataFrame):
                    ser = ser.iloc[:, 0].dropna()
                last_val = float(ser.iat[-1])
                return last_val
            # otherwise unknown type
            raise RuntimeError(f"unexpected yf.download return type: {type(df)}")
            return last_val
        except Exception as e:
            # on last attempt warn, otherwise sleep and retry
            if i == attempts - 1:
                warnings.warn(f"market_data: failed to download {ticker}: {e}")
                return None
            time.sleep(pause)


def _try_info_price(ticker: str) -> Optional[float]:
    """Fallback: use Ticker.info regularMarketPrice if available."""
    if yf is None:
        return None
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        p = info.get("regularMarketPrice") or info.get("previousClose")
        if p is None:
            return None
        return float(p)
    except Exception:
        return None


def get_prices_yf(tickers: List[str]) -> Dict[str, Optional[float]]:
    """Return a dict mapping tickers to last price (float) or None if unavailable.

    This function fetches each ticker individually with retries and falls back to
    ticker.info if the minute-level history fails (helps in flaky network or
    rate-limited environments).
    """
    if yf is None:
        raise RuntimeError("Install yfinance to enable market data")
    if not tickers:
        return {}

    prices: Dict[str, Optional[float]] = {}
    for t in tickers:
        # sanitize ticker
        tk = t.strip()
        if not tk:
            continue
        price = _try_history_price(tk)
        if price is None:
            price = _try_info_price(tk)
        prices[tk] = price
    return prices
