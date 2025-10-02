"""Streamlit app for personal finance toolbox

Clean single-file UI with four flows: Savings, Insurance, Realtime Advice,
and Rebalance. Includes a cached warmup helper and a daily-fallback toggle
for realtime price lookups.
"""
from __future__ import annotations

import json
import time
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

import streamlit as st

from core.config import settings
from tools import savings_model, insurance_model, realtime_advice, rebalancer


# --- Diagnostics / tracing utilities -----------------------------------------------
if "traces" not in st.session_state:
    st.session_state.traces = []


def log_trace(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.traces.append(f"[{ts}] {msg}")


def clear_traces() -> None:
    st.session_state.traces = []


# --- Market data warmup helper (cached) -------------------------------------------
@st.cache_data(ttl=300)
def warm_market_data(symbols: List[str]) -> Dict[str, Optional[float]]:
    """Prefetch recent daily close prices for a list of symbols.

    Returns symbol -> last_close or None on failure.
    """
    results: Dict[str, Optional[float]] = {}
    try:
        import yfinance as yf
    except Exception:
        for s in symbols:
            results[s] = None
        log_trace("warm_market_data: yfinance import failed")
        return results

    for s in symbols:
        try:
            ticker = yf.Ticker(s)
            df = ticker.history(period="7d", interval="1d")
            if df is None or df.empty:
                results[s] = None
                log_trace(f"warm_market_data: no daily history for {s}")
            else:
                last_close = float(df["Close"].dropna().iloc[-1])
                results[s] = last_close
                log_trace(f"warm_market_data: {s} -> {last_close}")
        except Exception as e:
            results[s] = None
            log_trace(f"warm_market_data: error for {s}: {e}")

    return results


# --- Small helpers -----------------------------------------------------------------
def json_display(obj: object) -> None:
    st.json(obj)


def run_with_timeout(fn, timeout: float = 8.0, *a, **kw) -> Tuple[Optional[object], Optional[str]]:
    """Run `fn(*a, **kw)` in a background thread and return (result, error_str).

    If the call times out or raises, result will be None and error_str a message.
    """
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(fn, *a, **kw)
        try:
            return fut.result(timeout=timeout), None
        except FuturesTimeout:
            try:
                fut.cancel()
            except Exception:
                pass
            return None, f"timeout after {timeout} seconds"
        except Exception as e:
            return None, str(e)


# --- Streamlit UI ------------------------------------------------------------------
st.set_page_config(page_title="Personal Finance Toolbox", layout="wide")

st.title("Personal Finance Toolbox")

with st.sidebar:
    st.header("Tools")
    st.write("Quick actions and warmups")

    if st.button("Warm market data for portfolio"):
        try:
            with open("data/mock_portfolio.json") as f:
                portfolio = json.load(f)
                symbols = [h.get("symbol") for h in portfolio.get("holdings", []) if h.get("symbol")]
        except Exception:
            symbols = []

        if not symbols:
            st.write("No symbols found in mock portfolio")
        else:
            with st.spinner("Prefetching daily closes..."):
                warmed = warm_market_data(symbols)
            st.write("Warmup results:")
            json_display(warmed)
            log_trace(f"Warmup prefetch for {len(symbols)} symbols")

    if st.button("Clear traces"):
        clear_traces()
        st.experimental_rerun()

    st.markdown("---")
    st.write(f"App settings: env={settings.ENV}")


# Top-level tabs for flows
tabs = st.tabs(["Savings", "Insurance", "Realtime Advice", "Rebalance"])


# ------------------ Savings flow ---------------------------------------------------
with tabs[0]:
    st.header("Savings planner")
    with st.form("savings_form"):
        st.subheader("Demographics")
        age = st.number_input("Age", min_value=18, max_value=100, value=35, key="sav_age")
        dependents = st.number_input("Dependents", min_value=0, max_value=10, value=2, key="sav_dependents")
        risk_score = st.slider("Risk score", min_value=1, max_value=5, value=3, key="sav_risk")

        st.subheader("Income & expenses")
        monthly_income_fixed = st.number_input("Monthly income (fixed) (INR)", min_value=0.0, value=50000.0)
        monthly_income_variable = st.number_input("Monthly income (variable) (INR)", min_value=0.0, value=0.0)
        fixed_expenses = st.number_input("Fixed monthly expenses (INR)", min_value=0.0, value=15000.0)
        variable_expenses = st.number_input("Variable monthly expenses (INR)", min_value=0.0, value=10000.0)

        st.subheader("Assets & goals")
        existing_savings = st.number_input("Existing savings (INR)", min_value=0.0, value=100000.0)
        existing_debt = st.number_input("Existing debt (INR)", min_value=0.0, value=0.0)
        emergency_fund_months_target = st.number_input("Emergency fund target (months)", min_value=0.0, max_value=24.0, value=6.0)

        submit = st.form_submit_button("Run savings model")

    if submit:
        payload = {
            "demo": {"age": int(age), "dependents": int(dependents), "risk_score": int(risk_score)},
            "monthly_income_fixed": float(monthly_income_fixed),
            "monthly_income_variable": float(monthly_income_variable),
            "fixed_expenses": float(fixed_expenses),
            "variable_expenses": float(variable_expenses),
            "existing_savings": float(existing_savings),
            "existing_debt": float(existing_debt),
            "emergency_fund_months_target": float(emergency_fund_months_target),
        }

        with st.spinner("Computing savings plan..."):
            res, err = run_with_timeout(savings_model.run_savings_model, 6.0, payload)
            if err:
                st.error(f"Savings model error: {err}")
                log_trace(f"Savings model error: {err}")
            else:
                st.success("Done")
                json_display(res)
                log_trace("Ran savings model")


# ------------------ Insurance flow -------------------------------------------------
with tabs[1]:
    st.header("Insurance needs")
    with st.form("insurance_form"):
        st.subheader("About you")
        age = st.number_input("Age", min_value=18, max_value=100, value=35, key="ins_age")
        dependents = st.number_input("Dependents", min_value=0, max_value=10, value=2, key="ins_dependents")
        st.subheader("Income & covers")
        annual_income = st.number_input("Annual income (INR)", min_value=0.0, value=600000.0)
        has_employer_health = st.checkbox("Do you have employer health cover?", value=False)
        employer_health_cover = 0.0
        if has_employer_health:
            employer_health_cover = st.number_input("Employer health cover amount (INR)", min_value=0.0, value=0.0)

        submit_ins = st.form_submit_button("What insurance do I need?")

    if submit_ins:
        payload = {
            "demo": {"age": int(age), "dependents": int(dependents), "risk_score": 3},
            "annual_income": float(annual_income),
            "has_employer_health": bool(has_employer_health),
            "employer_health_cover": float(employer_health_cover),
            "existing_covers": {},
        }
        with st.spinner("Computing insurance recommendations..."):
            res, err = run_with_timeout(insurance_model.run_insurance_model, 6.0, payload)
            if err:
                st.error(f"Insurance model error: {err}")
                log_trace(f"Insurance model error: {err}")
            else:
                st.success("Done")
                json_display(res)
                log_trace("Ran insurance model")


# ------------------ Realtime advice flow ------------------------------------------
with tabs[2]:
    st.header("Realtime advice")
    st.write("Get quick buy/hold/sell advice. Minute data may be unavailable; enable daily fallback to use last daily close.")

    use_daily_fallback = st.checkbox("Use daily-fallback when minute data unavailable", value=True)

    with st.form("realtime_form"):
        symbols_text = st.text_area("Tickers (comma separated, ex: INFY.NS, TCS.NS)", value="INFY.NS,TCS.NS")
        capital = st.number_input("Available capital for advice (INR)", min_value=0.0, value=100000.0)
        max_position_pct = st.number_input("Max position % per symbol", min_value=0.0, max_value=100.0, value=10.0)
        stop_loss_pct = st.number_input("Stop loss %", min_value=0.0, max_value=100.0, value=2.0)
        take_profit_pct = st.number_input("Take profit %", min_value=0.0, max_value=1000.0, value=4.0)
        submit_rt = st.form_submit_button("Show realtime advice for these stocks?")

    if submit_rt:
        tickers = [s.strip() for s in symbols_text.split(",") if s.strip()]
        payload = {
            "tickers": tickers,
            "capital": float(capital),
            "max_position_pct": float(max_position_pct),
            "stop_loss_pct": float(stop_loss_pct),
            "take_profit_pct": float(take_profit_pct),
        }
        with st.spinner("Running realtime advice..."):
            out, err = run_with_timeout(realtime_advice.run_realtime_advice, 10.0, payload, use_daily_fallback=use_daily_fallback)
            if err:
                st.error(f"Realtime advice error: {err}")
                log_trace(f"Realtime advice error: {err}")
            else:
                st.success("Done")
                json_display(out)
                log_trace(f"Ran realtime advice for {len(tickers)} symbols (daily_fallback={use_daily_fallback})")


# ------------------ Rebalance flow ------------------------------------------------
with tabs[3]:
    st.header("Portfolio rebalance helper")
    st.write("Compute suggested trades to drift back to target allocations.")

    with st.form("rebalance_form"):
        try:
            with open("data/mock_portfolio.json") as f:
                portfolio = json.load(f)
        except Exception:
            portfolio = {"holdings": []}

        st.write("Current portfolio (mock):")
        st.json(portfolio)
        drift_threshold = st.number_input("Drift threshold % (only show trades > this)", min_value=0.0, max_value=100.0, value=5.0)

        submit_rb = st.form_submit_button("Show me how to rebalance my portfolio?")

    if submit_rb:
        with st.spinner("Computing rebalance plan..."):
            plan, err = run_with_timeout(rebalancer.compute_rebalance_plan, 8.0, float(drift_threshold))
            if err:
                st.error(f"Rebalance computation error: {err}")
                log_trace(f"Rebalance computation error: {err}")
            else:
                st.success("Done")
                json_display(plan)
                log_trace("Computed rebalance plan")


# --- Trace panel -------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("Trace log")
for t in st.session_state.traces[-50:]:
    st.sidebar.text(t)


# End of app

