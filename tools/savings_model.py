# streamlit_app/tools/savings_model.py
from core.schemas import SavingsInput
from typing import Dict, Union


def run_savings_model(inp: Union[SavingsInput, Dict]) -> Dict:
    """Run a simple heuristic savings calculator.

    Accepts either a `SavingsInput` instance or a plain dict (useful when called
    from an agent that serializes arguments).
    """
    # allow dict inputs (e.g. coming from an agent/runtime)
    if isinstance(inp, dict):
        inp = SavingsInput(**inp)

    # Replace this block with your real ML model call
    monthly_income = inp.monthly_income_fixed + inp.monthly_income_variable
    monthly_spend = inp.fixed_expenses + inp.variable_expenses
    base_saving = max(monthly_income - monthly_spend, 0)
    # Heuristic boost by risk tolerance and emergency fund status
    buffer_needed = inp.emergency_fund_months_target * monthly_spend
    buffer_gap = max(buffer_needed - inp.existing_savings, 0)
    target_saving = base_saving * (1 + 0.05 * (inp.demo.risk_score - 3))
    return {
        "monthly_income": round(monthly_income, 2),
        "monthly_spend": round(monthly_spend, 2),
        "suggested_monthly_saving": round(target_saving, 2),
        "emergency_buffer_gap": round(buffer_gap, 2),
    }
