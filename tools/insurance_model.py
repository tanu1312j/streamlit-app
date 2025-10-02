# streamlit_app/tools/insurance_model.py
from core.schemas import InsuranceInput
from typing import Dict, Union


def run_insurance_model(inp: Union[InsuranceInput, Dict]) -> Dict:
    """Return simple insurance recommendations.

    Accepts either a `InsuranceInput` instance or a plain dict.
    """
    if isinstance(inp, dict):
        inp = InsuranceInput(**inp)

    # Swap this for your classifier/regressor
    ideal_term_cover = max(inp.annual_income * 10, 2_500_000)
    if inp.demo.dependents >= 2:
        ideal_term_cover = int(ideal_term_cover * 1.2)

    existing_term = inp.existing_covers.get("term", {}).get("sum_assured", 0)
    term_gap = max(int(ideal_term_cover - existing_term), 0)

    base_health = 500_000 if inp.demo.city else 300_000
    if inp.has_employer_health:
        base_health = max(int(base_health - inp.employer_health_cover), 0)
    health_gap = max(int(base_health), 0)

    return {
        "term_cover_needed": int(ideal_term_cover),
        "term_cover_gap": int(term_gap),
        "health_cover_recommended": int(base_health),
        "health_gap": int(health_gap),
        "notes": [
            "Aim 10–15× annual income for term life.",
            "Top-up health plan if employer cover < recommended.",
        ],
    }
