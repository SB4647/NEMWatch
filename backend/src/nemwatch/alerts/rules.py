from datetime import datetime
from decimal import Decimal

from nemwatch.domain.models import Alert, AlertRule, AlertRuleType, DispatchRecord


def _alert(rule: AlertRule, current: DispatchRecord, observed: Decimal, message: str) -> Alert:
    return Alert(
        idempotency_key=f"{rule.rule_key}|{current.region.value}|{current.interval_datetime.isoformat()}",
        rule_key=rule.rule_key, rule_type=rule.rule_type, region=current.region,
        interval_datetime=current.interval_datetime, severity=rule.severity,
        message=message, observed_value=observed, threshold=rule.threshold,
    )


def evaluate_alerts(
    current: DispatchRecord,
    previous: DispatchRecord | None,
    now: datetime,
    rules: list[AlertRule],
) -> tuple[Alert, ...]:
    alerts: list[Alert] = []
    for rule in rules:
        if not rule.enabled or (rule.region is not None and rule.region != current.region):
            continue
        if rule.rule_type is AlertRuleType.HIGH_PRICE and current.price > rule.threshold:
            alerts.append(_alert(rule, current, current.price, f"{current.region.value} price exceeded ${rule.threshold}/MWh"))
        elif rule.rule_type is AlertRuleType.RAPID_DEMAND_CHANGE and previous is not None:
            change = abs(current.demand - previous.demand)
            if rule.config.get("mode") == "percentage":
                observed = Decimal("0") if previous.demand == 0 else change / abs(previous.demand) * Decimal("100")
            else:
                observed = change
            if observed > rule.threshold:
                alerts.append(_alert(rule, current, observed, f"{current.region.value} demand changed rapidly"))
        elif rule.rule_type is AlertRuleType.STALE_DATA:
            age_minutes = Decimal(str((now - current.interval_datetime).total_seconds() / 60))
            if age_minutes > rule.threshold:
                alerts.append(_alert(rule, current, age_minutes, f"{current.region.value} dispatch data is stale"))
    return tuple(alerts)
