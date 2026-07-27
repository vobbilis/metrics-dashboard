import math
import uuid
from collections import deque

from models import AlertEvent, AlertRuleIn, AlertRuleOut, AlertRuleUpdate
from store import MetricStore


class AlertStore:
    def __init__(self) -> None:
        self._rules: list[AlertRuleOut] = []
        self._events: deque[AlertEvent] = deque(maxlen=200)

    def add_rule(self, rule: AlertRuleIn) -> AlertRuleOut:
        out = AlertRuleOut(
            id=str(uuid.uuid4()),
            metric_name=rule.metric_name,
            operator=rule.operator,
            threshold=rule.threshold,
            state="ok",
        )
        self._rules.append(out)
        return out

    def all_rules(self) -> list[AlertRuleOut]:
        return list(self._rules)

    def delete_rule(self, rule_id: str) -> int:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.id != rule_id]
        return before - len(self._rules)

    def delete_rules_by_metric_name(self, metric_name: str) -> int:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.metric_name != metric_name]
        return before - len(self._rules)

    def update_rule(self, rule_id: str, update: AlertRuleUpdate) -> AlertRuleOut | None:
        for rule in self._rules:
            if rule.id == rule_id:
                if update.metric_name is not None:
                    rule.metric_name = update.metric_name
                if update.operator is not None:
                    rule.operator = update.operator
                if update.threshold is not None:
                    rule.threshold = update.threshold
                rule.state = "ok"
                return rule
        return None

    def all_events(self) -> list[AlertEvent]:
        return list(self._events)

    def clear(self) -> None:
        self._rules = []
        self._events = deque(maxlen=200)

    def evaluate(self, metric_store: MetricStore) -> list[tuple[str, str, str]]:
        """Evaluate all rules against latest metric values. Returns state transitions."""
        transitions: list[tuple[str, str, str]] = []

        for rule in self._rules:
            # Get metrics for this rule's metric name
            metrics = metric_store.by_name(rule.metric_name)

            if not metrics:
                # No data → not firing
                new_state = "ok"
            else:
                # Get latest value and compare with threshold
                latest = metrics[-1].value

                if rule.operator == "gt":
                    new_state = "firing" if latest > rule.threshold else "ok"
                elif rule.operator == "lt":
                    new_state = "firing" if latest < rule.threshold else "ok"
                elif rule.operator == "eq":
                    is_close = math.isclose(latest, rule.threshold, rel_tol=1e-6)
                    new_state = "firing" if is_close else "ok"
                else:
                    new_state = "ok"  # Unknown operator, default to ok

            # Check for state transition
            if new_state != rule.state:
                self._events.append(
                    AlertEvent(
                        rule_id=rule.id,
                        metric_name=rule.metric_name,
                        old_state=rule.state,
                        new_state=new_state,
                    )
                )
                transitions.append((rule.id, rule.state, new_state))
                rule.state = new_state

        return transitions
