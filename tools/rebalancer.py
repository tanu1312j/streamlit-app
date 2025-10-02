# simple rebalancing logic + order plan
from tools.broker import load_portfolio
from tools.market_data import get_prices_yf
from typing import Union


def compute_rebalance_plan(drift_threshold_pct: float = 5.0, payload: Union[dict, None] = None):
    """Compute a simple rebalance plan.

    If `payload` is provided (from an agent), it is ignored currently but accepted
    so the function can be wrapped by StructuredTool.from_function.
    """
    p = load_portfolio()
    symbols = [h.symbol for h in p.holdings]
    prices = get_prices_yf(symbols)
    values = {}
    for h in p.holdings:
        # prefer fetched price, fall back to recorded holding price, finally 0
        fetched = prices.get(h.symbol) if prices is not None else None
        use_price = fetched if (fetched is not None) else (h.price if h.price is not None else 0.0)
        try:
            values[h.symbol] = h.qty * float(use_price)
        except Exception:
            # defensive: if anything unexpected, set to zero
            values[h.symbol] = 0.0
    total_value = p.cash + sum(values.values())
    if total_value == 0:
        current_w = {s: 0.0 for s in values.keys()}
    else:
        current_w = {s: (v / total_value) * 100 for s, v in values.items()}
    plan = []
    for s, target_pct in p.targets.items():
        drift = current_w.get(s, 0.0) - target_pct
        if abs(drift) >= drift_threshold_pct:
            plan.append({"symbol": s, "drift": round(drift, 2)})
    return {
        "total_value": round(total_value, 2),
        "current_weights": current_w,
        "plan": plan,
    }
