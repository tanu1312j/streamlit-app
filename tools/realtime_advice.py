# streamlit_app/tools/realtime_advice.py
from typing import Dict, Union

try:
    import yfinance as yf
except Exception:  # pragma: no cover - optional dependency
    yf = None

def _sma_signal(symbol: str, days_fast=20, days_slow=50, use_daily_fallback: bool = False):
    """Compute a simple SMA crossover signal using daily history.

    If `use_daily_fallback` is True, this function will still attempt to use
    daily history even when minute data was requested elsewhere. This helps
    environments where minute-level downloads time out.
    """
    if yf is None:
        return {"signal": "hold", "reason": "yfinance not available"}
    # explicit auto_adjust to silence future warning and threads=False for single-ticker
    df = None
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False, auto_adjust=True, threads=False)
    except Exception:
        df = None
    if df is None or df.empty or "Adj Close" not in df:
        return {"signal": "hold", "reason": "insufficient data"}
    hist = df["Adj Close"].dropna()
    if len(hist) < days_slow:
        return {"signal": "hold", "reason": "insufficient data"}
    sma_fast = hist.rolling(days_fast).mean().iloc[-1]
    sma_slow = hist.rolling(days_slow).mean().iloc[-1]
    if sma_fast > sma_slow * 1.01:
        return {"signal": "long", "reason": f"SMA{days_fast}>{days_slow}"}
    elif sma_fast < sma_slow * 0.99:
        return {"signal": "short", "reason": f"SMA{days_fast}<{days_slow}"}
    else:
        return {"signal": "hold", "reason": "no clear edge"}

def make_position_plan(
    price: float,
    capital: float,
    max_pct: float,
    stop_loss_pct: float,
    take_profit_pct: float,
):
    alloc = capital * (max_pct/100.0)
    qty = max(int(alloc // price), 0)
    sl = round(price * (1 - stop_loss_pct/100.0), 2)
    tp = round(price * (1 + take_profit_pct/100.0), 2)
    return {
        "qty": qty,
        "stop_loss": sl,
        "take_profit": tp,
        "allocated_cash": round(qty * price, 2),
    }

def run_realtime_advice(inp, use_daily_fallback: bool = False) -> Dict:
    out = {}
    # allow dict inputs (from an LLM agent)
    if isinstance(inp, dict):
        # minimal validation
        tickers = inp.get("tickers", [])
        capital = float(inp.get("capital", 0.0))
        max_pct = float(inp.get("max_position_pct", 10.0))
        stop_loss = float(inp.get("stop_loss_pct", 2.0))
        take_profit = float(inp.get("take_profit_pct", 4.0))
    else:
        tickers = inp.tickers
        capital = inp.capital
        max_pct = inp.max_position_pct
        stop_loss = inp.stop_loss_pct
        take_profit = inp.take_profit_pct

    for sym in tickers:
        try:
            if yf is None:
                out[sym] = {
                    "price": None,
                    "signal": "hold",
                    "reason": "yfinance not available",
                    "plan": {},
                }
                continue
            # Try minute-level recent price first (best for intraday). If that fails
            # and use_daily_fallback=True, fall back to recent daily close.
            px = None
            tick_df = None
            try:
                tick_df = yf.download(sym, period="5d", interval="1m", progress=False, auto_adjust=True, threads=False)
                if tick_df is not None and not tick_df.empty and "Adj Close" in tick_df:
                    px = tick_df["Adj Close"].dropna().iat[-1]
            except Exception:
                px = None

            if px is None and use_daily_fallback:
                # try to get the last daily close
                try:
                    ddf = yf.download(sym, period="7d", interval="1d", progress=False, auto_adjust=True, threads=False)
                    if ddf is not None and not ddf.empty and "Adj Close" in ddf:
                        px = ddf["Adj Close"].dropna().iat[-1]
                except Exception:
                    px = None

            if px is None:
                out[sym] = {
                    "price": None,
                    "signal": "hold",
                    "reason": "no recent price (minute and daily fallback attempted)",
                    "plan": {},
                }
                continue

            sig = _sma_signal(sym, use_daily_fallback=use_daily_fallback)
            plan = make_position_plan(px, capital, max_pct, stop_loss, take_profit)
            out[sym] = {
                "price": round(float(px), 2),
                "signal": sig["signal"],
                "reason": sig["reason"],
                "plan": plan,
            }
        except Exception as e:
            out[sym] = {"price": None, "signal": "hold", "reason": f"error: {e}", "plan": {}}

    out["_disclaimer"] = "Educational only. Not investment advice. Use paper trading."
    return out
