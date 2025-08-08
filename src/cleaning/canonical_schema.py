# from pydantic import BaseModel, Field, validator
# from typing import Dict, List, Optional

# class Series(BaseModel):
#     values: Dict[str, Optional[float]]  # {"YYYY-MM-DD": number|null}

# class Period(BaseModel):
#     label: str
#     start_date: Optional[str]
#     end_date: str
#     fy: Optional[int]
#     fp: str  # Q1|Q2|Q3|Q4|FY
#     is_audited: Optional[bool] = None

# class FinancialBlock(BaseModel):
#     # add as needed; None means optional in output
#     Revenue: Optional[Series] = None
#     CostOfRevenue: Optional[Series] = None
#     GrossProfit: Optional[Series] = None
#     OperatingExpenses: Optional[Series] = None
#     OperatingIncome: Optional[Series] = None
#     InterestExpense: Optional[Series] = None
#     OtherIncomeExpenseNet: Optional[Series] = None
#     PretaxIncome: Optional[Series] = None
#     IncomeTaxExpense: Optional[Series] = None
#     NetIncome: Optional[Series] = None

# class BalanceBlock(BaseModel):
#     CashAndCashEquivalents: Optional[Series] = None
#     ShortTermInvestments: Optional[Series] = None
#     AccountsReceivableNet: Optional[Series] = None
#     Inventory: Optional[Series] = None
#     TotalCurrentAssets: Optional[Series] = None
#     PPENet: Optional[Series] = None
#     TotalAssets: Optional[Series] = None
#     AccountsPayable: Optional[Series] = None
#     TotalCurrentLiabilities: Optional[Series] = None
#     LongTermDebt: Optional[Series] = None
#     TotalLiabilities: Optional[Series] = None
#     CommonStockAndAPIC: Optional[Series] = None
#     RetainedEarnings: Optional[Series] = None
#     TotalEquity: Optional[Series] = None

# class CashFlowBlock(BaseModel):
#     NetCashFromOperations: Optional[Series] = None
#     NetCashFromInvesting: Optional[Series] = None
#     NetCashFromFinancing: Optional[Series] = None
#     DepreciationAndAmortization: Optional[Series] = None
#     ShareBasedCompensation: Optional[Series] = None
#     CapitalExpenditures: Optional[Series] = None
#     DividendsPaid: Optional[Series] = None
#     NetChangeInCash: Optional[Series] = None

# class Payload(BaseModel):
#     company: Dict[str, Optional[str]]
#     currency: str
#     scale: int
#     periods: List[Period]
#     income_statement: Dict[str, Series]
#     balance_sheet: Dict[str, Series]
#     cash_flow: Dict[str, Series]
#     notes: List[Dict[str, str]] = []

#     @validator('scale')
#     def check_scale(cls, v):
#         if v not in (1, 1_000, 1_000_000, 1_000_000_000):
#             raise ValueError("scale must be 1, 1e3, 1e6, or 1e9")
#         return v


from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional

class Series(BaseModel):
    values: Dict[str, Optional[float]]  # {"YYYY-MM-DD": number|null}

class Period(BaseModel):
    label: str
    start_date: Optional[str]
    end_date: str
    fy: Optional[int]
    fp: str  # Q1|Q2|Q3|Q4|FY
    is_audited: Optional[bool] = None

class Payload(BaseModel):
    company: Dict[str, Optional[str]]
    currency: str
    scale: int
    periods: List[Period]
    income_statement: Dict[str, Series]
    balance_sheet: Dict[str, Series]
    cash_flow: Dict[str, Series]
    notes: List[Dict[str, str]] = []

    @validator('scale')
    def check_scale(cls, v):
        if v not in (1, 1_000, 1_000_000, 1_000_000_000):
            raise ValueError("scale must be 1, 1e3, 1e6, or 1e9")
        return v
