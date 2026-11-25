from dataclasses import dataclass
from datetime import date 
import pandas as pd
import yaml

# defining classes
@dataclass
class Settings: 
    initial_balance: float    #starting balance 
    reference_month: date     #month the forecast starts from 
    warning_threshold: float  #below this value, the balance turns red 
    monthly_deposit: float    #recurring montlhy deposit 
    stop_threshold: float
    
@dataclass
class Movement: 
    month: date               #month when the movement happens 
    kind: str                 #'expense' or 'income'
    amount: float             #always positive
    description: str = ""

    #amount and kind check function 
    def __post_init__(self):
        if self.kind not in ("expense", "income"):
            raise ValueError(f"kind must be 'expense' or 'income', got {self.kind}")
        if self.amount <= 0:
            raise ValueError(f"amount must be positive, got {self.amount}")


# Month helpers: convert "YYYY-MM" text into dates and count months between two dates
def parse_month(text: str) -> date:
    """Convert '2026-12' into date(2026, 12, 1)."""
    year, month = str(text).split("-")
    return date(int(year), int(month), 1)

def months_between(start: date, end: date) -> int:
    """Number of months from start to end (month counter)"""
    return (end.year - start.year) * 12 + (end.month - start.month)


# Reader: load the YAML file and build the Settings and Movement objects
def load_spendable(path: str) -> tuple[Settings, list[Movement]]:
    """Read the YAML file and return the settings and the list of movements."""
    with open(path) as f:
        data = yaml.safe_load(f)

    s = data["spendable"]
    settings = Settings(
        initial_balance=float(s["initial_balance"]),
        reference_month=parse_month(s["reference_month"]),
        warning_threshold=float(s["warning_threshold"]),
        stop_threshold=float(s["stop_threshold"]),
        monthly_deposit=float(s["monthly_deposit"]),
    )

    movements = [
        Movement(
            month=parse_month(m["month"]),
            kind=m["kind"],
            amount=float(m["amount"]),
            description=m.get("description", ""),
        )
        for m in data.get("movements", [])
    ]
    return settings, movements


# Series builder: monthly balance from the reference month onward
def add_months(start: date, n: int) -> date:
    """Return the first day of the month n months after start."""
    total = start.year * 12 + (start.month - 1) + n
    return date(total // 12, total % 12 + 1, 1)

# predictions 
def build_balance_series(settings: Settings, movements: list[Movement], n_months: int) -> pd.DataFrame:
    """Balance for each month, from month 0 (reference month) to month n_months."""
    # net one-off amount for each month (income positive, expense negative)
    net = {}
    for m in movements:
        sign = 1 if m.kind == "income" else -1
        net[m.month] = net.get(m.month, 0.0) + sign * m.amount

    rows = []
    balance = settings.initial_balance
    for i in range(n_months + 1):
        month = add_months(settings.reference_month, i)
        if i > 0:
            balance += settings.monthly_deposit + net.get(month, 0.0)
        rows.append({"month": month, "balance": balance})
    return pd.DataFrame(rows)


# amount controller (OK, STOP)
# Alert logic: status of a balance, and first future month that is not "ok"
def get_status(balance: float, settings: Settings) -> str:
    """Return 'stop', 'warning' or 'ok' for a given balance."""
    if balance <= settings.stop_threshold:
        return "stop"
    if balance < settings.warning_threshold:
        return "warning"
    return "ok"


def first_alert(series: pd.DataFrame, settings: Settings):
    """Return (month, status) of the first month that is not 'ok', or None."""
    for row in series.itertuples():
        status = get_status(row.balance, settings)
        if status != "ok":
            return row.month, status
    return None

