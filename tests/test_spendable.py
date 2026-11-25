from datetime import date

import pytest

from src.spendable import (
    Settings,
    Movement,
    build_balance_series,
    first_alert,
    get_status,
)


def make_settings():
    return Settings(
        initial_balance=3200,
        reference_month=date(2026, 11, 1),
        warning_threshold=100,
        stop_threshold=0,
        monthly_deposit=50,
    )


def make_movements(fees):
    return [
        Movement(month=date(2026, 12, 1), kind="expense", amount=400),
        Movement(month=date(2027, 1, 1), kind="expense", amount=fees),
        Movement(month=date(2027, 3, 1), kind="income", amount=200),
    ]


def test_status_levels():
    s = make_settings()
    assert get_status(500, s) == "ok"
    assert get_status(50, s) == "warning"
    assert get_status(0, s) == "stop"
    assert get_status(-20, s) == "stop"


def test_balance_series_values():
    series = build_balance_series(make_settings(), make_movements(900), 6)
    assert list(series["balance"]) == [3200, 2850, 2000, 2050, 2300, 2350, 2400]


def test_no_alert_when_balance_stays_high():
    series = build_balance_series(make_settings(), make_movements(900), 12)
    assert first_alert(series, make_settings()) is None


def test_warning_alert():
    series = build_balance_series(make_settings(), make_movements(2850), 12)
    assert first_alert(series, make_settings()) == (date(2027, 1, 1), "warning")


def test_stop_alert():
    series = build_balance_series(make_settings(), make_movements(2900), 12)
    assert first_alert(series, make_settings()) == (date(2027, 1, 1), "stop")


def test_negative_amount_is_rejected():
    with pytest.raises(ValueError):
        Movement(month=date(2026, 12, 1), kind="expense", amount=-10)


def test_wrong_kind_is_rejected():
    with pytest.raises(ValueError):
        Movement(month=date(2026, 12, 1), kind="gift", amount=10)