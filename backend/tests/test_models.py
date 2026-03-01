from datetime import datetime

import pytest
from pydantic import ValidationError


# This test will fail initially since the new types don't exist yet
def test_alert_types_import():
    """Test that all alert types can be imported and work correctly."""
    from models import AlertRuleIn, AlertRuleOut

    # Test AlertRuleIn creation and validation
    rule_in = AlertRuleIn(metric_name="cpu_usage", operator="gt", threshold=90.0)
    assert rule_in.metric_name == "cpu_usage"
    assert rule_in.operator == "gt"
    assert rule_in.threshold == 90.0

    # Test operator validation
    with pytest.raises(ValidationError):
        AlertRuleIn(metric_name="cpu", operator="invalid", threshold=80.0)

    # Test metric_name length constraints
    with pytest.raises(ValidationError):
        AlertRuleIn(metric_name="", operator="gt", threshold=80.0)  # too short

    with pytest.raises(ValidationError):
        AlertRuleIn(metric_name="x" * 129, operator="gt", threshold=80.0)  # too long

    # Test AlertRuleOut creation with defaults
    rule_out = AlertRuleOut(
        id="test-rule-1", metric_name="memory_usage", operator="lt", threshold=50.0
    )
    assert rule_out.id == "test-rule-1"
    assert rule_out.metric_name == "memory_usage"
    assert rule_out.operator == "lt"
    assert rule_out.threshold == 50.0
    assert rule_out.state == "ok"  # default value
    assert isinstance(rule_out.created_at, datetime)

    # Test state validation
    rule_out_firing = AlertRuleOut(
        id="test-rule-2", metric_name="cpu", operator="eq", threshold=100.0, state="firing"
    )
    assert rule_out_firing.state == "firing"

    # Test invalid state
    with pytest.raises(ValidationError):
        AlertRuleOut(
            id="test-rule-3",
            metric_name="cpu",
            operator="gt",
            threshold=80.0,
            state="invalid_state",
        )


def test_alert_operator_literals():
    """Test AlertOperator literal type values."""
    from models import AlertRuleIn

    # These should be the valid literal values
    valid_operators = ["gt", "lt", "eq"]
    for op in valid_operators:
        rule = AlertRuleIn(metric_name="test", operator=op, threshold=50.0)
        assert rule.operator == op


def test_alert_state_literals():
    """Test AlertState literal type values."""
    from models import AlertRuleOut

    # These should be the valid literal values
    valid_states = ["ok", "firing"]
    for state in valid_states:
        rule = AlertRuleOut(
            id="test", metric_name="test", operator="gt", threshold=50.0, state=state
        )
        assert rule.state == state
