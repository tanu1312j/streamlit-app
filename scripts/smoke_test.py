import json
import traceback

from core.schemas import Demographics, SavingsInput, InsuranceInput
from tools.savings_model import run_savings_model
from tools.insurance_model import run_insurance_model
from tools.realtime_advice import run_realtime_advice
from tools.rebalancer import compute_rebalance_plan


def safe(fn, *a, **k):
    try:
        r = fn(*a, **k)
        print(fn.__name__, "OK", json.dumps(r, default=str))
    except Exception as e:
        print(fn.__name__, "ERR", str(e))
        traceback.print_exc()


def main():
    demo = Demographics(age=30, country='India', city='Bengaluru', dependents=0, risk_score=3)
    si = SavingsInput(
        demo=demo,
        monthly_income_fixed=50000,
        monthly_income_variable=0,
        fixed_expenses=20000,
        variable_expenses=5000,
        existing_savings=100000,
        existing_debt=0,
        emergency_fund_months_target=6,
    )
    safe(run_savings_model, si)

    ii = InsuranceInput(demo=demo, annual_income=600000, has_employer_health=False, employer_health_cover=0, existing_covers={})
    safe(run_insurance_model, ii)

    # realtime may attempt network calls — it's okay if prices are None
    safe(run_realtime_advice, {"tickers": ["INFY.NS", "TCS.NS"], "capital": 100000, "max_position_pct": 10, "stop_loss_pct": 2.0, "take_profit_pct": 4.0})

    safe(compute_rebalance_plan)


if __name__ == '__main__':
    main()
