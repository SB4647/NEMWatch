from datetime import UTC, datetime, timedelta
from decimal import Decimal

from nemwatch.alerts.rules import evaluate_alerts
from nemwatch.domain.models import AlertRule, AlertRuleType, DispatchRecord, Region


def record(price: str = "100", demand: str = "1000", minutes_ago: int = 0) -> DispatchRecord:
    return DispatchRecord(
        region=Region.QLD1,
        interval_datetime=datetime(2026, 9, 19, tzinfo=UTC) - timedelta(minutes=minutes_ago),
        price=Decimal(price), demand=Decimal(demand), source_file="fixture.csv", source_row=2,
    )


def test_high_price_is_strictly_above_threshold() -> None:
    rule = AlertRule(rule_key="high", rule_type=AlertRuleType.HIGH_PRICE, threshold=Decimal("300"))
    assert evaluate_alerts(record(price="300"), None, datetime(2026, 9, 19, tzinfo=UTC), [rule]) == ()
    assert len(evaluate_alerts(record(price="301"), None, datetime(2026, 9, 19, tzinfo=UTC), [rule])) == 1


def test_rapid_demand_percentage_handles_zero_baseline() -> None:
    rule = AlertRule(rule_key="rapid", rule_type=AlertRuleType.RAPID_DEMAND_CHANGE, threshold=Decimal("10"), config={"mode": "percentage"})
    assert evaluate_alerts(record(demand="100"), record(demand="0"), datetime(2026, 9, 19, tzinfo=UTC), [rule]) == ()


def test_stale_data_uses_age_in_minutes() -> None:
    rule = AlertRule(rule_key="stale", rule_type=AlertRuleType.STALE_DATA, threshold=Decimal("15"))
    assert len(evaluate_alerts(record(minutes_ago=16), None, datetime(2026, 9, 19, tzinfo=UTC), [rule])) == 1
