from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Annotated


class Demographics(BaseModel):
    age: int = Field(..., ge=18, le=100)
    country: str = "India"
    city: Optional[str] = None
    marital_status: Optional[str] = None
    dependents: int = Field(0, ge=0)
    risk_score: int = Field(3, ge=1, le=5)


class SavingsInput(BaseModel):
    demo: Demographics
    monthly_income_fixed: Annotated[float, Field(..., ge=0)]
    monthly_income_variable: Annotated[float, Field(0, ge=0)] = 0
    fixed_expenses: Annotated[float, Field(..., ge=0)]
    variable_expenses: Annotated[float, Field(..., ge=0)]
    existing_savings: Annotated[float, Field(0, ge=0)] = 0
    existing_debt: Annotated[float, Field(0, ge=0)] = 0
    emergency_fund_months_target: Annotated[float, Field(6, ge=0, le=24)] = 6
    goals_months: Dict[str, int] = Field(
        default_factory=lambda: {"short": 12, "medium": 36, "long": 84}
    )


class InsuranceInput(BaseModel):
    demo: Demographics
    annual_income: Annotated[float, Field(..., ge=0)]
    has_employer_health: bool = False
    employer_health_cover: Annotated[float, Field(0, ge=0)] = 0
    existing_covers: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class RTAdviceInput(BaseModel):
    tickers: Annotated[List[str], Field(..., min_items=1)]
    capital: Annotated[float, Field(..., ge=0)]
    max_position_pct: Annotated[float, Field(10, ge=1, le=100)] = 10
    horizon: str  # "intraday"|"swing"|"position"
    risk_score: Annotated[int, Field(..., ge=1, le=5)]
    stop_loss_pct: Annotated[float, Field(2.0, ge=0, le=50)] = 2.0
    take_profit_pct: Annotated[float, Field(4.0, ge=0, le=200)] = 4.0
    leverage_allowed: bool = False
    constraints: Dict[str, bool] = Field(default_factory=dict)  # {"no_short":True}
    news_sensitivity: str = "medium"
    paper_only: bool = True


class Holding(BaseModel):
    symbol: str
    qty: Annotated[float, Field(..., ge=0)]
    price: Annotated[float, Field(..., ge=0)]


class Portfolio(BaseModel):
    cash: Annotated[float, Field(100000.0, ge=0)] = 100000.0
    holdings: List[Holding] = Field(default_factory=list)
    targets: Dict[str, float] = Field(default_factory=dict)  # symbol -> target %
    drift_threshold_pct: Annotated[float, Field(5.0, ge=0, le=50)] = 5.0
    rebalance_frequency_days: Annotated[int, Field(30, ge=1, le=365)] = 30
