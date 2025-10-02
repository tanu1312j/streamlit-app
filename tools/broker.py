"""mock broker + portfolio store"""
from pathlib import Path
import json
from core.schemas import Portfolio

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "mock_portfolio.json"

def load_portfolio() -> Portfolio:
    if not DATA_PATH.exists():
        # return an empty portfolio if file missing
        return Portfolio()
    with DATA_PATH.open("r") as f:
        return Portfolio(**json.load(f))
