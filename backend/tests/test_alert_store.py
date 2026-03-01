from alert_store import AlertStore
from models import AlertRuleIn, MetricIn
from store import MetricStore


def test_evaluate_no_metrics():
    """Rules with no matching metrics should stay in 'ok' state."""
    metric_store = MetricStore()
    alert_store = AlertStore()

    # Add rule but no metrics
    rule = alert_store.add_rule(AlertRuleIn(metric_name="cpu", operator="gt", threshold=80.0))

    # Evaluate - should return no transitions
    transitions = alert_store.evaluate(metric_store)
    assert transitions == []
    assert rule.state == "ok"


def test_evaluate_gt_operator():
    """Test 'gt' operator fires when latest > threshold."""
    metric_store = MetricStore()
    alert_store = AlertStore()

    rule = alert_store.add_rule(AlertRuleIn(metric_name="cpu", operator="gt", threshold=80.0))

    # Add metric above threshold
    metric_store.add(MetricIn(name="cpu", value=95.0))

    # Should transition from ok -> firing
    transitions = alert_store.evaluate(metric_store)
    assert len(transitions) == 1
    assert transitions[0] == (rule.id, "ok", "firing")
    assert rule.state == "firing"

    # Evaluate again - no change expected
    transitions = alert_store.evaluate(metric_store)
    assert transitions == []

    # Add metric below threshold
    metric_store.add(MetricIn(name="cpu", value=50.0))

    # Should transition from firing -> ok
    transitions = alert_store.evaluate(metric_store)
    assert len(transitions) == 1
    assert transitions[0] == (rule.id, "firing", "ok")
    assert rule.state == "ok"


def test_evaluate_lt_operator():
    """Test 'lt' operator fires when latest < threshold."""
    metric_store = MetricStore()
    alert_store = AlertStore()

    rule = alert_store.add_rule(AlertRuleIn(metric_name="memory", operator="lt", threshold=20.0))

    # Add metric below threshold
    metric_store.add(MetricIn(name="memory", value=15.0))

    transitions = alert_store.evaluate(metric_store)
    assert len(transitions) == 1
    assert transitions[0] == (rule.id, "ok", "firing")
    assert rule.state == "firing"


def test_evaluate_eq_operator():
    """Test 'eq' operator fires when latest == threshold."""
    metric_store = MetricStore()
    alert_store = AlertStore()

    rule = alert_store.add_rule(AlertRuleIn(metric_name="disk", operator="eq", threshold=100.0))

    # Add metric equal to threshold
    metric_store.add(MetricIn(name="disk", value=100.0))

    transitions = alert_store.evaluate(metric_store)
    assert len(transitions) == 1
    assert transitions[0] == (rule.id, "ok", "firing")
    assert rule.state == "firing"


def test_evaluate_multiple_rules():
    """Test evaluation with multiple rules and different scenarios."""
    metric_store = MetricStore()
    alert_store = AlertStore()

    rule1 = alert_store.add_rule(AlertRuleIn(metric_name="cpu", operator="gt", threshold=80.0))
    rule2 = alert_store.add_rule(AlertRuleIn(metric_name="memory", operator="lt", threshold=20.0))
    rule3 = alert_store.add_rule(AlertRuleIn(metric_name="disk", operator="eq", threshold=100.0))

    # Add metrics that trigger rule1 and rule3
    metric_store.add(MetricIn(name="cpu", value=95.0))  # triggers rule1 (95 > 80)
    metric_store.add(MetricIn(name="memory", value=50.0))  # doesn't trigger rule2 (50 not < 20)
    metric_store.add(MetricIn(name="disk", value=100.0))  # triggers rule3 (100 == 100)

    transitions = alert_store.evaluate(metric_store)
    assert len(transitions) == 2

    # Check individual transitions
    transition_ids = [(t[0], t[1], t[2]) for t in transitions]
    assert (rule1.id, "ok", "firing") in transition_ids
    assert (rule3.id, "ok", "firing") in transition_ids

    # Check states updated
    assert rule1.state == "firing"
    assert rule2.state == "ok"
    assert rule3.state == "firing"
