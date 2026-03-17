# Plan: Alert Management UI and Firing History

> **Status:** COMPLETE (2026-03-17)
> All 14 tasks completed. 97/97 backend tests passing. 55/55 frontend tests passing. Validated by agent team with build evidence.

## Build Evidence

> **Status:** COMPLETE
> **Date:** 2026-03-17
> **Team:** alert-management-20260317-0930

### Test Results
- backend/tests/test_api.py — 87/87 PASSED
- backend/tests/test_alert_store.py — 13/13 PASSED
- backend/tests/test_evaluate_loop.py — 1/1 PASSED
- backend/tests/test_models.py — 3/3 PASSED (total: 97/97 backend tests)
- frontend/src/App.test.tsx — 23/23 PASSED
- frontend/src/api.test.ts — 14/14 PASSED
- frontend/src/components/MetricCard.test.tsx — 9/9 PASSED
- frontend/src/components/SparklineChart.test.tsx — 4/4 PASSED
- frontend/src/components/TimeRangeBar.test.tsx — 5/5 PASSED (total: 55/55 frontend tests)

### Validation Commands
- `cd backend && ruff check .` — PASS (All checks passed!)
- `cd backend && python3.11 -m pytest tests/ -v` — PASS (97 passed in 3.05s)
- `cd frontend && npx tsc --noEmit` — PASS (no errors)
- `cd frontend && npx vitest run` — PASS (5 test files, 55 tests passed)

### Acceptance Criteria Verification
- [x] PUT /alerts/{id} updates rule, resets state, returns 404 for nonexistent — VERIFIED (tests test_update_alert_rule, test_update_alert_rule_partial, test_update_alert_rule_not_found, test_update_alert_resets_state all pass; route at main.py:239)
- [x] GET /alerts/events returns event list — VERIFIED (tests test_get_alert_events_empty, test_get_alert_events_after_transition, test_alert_events_multiple_transitions all pass; route at main.py:234)
- [x] Event deque caps at 200 — VERIFIED (deque(maxlen=200) at alert_store.py:12; test_alert_events_cap_at_200 passes)
- [x] AlertPanel.tsx exists with create/edit/delete/history — VERIFIED (file exists at frontend/src/components/AlertPanel.tsx)
- [x] App.tsx uses AlertPanel, polls events — VERIFIED (imports AlertPanel at line 3, renders at line 134; fetches alertEvents via fetchAlertEvents at line 56)
- [x] All tests pass, ruff/tsc/eslint clean — VERIFIED (97/97 backend, 55/55 frontend, ruff clean, tsc clean)

### Files Changed
| File | Action | Verified |
|------|--------|----------|
| backend/models.py | Modified (AlertEvent, AlertRuleUpdate models) | Yes |
| backend/alert_store.py | Modified (event deque, update_rule, all_events) | Yes |
| backend/main.py | Modified (PUT /alerts/{id}, GET /alerts/events) | Yes |
| backend/tests/test_api.py | Modified (new endpoint tests) | Yes |
| frontend/src/api.ts | Modified (AlertEvent type, updateAlert, fetchAlertEvents) | Yes |
| frontend/src/components/AlertPanel.tsx | Created | Yes |
| frontend/src/App.tsx | Modified (AlertPanel integration, event polling) | Yes |
| frontend/src/App.test.tsx | Modified (AlertPanel tests) | Yes |
| frontend/src/dashboard.css | Modified (AlertPanel styles) | Yes |
| docs/design/metrics.md | Modified (design doc update) | Yes |

> **EXECUTION DIRECTIVE**: This is a team-orchestrated plan.
> **FORBIDDEN**: Direct implementation (Edit, Write, NotebookEdit) by the main agent. If you are the main conversation agent and a user asks you to implement this plan, you MUST invoke `/build_v2 specs/alert-management-ui-and-history.md` -- do NOT implement it yourself.
> **REQUIRED**: Execute ONLY via the `/build_v2` command, which deploys team agents to do the work.

## Task Description

Add full alert management UI and alert firing history to the metrics dashboard. This involves:

**Backend changes:**
1. An alert event log (capped `deque` at 200 entries) recording state transitions in `evaluate()` — each event captures rule ID, metric name, old state, new state, and timestamp.
2. `PUT /alerts/{id}` endpoint for editing existing alert rules (metric_name, operator, threshold).
3. `GET /alerts/events` endpoint returning the alert event history.

**Frontend changes:**
1. New `AlertPanel` component with:
   - Create/edit/delete alert forms
   - Alert rules list with state badges (ok/firing)
   - Alert history timeline showing recent ok->firing and firing->ok transitions
2. New API client functions: `updateAlert()`, `fetchAlertEvents()`
3. Replace the inline alerts section in `App.tsx` with the new `AlertPanel`

## Objective

When this plan is complete, users will be able to create, edit, and delete alert rules through a dedicated AlertPanel UI, see real-time alert states with visual badges, and view a timeline of recent alert state transitions. The backend will persistently track the last 200 state transition events and expose them via API.

## Problem Statement

The current alerting system (Phase 1) only supports creating and deleting rules via API, with a minimal inline display in `App.tsx` that shows rule state but offers no edit capability, no creation form, and no history of when alerts fired or recovered. Users cannot see when an alert started firing or when it resolved, making it difficult to understand system behavior over time.

## Solution Approach

**Backend**: Extend `AlertStore` with a `collections.deque(maxlen=200)` that records `AlertEvent` objects (Pydantic model with `rule_id`, `metric_name`, `old_state`, `new_state`, `timestamp`) on every state transition in `evaluate()`. Add a `PUT /alerts/{id}` endpoint that updates an existing rule's `metric_name`, `operator`, and `threshold` fields (resetting state to "ok"). Add `GET /alerts/events` endpoint returning the event deque as a list. Add a new `AlertRuleUpdate` Pydantic model for the PUT body (all fields optional).

**Frontend**: Create a new `AlertPanel` component that encapsulates all alert functionality: a form for creating/editing rules, a list of current rules with state badges and edit/delete actions, and a timeline of recent events. Add `updateAlert()` and `fetchAlertEvents()` to `api.ts`. The `AlertPanel` receives alerts and events as props from `App.tsx` (following the lifted-state pattern from DD-004/DD-013). Replace the inline alerts section in `App.tsx` with `<AlertPanel>`.

## Relevant Files

- `backend/models.py` — Add `AlertEvent` model and `AlertRuleUpdate` model. Existing alert models: `AlertRuleIn`, `AlertRuleOut`, `AlertOperator`, `AlertState` (lines 7-42).
- `backend/alert_store.py` — Add event deque, modify `evaluate()` to record events, add `update_rule()` method, add `all_events()` method. Current evaluate returns transitions but doesn't persist them (lines 39-69).
- `backend/main.py` — Add `PUT /alerts/{id}` and `GET /alerts/events` routes. Existing alert routes at lines 211-224.
- `backend/tests/test_api.py` — Add tests for PUT and GET /alerts/events endpoints. Existing test patterns with `client = TestClient(app)` and `clear_store` autouse fixture.
- `frontend/src/api.ts` — Add `AlertEvent` interface, `updateAlert()`, `fetchAlertEvents()` functions. Existing alert types at lines 3-19, alert functions at lines 88-103.
- `frontend/src/App.tsx` — Add `alertEvents` state, load events in polling loop, replace inline alerts section with `<AlertPanel>`. Current inline alerts section at lines 120-142.
- `frontend/src/App.test.tsx` — Update tests that reference the inline alerts section to work with AlertPanel. Current alert tests at lines 47-127.
- `frontend/src/dashboard.css` — Add AlertPanel styles. Existing alert styles at lines 273-341.
- `frontend/src/alerts.css` — May need updates or can be absorbed into dashboard.css.

### New Files

- `frontend/src/components/AlertPanel.tsx` — New component containing alert management UI (create/edit forms, rules list, history timeline).

## Implementation Phases

### Phase 1: Foundation (Backend Models & Store)
Add `AlertEvent` and `AlertRuleUpdate` Pydantic models. Extend `AlertStore` with event deque, `update_rule()` method, and modify `evaluate()` to record events. This is the data layer everything depends on.

### Phase 2: Backend API
Add `PUT /alerts/{id}` and `GET /alerts/events` routes in `main.py`. Add backend tests for the new endpoints.

### Phase 3: Frontend API & Component
Add new TypeScript types and API functions. Build the `AlertPanel` component. Integrate into `App.tsx` replacing the inline section. Update frontend tests.

## Team Orchestration

- The `/build_v2` command deploys a **self-organizing agent team**. Agents autonomously discover, claim, and execute tasks from a shared task list.
- You are responsible for designing the team composition and task graph so agents can work autonomously.
- IMPORTANT: The plan is the **single source of truth**. `/build_v2` is a pure executor — it does NOT make decisions. Everything must be specified here: team members, task assignments, dependencies, and exhaustive task descriptions.
- **`Assigned To` is enforced**: `/build_v2` injects each agent's name into their standing orders. Agents only claim tasks where `Assigned To` matches their own name. Every task MUST have an `Assigned To`.
- Agents cannot ask for clarification mid-task. Every task description must be fully self-contained with all context needed for autonomous execution.

### Team Members

- Builder
  - Name: builder-backend
  - Role: Backend models, alert store changes, API routes, backend tests
  - Agent Type: general-purpose
- Builder
  - Name: builder-frontend
  - Role: Frontend API client, AlertPanel component, App.tsx integration, CSS, frontend tests
  - Agent Type: general-purpose
- Validator
  - Name: validator
  - Role: Validates all acceptance criteria and runs validation commands
  - Agent Type: validator
- Design Updater
  - Name: design-updater
  - Role: Updates docs/design/metrics.md with code-aligned design decisions after build completes
  - Agent Type: design-updater

## Step by Step Tasks

- These tasks are executed by self-organizing agents. Agents discover and claim tasks autonomously from the shared task list.
- Each task maps directly to a `TaskCreate` call made by `/build_v2`.
- Task descriptions must be **exhaustive** — agents cannot ask for clarification. Include ALL context: file paths, code patterns, acceptance criteria, and validation commands.
- Every task MUST have an `Assigned To` matching a name in Team Members. This is enforced — tasks without a valid `Assigned To` will not be claimed.
- Start with foundational work, then core implementation, then validation.

### 1. Add AlertEvent and AlertRuleUpdate Models
- **Task ID**: add-alert-event-models
- **Role**: builder
- **Depends On**: none
- **Assigned To**: builder-backend
- **Description**: |
    Add two new Pydantic models to `backend/models.py` for the alert event log and rule editing features.

    ## What to do
    1. Add `AlertEvent(BaseModel)` after the existing `AlertRuleOut` class (after line 42) with these fields:
       - `rule_id: str`
       - `metric_name: str`
       - `old_state: AlertState`
       - `new_state: AlertState`
       - `timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))`
    2. Add `AlertRuleUpdate(BaseModel)` after `AlertEvent` with these fields (all optional for partial updates):
       - `metric_name: str | None = None`
       - `operator: AlertOperator | None = None`
       - `threshold: float | None = None`

    ## Files to modify
    - `backend/models.py` — Add `AlertEvent` and `AlertRuleUpdate` classes after `AlertRuleOut`.

    ## Code patterns to follow
    Follow the existing pattern in `backend/models.py`:
    ```python
    class AlertRuleOut(BaseModel):
        id: str
        metric_name: str
        operator: AlertOperator
        threshold: float
        state: AlertState = "ok"
        created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ```
    Use `Field(default_factory=...)` for computed defaults. Use explicit type annotations.

    ## Acceptance criteria
    - `AlertEvent` model exists with fields: `rule_id`, `metric_name`, `old_state`, `new_state`, `timestamp`
    - `AlertRuleUpdate` model exists with all-optional fields: `metric_name`, `operator`, `threshold`
    - `from models import AlertEvent, AlertRuleUpdate` succeeds
    - `ruff check backend/models.py` passes

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && python3.11 -c "
    from models import AlertEvent, AlertRuleUpdate, AlertState
    e = AlertEvent(rule_id='r1', metric_name='cpu', old_state='ok', new_state='firing')
    print(f'Event: {e}')
    assert e.rule_id == 'r1'
    assert e.timestamp is not None
    u = AlertRuleUpdate()
    print(f'Update empty: {u}')
    assert u.metric_name is None
    u2 = AlertRuleUpdate(metric_name='mem', operator='lt', threshold=50.0)
    print(f'Update full: {u2}')
    print('OK')
    "
    ```

### 2. Extend AlertStore with Event Log and Update Method
- **Task ID**: extend-alert-store
- **Role**: builder
- **Depends On**: add-alert-event-models
- **Assigned To**: builder-backend
- **Description**: |
    Extend `AlertStore` in `backend/alert_store.py` with:
    1. A capped event deque recording state transitions
    2. An `update_rule()` method for editing existing rules
    3. Modified `evaluate()` to record events
    4. An `all_events()` method to retrieve the event log

    ## What to do

    1. Add imports at the top of `backend/alert_store.py`:
       ```python
       from collections import deque
       from models import AlertEvent, AlertRuleIn, AlertRuleOut, AlertRuleUpdate
       ```
       Remove the existing `from models import AlertRuleIn, AlertRuleOut` line and replace with the expanded import.

    2. In `__init__`, add the event deque:
       ```python
       def __init__(self) -> None:
           self._rules: list[AlertRuleOut] = []
           self._events: deque[AlertEvent] = deque(maxlen=200)
       ```

    3. Add `update_rule()` method after `delete_rules_by_metric_name()`:
       ```python
       def update_rule(self, rule_id: str, update: AlertRuleUpdate) -> AlertRuleOut | None:
           for rule in self._rules:
               if rule.id == rule_id:
                   if update.metric_name is not None:
                       rule.metric_name = update.metric_name
                   if update.operator is not None:
                       rule.operator = update.operator
                   if update.threshold is not None:
                       rule.threshold = update.threshold
                   rule.state = "ok"  # reset state on edit
                   return rule
           return None
       ```

    4. Modify `evaluate()` to record events. After detecting a state transition (where `new_state != rule.state`), BEFORE appending to `transitions` and updating `rule.state`, create and append an `AlertEvent`:
       ```python
       if new_state != rule.state:
           event = AlertEvent(
               rule_id=rule.id,
               metric_name=rule.metric_name,
               old_state=rule.state,
               new_state=new_state,
           )
           self._events.append(event)
           transitions.append((rule.id, rule.state, new_state))
           rule.state = new_state
       ```

    5. Add `all_events()` method:
       ```python
       def all_events(self) -> list[AlertEvent]:
           return list(self._events)
       ```

    6. Update `clear()` to also clear events:
       ```python
       def clear(self) -> None:
           self._rules = []
           self._events = deque(maxlen=200)
       ```

    ## Files to modify
    - `backend/alert_store.py` — Expand imports, add `_events` deque to `__init__`, add `update_rule()`, modify `evaluate()`, add `all_events()`, update `clear()`.

    ## Code patterns to follow
    The existing `evaluate()` method (lines 39-69) already detects transitions and returns them as tuples. The change adds event recording INSIDE the existing transition detection block. The `update_rule()` follows the same pattern as `delete_rule()` — iterate `self._rules`, find by ID, return result or None.

    ## Acceptance criteria
    - `self._events` is a `deque(maxlen=200)` initialized in `__init__`
    - `evaluate()` creates `AlertEvent` objects and appends them to `self._events` on every state transition
    - `all_events()` returns a list copy of the events deque
    - `update_rule()` updates matching rule fields, resets state to "ok", returns the updated rule (or None if not found)
    - `clear()` resets both `_rules` and `_events`
    - Event deque caps at 200 entries (oldest evicted when full)
    - `ruff check backend/alert_store.py` passes

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && python3.11 -c "
    from alert_store import AlertStore
    from store import MetricStore
    from models import AlertRuleIn, AlertRuleUpdate, MetricIn
    ms = MetricStore()
    als = AlertStore()
    # Create rule and trigger transition
    rule = als.add_rule(AlertRuleIn(metric_name='cpu', operator='gt', threshold=80.0))
    ms.add(MetricIn(name='cpu', value=95.0))
    t = als.evaluate(ms)
    assert len(t) == 1
    events = als.all_events()
    assert len(events) == 1
    assert events[0].rule_id == rule.id
    assert events[0].old_state == 'ok'
    assert events[0].new_state == 'firing'
    assert events[0].metric_name == 'cpu'
    # Update rule
    from models import AlertRuleUpdate
    updated = als.update_rule(rule.id, AlertRuleUpdate(threshold=99.0))
    assert updated is not None
    assert updated.threshold == 99.0
    assert updated.state == 'ok'  # reset on edit
    # Not found
    assert als.update_rule('nonexistent', AlertRuleUpdate(threshold=50.0)) is None
    # Clear
    als.clear()
    assert len(als.all_events()) == 0
    assert len(als.all_rules()) == 0
    print('OK')
    " && ruff check alert_store.py
    ```

### 3. Add PUT and GET Events API Routes
- **Task ID**: add-alert-api-routes
- **Role**: builder
- **Depends On**: extend-alert-store
- **Assigned To**: builder-backend
- **Description**: |
    Add `PUT /alerts/{id}` and `GET /alerts/events` routes to `backend/main.py`.

    ## What to do

    1. Update the import line from `models` in `backend/main.py` to include the new types. The current import (line 16) is:
       ```python
       from models import AlertRuleIn, AlertRuleOut, MetricIn, MetricOut, MetricSummary
       ```
       Change to:
       ```python
       from models import AlertEvent, AlertRuleIn, AlertRuleOut, AlertRuleUpdate, MetricIn, MetricOut, MetricSummary
       ```

    2. Add `GET /alerts/events` route BEFORE the existing `DELETE /alerts/{rule_id}` route (this is important — FastAPI matches routes in order, and `/alerts/events` must not be caught by `/alerts/{rule_id}`). Place it after the `GET /alerts` route (line 217):
       ```python
       @app.get("/alerts/events", response_model=list[AlertEvent])
       def list_alert_events() -> list[AlertEvent]:
           return alert_store.all_events()
       ```

    3. Add `PUT /alerts/{rule_id}` route after `GET /alerts/events`:
       ```python
       @app.put("/alerts/{rule_id}", response_model=AlertRuleOut)
       def update_alert(rule_id: str, update: AlertRuleUpdate) -> AlertRuleOut:
           result = alert_store.update_rule(rule_id, update)
           if result is None:
               raise HTTPException(status_code=404, detail=f"Alert rule '{rule_id}' not found")
           return result
       ```

    4. IMPORTANT: Route ordering in `main.py` must be:
       - `POST /alerts` (existing, line 211)
       - `GET /alerts` (existing, line 216)
       - `GET /alerts/events` (NEW — must come before DELETE to avoid path conflict)
       - `PUT /alerts/{rule_id}` (NEW)
       - `DELETE /alerts/{rule_id}` (existing, line 221)

    ## Files to modify
    - `backend/main.py` — Update model imports, add two new route functions between existing GET /alerts and DELETE /alerts/{rule_id}.

    ## Code patterns to follow
    Existing route patterns in `backend/main.py`:
    - GET list: `@app.get("/alerts", response_model=list[AlertRuleOut])` (line 216)
    - DELETE with return: `@app.delete("/alerts/{rule_id}")` returning `dict[str, int]` (line 221)
    - 404 pattern: `raise HTTPException(status_code=404, detail=f"...")` (used in `get_metric`, line 200)

    ## Acceptance criteria
    - `GET /alerts/events` returns 200 with list of `AlertEvent` objects (empty list when no events)
    - `PUT /alerts/{rule_id}` with valid body returns 200 with updated `AlertRuleOut`
    - `PUT /alerts/{rule_id}` with nonexistent ID returns 404
    - `PUT /alerts/{rule_id}` resets the rule's state to "ok"
    - Route ordering prevents `/alerts/events` from being caught by `/alerts/{rule_id}`
    - `ruff check backend/main.py` passes
    - All existing tests still pass

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && python3.11 -c "
    from fastapi.testclient import TestClient
    from main import app, store, alert_store
    store.clear(); alert_store.clear()
    c = TestClient(app)
    # Events initially empty
    assert c.get('/alerts/events').json() == []
    # Create rule
    r = c.post('/alerts', json={'metric_name': 'cpu', 'operator': 'gt', 'threshold': 80.0})
    assert r.status_code == 201
    rule_id = r.json()['id']
    # PUT to update
    r2 = c.put(f'/alerts/{rule_id}', json={'threshold': 95.0})
    assert r2.status_code == 200
    assert r2.json()['threshold'] == 95.0
    assert r2.json()['state'] == 'ok'
    # PUT nonexistent
    r3 = c.put('/alerts/nonexistent', json={'threshold': 50.0})
    assert r3.status_code == 404
    # Submit metric and trigger evaluation to generate event
    c.post('/metrics', json={'name': 'cpu', 'value': 100.0})
    alert_store.evaluate(store)
    events = c.get('/alerts/events').json()
    assert len(events) == 1
    assert events[0]['old_state'] == 'ok'
    assert events[0]['new_state'] == 'firing'
    store.clear(); alert_store.clear()
    print('OK')
    " && ruff check main.py
    ```

### 4. Add Backend Tests for New Endpoints
- **Task ID**: add-backend-tests
- **Role**: builder
- **Depends On**: add-alert-api-routes
- **Assigned To**: builder-backend
- **Description**: |
    Add tests for the new `PUT /alerts/{id}` and `GET /alerts/events` endpoints to `backend/tests/test_api.py`.

    ## What to do
    Add the following test functions at the bottom of `backend/tests/test_api.py`. Use the existing `client` module-level `TestClient` and the `alert_store`/`store` imports already present (`from main import alert_store, app, store` on line 11).

    1. **test_update_alert_rule**: POST a rule, then PUT to update threshold. Assert 200, check threshold changed, state reset to "ok".
       ```python
       def test_update_alert_rule():
           r = client.post("/alerts", json={"metric_name": "cpu", "operator": "gt", "threshold": 80.0})
           rule_id = r.json()["id"]
           r2 = client.put(f"/alerts/{rule_id}", json={"threshold": 95.0})
           assert r2.status_code == 200
           data = r2.json()
           assert data["threshold"] == 95.0
           assert data["metric_name"] == "cpu"
           assert data["operator"] == "gt"
           assert data["state"] == "ok"
       ```

    2. **test_update_alert_rule_partial**: POST a rule, then PUT with only `metric_name`. Assert other fields unchanged.
       ```python
       def test_update_alert_rule_partial():
           r = client.post("/alerts", json={"metric_name": "cpu", "operator": "gt", "threshold": 80.0})
           rule_id = r.json()["id"]
           r2 = client.put(f"/alerts/{rule_id}", json={"metric_name": "memory"})
           assert r2.status_code == 200
           data = r2.json()
           assert data["metric_name"] == "memory"
           assert data["operator"] == "gt"
           assert data["threshold"] == 80.0
       ```

    3. **test_update_alert_rule_not_found**: PUT to nonexistent ID. Assert 404.
       ```python
       def test_update_alert_rule_not_found():
           r = client.put("/alerts/nonexistent", json={"threshold": 50.0})
           assert r.status_code == 404
       ```

    4. **test_update_alert_resets_state**: Create rule, trigger firing, then update. Assert state resets to "ok".
       ```python
       def test_update_alert_resets_state():
           client.post("/alerts", json={"metric_name": "cpu", "operator": "gt", "threshold": 80.0})
           client.post("/metrics", json={"name": "cpu", "value": 95.0})
           alert_store.evaluate(store)
           alerts = client.get("/alerts").json()
           assert alerts[0]["state"] == "firing"
           rule_id = alerts[0]["id"]
           r = client.put(f"/alerts/{rule_id}", json={"threshold": 99.0})
           assert r.json()["state"] == "ok"
       ```

    5. **test_get_alert_events_empty**: GET /alerts/events with no events. Assert 200, empty list.
       ```python
       def test_get_alert_events_empty():
           r = client.get("/alerts/events")
           assert r.status_code == 200
           assert r.json() == []
       ```

    6. **test_get_alert_events_after_transition**: Create rule, submit metric, evaluate, check events.
       ```python
       def test_get_alert_events_after_transition():
           client.post("/alerts", json={"metric_name": "cpu", "operator": "gt", "threshold": 80.0})
           client.post("/metrics", json={"name": "cpu", "value": 95.0})
           alert_store.evaluate(store)
           r = client.get("/alerts/events")
           assert r.status_code == 200
           events = r.json()
           assert len(events) == 1
           assert events[0]["old_state"] == "ok"
           assert events[0]["new_state"] == "firing"
           assert events[0]["metric_name"] == "cpu"
           assert "timestamp" in events[0]
           assert "rule_id" in events[0]
       ```

    7. **test_alert_events_multiple_transitions**: Create rule, trigger ok->firing->ok, check 2 events.
       ```python
       def test_alert_events_multiple_transitions():
           client.post("/alerts", json={"metric_name": "cpu", "operator": "gt", "threshold": 80.0})
           client.post("/metrics", json={"name": "cpu", "value": 95.0})
           alert_store.evaluate(store)
           client.post("/metrics", json={"name": "cpu", "value": 50.0})
           alert_store.evaluate(store)
           events = client.get("/alerts/events").json()
           assert len(events) == 2
           assert events[0]["new_state"] == "firing"
           assert events[1]["new_state"] == "ok"
       ```

    8. **test_alert_events_cap_at_200**: Verify event deque caps at 200 by adding 201 events.
       ```python
       def test_alert_events_cap_at_200():
           client.post("/alerts", json={"metric_name": "cpu", "operator": "gt", "threshold": 80.0})
           for i in range(201):
               value = 95.0 if i % 2 == 0 else 50.0
               client.post("/metrics", json={"name": "cpu", "value": value})
               alert_store.evaluate(store)
           events = client.get("/alerts/events").json()
           assert len(events) == 200
       ```

    ## Files to modify
    - `backend/tests/test_api.py` — Add 8 new test functions at the bottom of the file.

    ## Code patterns to follow
    Existing test pattern:
    ```python
    def test_create_alert_rule():
        r = client.post("/alerts", json={"metric_name": "cpu", "operator": "gt", "threshold": 90.0})
        assert r.status_code == 201
        data = r.json()
        assert data["metric_name"] == "cpu"
    ```
    Use the module-level `client`, `store`, and `alert_store`. The `clear_store` autouse fixture resets both stores before each test.

    ## Acceptance criteria
    - 8 new test functions added
    - All new tests pass
    - All existing tests still pass
    - `ruff check backend/tests/test_api.py` passes

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && python3.11 -m pytest tests/test_api.py -v -k "update_alert or alert_events or alert_resets" --tb=short && python3.11 -m pytest tests/ -v --tb=short 2>&1 | tail -15
    ```

### 5. Add Frontend API Types and Functions
- **Task ID**: add-frontend-api
- **Role**: builder
- **Depends On**: add-alert-api-routes
- **Assigned To**: builder-frontend
- **Description**: |
    Add new TypeScript interfaces and API functions to `frontend/src/api.ts` for alert events and alert updating.

    ## What to do

    1. Add `AlertEvent` interface after the existing `AlertRuleIn` interface (after line 19):
       ```typescript
       export interface AlertEvent {
         rule_id: string
         metric_name: string
         old_state: AlertState
         new_state: AlertState
         timestamp: string
       }
       ```

    2. Add `AlertRuleUpdate` interface after `AlertEvent`:
       ```typescript
       export interface AlertRuleUpdate {
         metric_name?: string
         operator?: AlertOperator
         threshold?: number
       }
       ```

    3. Add `updateAlert()` function after the existing `createAlert()` function (after line 97):
       ```typescript
       export async function updateAlert(ruleId: string, update: AlertRuleUpdate): Promise<AlertRule> {
         const res = await fetch(`${BASE}/alerts/${ruleId}`, {
           method: 'PUT',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify(update),
         })
         if (!res.ok) throw new Error(`Failed to update alert: ${res.status}`)
         return res.json()
       }
       ```

    4. Add `fetchAlertEvents()` function after `updateAlert()`:
       ```typescript
       export async function fetchAlertEvents(): Promise<AlertEvent[]> {
         const res = await fetch(`${BASE}/alerts/events`)
         if (!res.ok) throw new Error(`Failed to fetch alert events: ${res.status}`)
         return res.json()
       }
       ```

    ## Files to modify
    - `frontend/src/api.ts` — Add `AlertEvent` interface, `AlertRuleUpdate` interface, `updateAlert()` function, `fetchAlertEvents()` function.

    ## Code patterns to follow
    Existing patterns in `frontend/src/api.ts`:
    ```typescript
    export async function createAlert(rule: AlertRuleIn): Promise<AlertRule> {
      const res = await fetch(`${BASE}/alerts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(rule),
      })
      if (!res.ok || res.status !== 201)
        throw new Error(`Failed to create alert: ${res.status}`)
      return res.json()
    }
    ```
    Follow the same style: async function, fetch with BASE, error check on `!res.ok`, return `res.json()`.

    ## Acceptance criteria
    - `AlertEvent` interface has fields: `rule_id`, `metric_name`, `old_state`, `new_state`, `timestamp`
    - `AlertRuleUpdate` interface has optional fields: `metric_name?`, `operator?`, `threshold?`
    - `updateAlert(ruleId, update)` sends PUT to `/alerts/{ruleId}` and returns `AlertRule`
    - `fetchAlertEvents()` sends GET to `/alerts/events` and returns `AlertEvent[]`
    - `npx tsc --noEmit` passes in the frontend directory

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx tsc --noEmit
    ```

### 6. Create AlertPanel Component
- **Task ID**: create-alert-panel
- **Role**: builder
- **Depends On**: add-frontend-api
- **Assigned To**: builder-frontend
- **Description**: |
    Create the `AlertPanel` component at `frontend/src/components/AlertPanel.tsx`. This component encapsulates all alert management functionality: creating rules, editing rules, deleting rules, displaying the rules list with state badges, and showing an event history timeline.

    ## What to do

    Create `frontend/src/components/AlertPanel.tsx` with the following structure:

    ```typescript
    import { useState } from 'react'
    import {
      createAlert,
      deleteAlert,
      updateAlert,
      type AlertEvent,
      type AlertOperator,
      type AlertRule,
      type AlertRuleIn,
    } from '../api'

    interface Props {
      alerts: AlertRule[]
      events: AlertEvent[]
      onAlertChange: () => void
    }

    const OP_SYMBOLS: Record<AlertOperator, string> = { gt: '>', lt: '<', eq: '=' }

    export function AlertPanel({ alerts, events, onAlertChange }: Props) {
      // Form state
      const [metricName, setMetricName] = useState('')
      const [operator, setOperator] = useState<AlertOperator>('gt')
      const [threshold, setThreshold] = useState('')
      const [editingId, setEditingId] = useState<string | null>(null)
      const [formError, setFormError] = useState<string | null>(null)
      const [submitting, setSubmitting] = useState(false)

      const resetForm = () => {
        setMetricName('')
        setOperator('gt')
        setThreshold('')
        setEditingId(null)
        setFormError(null)
      }

      const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!metricName.trim() || !threshold.trim()) return
        setSubmitting(true)
        setFormError(null)
        try {
          if (editingId) {
            await updateAlert(editingId, {
              metric_name: metricName.trim(),
              operator,
              threshold: parseFloat(threshold),
            })
          } else {
            await createAlert({
              metric_name: metricName.trim(),
              operator,
              threshold: parseFloat(threshold),
            })
          }
          resetForm()
          onAlertChange()
        } catch (err) {
          setFormError(err instanceof Error ? err.message : 'Failed to save alert')
        } finally {
          setSubmitting(false)
        }
      }

      const handleEdit = (alert: AlertRule) => {
        setMetricName(alert.metric_name)
        setOperator(alert.operator)
        setThreshold(String(alert.threshold))
        setEditingId(alert.id)
        setFormError(null)
      }

      const handleDelete = async (id: string) => {
        try {
          await deleteAlert(id)
          onAlertChange()
        } catch (err) {
          console.error('Failed to delete alert:', err)
        }
      }

      const formatTime = (ts: string) => new Date(ts).toLocaleTimeString()

      return (
        <div className="alerts-section">
          <div className="section-title">Alerts</div>

          {/* Create/Edit Form */}
          <form onSubmit={handleSubmit} className="alert-form">
            <input
              type="text"
              placeholder="metric name"
              value={metricName}
              onChange={(e) => setMetricName(e.target.value)}
              data-testid="alert-metric-input"
              required
            />
            <select
              value={operator}
              onChange={(e) => setOperator(e.target.value as AlertOperator)}
              data-testid="alert-operator-select"
            >
              <option value="gt">&gt; (greater than)</option>
              <option value="lt">&lt; (less than)</option>
              <option value="eq">= (equal)</option>
            </select>
            <input
              type="number"
              placeholder="threshold"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              step="any"
              data-testid="alert-threshold-input"
              required
            />
            <button type="submit" disabled={submitting} className="btn-primary" data-testid="alert-submit-btn">
              {submitting ? 'Saving...' : editingId ? 'Update Alert' : 'Create Alert'}
            </button>
            {editingId && (
              <button type="button" onClick={resetForm} data-testid="alert-cancel-btn">
                Cancel
              </button>
            )}
            {formError && <span className="alert-form-error">{formError}</span>}
          </form>

          {/* Alert Rules List */}
          {alerts.length === 0 ? (
            <p className="empty-state" style={{ padding: '1rem' }}>No alerts configured.</p>
          ) : (
            <div className="alert-list-container">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`alert-row ${alert.state === 'firing' ? 'alert-row--firing' : 'alert-row--ok'}`}
                >
                  <span className="alert-metric">{alert.metric_name}</span>
                  <span className="alert-condition">
                    {OP_SYMBOLS[alert.operator]} {alert.threshold}
                  </span>
                  <span
                    className={`alert-badge ${alert.state === 'firing' ? 'alert-badge--firing' : 'alert-badge--ok'}`}
                  >
                    {alert.state}
                  </span>
                  <div className="alert-actions">
                    <button
                      className="panel-action-btn"
                      onClick={() => handleEdit(alert)}
                      aria-label={`Edit ${alert.metric_name}`}
                      data-testid={`edit-alert-${alert.id}`}
                    >
                      Edit
                    </button>
                    <button
                      className="panel-action-btn alert-delete-btn"
                      onClick={() => handleDelete(alert.id)}
                      aria-label={`Delete ${alert.metric_name}`}
                      data-testid={`delete-alert-${alert.id}`}
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Alert History Timeline */}
          {events.length > 0 && (
            <div className="alert-history">
              <div className="section-title" style={{ marginTop: '1rem' }}>Alert History</div>
              <div className="alert-timeline">
                {events.slice().reverse().slice(0, 50).map((event, i) => (
                  <div
                    key={`${event.rule_id}-${event.timestamp}-${i}`}
                    className={`alert-timeline-item ${event.new_state === 'firing' ? 'alert-timeline-item--firing' : 'alert-timeline-item--ok'}`}
                  >
                    <span className="alert-timeline-time">{formatTime(event.timestamp)}</span>
                    <span className="alert-timeline-metric">{event.metric_name}</span>
                    <span className="alert-timeline-transition">
                      {event.old_state} → {event.new_state}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )
    }
    ```

    ## Files to modify
    - `frontend/src/components/AlertPanel.tsx` — Create this new file.

    ## Code patterns to follow
    - Component pattern: follow `MetricForm.tsx` for form handling (local state, handleSubmit, error display)
    - Props pattern: follow `TagFilterBar.tsx` (props with data + callback)
    - Alert display: replicate the existing inline alert rendering from `App.tsx` lines 120-142 (same CSS classes: `alerts-section`, `alert-row`, `alert-badge`, etc.)
    - Use `data-testid` attributes on interactive elements for testability

    ## Acceptance criteria
    - `AlertPanel.tsx` exists at `frontend/src/components/AlertPanel.tsx`
    - Component accepts `alerts: AlertRule[]`, `events: AlertEvent[]`, `onAlertChange: () => void` props
    - Create form: inputs for metric name, operator select, threshold; submit calls `createAlert()`
    - Edit mode: clicking Edit on a rule populates the form; submit calls `updateAlert()`; Cancel button exits edit mode
    - Delete: clicking delete button calls `deleteAlert()` and triggers `onAlertChange`
    - Rules list: displays all alerts with state badges (same CSS as current inline section)
    - History timeline: shows recent events in reverse chronological order (newest first), limited to 50 displayed
    - `npx tsc --noEmit` passes

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx tsc --noEmit
    ```

### 7. Add AlertPanel CSS Styles
- **Task ID**: add-alert-panel-css
- **Role**: builder
- **Depends On**: create-alert-panel
- **Assigned To**: builder-frontend
- **Description**: |
    Add CSS styles for the AlertPanel's new elements (form, actions, history timeline) to `frontend/src/dashboard.css`. The existing alert styles (`.alerts-section`, `.alert-row`, `.alert-badge`, etc. at lines 273-341) should be kept. New styles are added for the form, action buttons, and timeline.

    ## What to do

    Add the following CSS to the END of `frontend/src/dashboard.css` (after the existing tag filter bar section, which ends around line 381):

    ```css
    /* ─── Alert Form ─── */
    .alert-form {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem 0;
      margin-bottom: 0.5rem;
      flex-wrap: wrap;
    }

    .alert-form input,
    .alert-form select {
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      color: var(--text-primary);
      padding: 0.35rem 0.6rem;
      border-radius: 4px;
      font-size: 0.8rem;
    }

    .alert-form input::placeholder {
      color: var(--text-muted);
    }

    .alert-form input:focus,
    .alert-form select:focus {
      outline: none;
      border-color: var(--accent-blue);
    }

    .alert-form-error {
      color: var(--accent-red);
      font-size: 0.8rem;
    }

    /* ─── Alert Row Actions ─── */
    .alert-actions {
      display: flex;
      gap: 0.25rem;
      margin-left: auto;
    }

    .alert-delete-btn:hover {
      color: var(--accent-red) !important;
      background: rgba(239, 68, 68, 0.1) !important;
    }

    /* ─── Alert History Timeline ─── */
    .alert-history {
      margin-top: 0.5rem;
    }

    .alert-timeline {
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
      max-height: 300px;
      overflow-y: auto;
    }

    .alert-timeline-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.35rem 0.75rem;
      background: var(--bg-primary);
      border: 1px solid var(--border);
      border-radius: 4px;
      font-size: 0.8rem;
    }

    .alert-timeline-item--firing {
      border-left: 3px solid var(--accent-red);
    }

    .alert-timeline-item--ok {
      border-left: 3px solid var(--accent-green);
    }

    .alert-timeline-time {
      color: var(--text-muted);
      font-family: 'SF Mono', SFMono-Regular, Menlo, monospace;
      font-size: 0.75rem;
      min-width: 70px;
    }

    .alert-timeline-metric {
      color: var(--text-primary);
      font-weight: 500;
      flex: 1;
    }

    .alert-timeline-transition {
      color: var(--text-secondary);
      font-size: 0.75rem;
    }
    ```

    ## Files to modify
    - `frontend/src/dashboard.css` — Append new CSS classes at the end of the file.

    ## Code patterns to follow
    Follow the existing Grafana-inspired dark theme using CSS custom properties defined in `:root` (lines 2-16 of dashboard.css):
    - `var(--bg-secondary)` for input backgrounds
    - `var(--border)` for borders
    - `var(--text-primary)`, `var(--text-secondary)`, `var(--text-muted)` for text
    - `var(--accent-red)`, `var(--accent-green)` for state colors
    - Same sizing patterns: `0.8rem` for small text, `4px` border-radius

    ## Acceptance criteria
    - `.alert-form` styles exist with flex layout matching toolbar pattern
    - `.alert-actions` styles exist for edit/delete buttons
    - `.alert-timeline` and `.alert-timeline-item` styles exist for history display
    - Timeline items have colored left border (red for firing, green for ok)
    - Timeline has max-height with overflow scroll
    - All styles use existing CSS custom properties (no hardcoded colors)
    - `npx tsc --noEmit` still passes (CSS changes shouldn't affect TypeScript)

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx tsc --noEmit
    ```

### 8. Integrate AlertPanel into App.tsx
- **Task ID**: integrate-alert-panel
- **Role**: builder
- **Depends On**: create-alert-panel, add-alert-panel-css
- **Assigned To**: builder-frontend
- **Description**: |
    Replace the inline alerts section in `App.tsx` with the new `AlertPanel` component. Add alert events state and loading to the polling loop.

    ## What to do

    1. Update imports at the top of `frontend/src/App.tsx`. The current imports (lines 1-7) are:
       ```typescript
       import { useEffect, useRef, useState } from 'react'
       import { fetchAlerts, fetchMetrics, type AlertRule, type Metric } from './api'
       import { MetricCard } from './components/MetricCard'
       import { MetricForm } from './components/MetricForm'
       import { TagFilterBar } from './components/TagFilterBar'
       import { TimeRangeBar, type TimeRange } from './components/TimeRangeBar'
       import './dashboard.css'
       ```
       Change the api import to also include `fetchAlertEvents` and `AlertEvent`:
       ```typescript
       import { fetchAlertEvents, fetchAlerts, fetchMetrics, type AlertEvent, type AlertRule, type Metric } from './api'
       ```
       Add AlertPanel import after the MetricForm import:
       ```typescript
       import { AlertPanel } from './components/AlertPanel'
       ```

    2. Add `alertEvents` state after the existing `alerts` state (after line 13):
       ```typescript
       const [alertEvents, setAlertEvents] = useState<AlertEvent[]>([])
       ```

    3. Add `loadAlertEvents` function after the existing `loadAlerts` function (after line 50):
       ```typescript
       const loadAlertEvents = async () => {
         try {
           const data = await fetchAlertEvents()
           setAlertEvents(data)
         } catch (e) {
           console.error('Failed to load alert events:', e)
         }
       }
       ```

    4. Update the polling `loadData` function (lines 53-55) to also load events:
       ```typescript
       const loadData = async () => {
         await Promise.all([loadMetrics(), loadAlerts(), loadAlertEvents()])
       }
       ```

    5. Add a combined reload callback for AlertPanel (after loadAlertEvents):
       ```typescript
       const handleAlertChange = async () => {
         await Promise.all([loadAlerts(), loadAlertEvents()])
       }
       ```

    6. Replace the inline alerts section (lines 120-142) with the AlertPanel component. The current code is:
       ```tsx
       <div className="alerts-section">
         <div className="section-title">Alerts</div>
         {alerts.length === 0 ? (
           <p className="empty-state" style={{ padding: '1rem' }}>No alerts configured.</p>
         ) : (
           <div className="alert-list-container">
             {alerts.map((alert) => (
               <div
                 key={alert.id}
                 className={`alert-row ${alert.state === 'firing' ? 'alert-row--firing' : 'alert-row--ok'}`}
               >
                 <span className="alert-metric">{alert.metric_name}</span>
                 <span className="alert-condition">
                   {opSymbol(alert.operator)} {alert.threshold}
                 </span>
                 <span className={`alert-badge ${alert.state === 'firing' ? 'alert-badge--firing' : 'alert-badge--ok'}`}>
                   {alert.state}
                 </span>
               </div>
             ))}
           </div>
         )}
       </div>
       ```
       Replace with:
       ```tsx
       <AlertPanel alerts={alerts} events={alertEvents} onAlertChange={handleAlertChange} />
       ```

    7. Remove the `opSymbol` helper function (line 78) since it's no longer used:
       ```typescript
       const opSymbol = (op: string) => op === 'gt' ? '>' : op === 'lt' ? '<' : '='
       ```
       Delete this line. The AlertPanel has its own `OP_SYMBOLS` map.

    ## Files to modify
    - `frontend/src/App.tsx` — Update imports, add alertEvents state, add loadAlertEvents, update polling, add handleAlertChange, replace inline alerts section with AlertPanel, remove unused opSymbol.

    ## Code patterns to follow
    - State pattern: follow existing `alerts` state (line 13) and `loadAlerts` (lines 43-50)
    - Polling: follow existing `Promise.all` pattern in `loadData` (line 54)
    - Component usage: follow `<TagFilterBar tags={activeTags} onTagsChange={setActiveTags} />` pattern (line 96)

    ## Acceptance criteria
    - `AlertPanel` is imported and rendered in place of the inline alerts section
    - `alertEvents` state is managed in App.tsx
    - `loadAlertEvents()` fetches events from API
    - Polling loop calls `loadAlertEvents()` alongside metrics and alerts
    - `handleAlertChange` callback reloads both alerts and events
    - The `opSymbol` helper is removed (AlertPanel has its own)
    - `npx tsc --noEmit` passes

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx tsc --noEmit
    ```

### 9. Update Frontend Tests
- **Task ID**: update-frontend-tests
- **Role**: builder
- **Depends On**: integrate-alert-panel
- **Assigned To**: builder-frontend
- **Description**: |
    Update `frontend/src/App.test.tsx` to work with the new AlertPanel component and add tests for the new functionality. The main changes are:
    1. Mock the new `fetchAlertEvents` API function
    2. Update existing alert tests that reference inline elements
    3. Add tests for the AlertPanel create/edit/delete forms

    ## What to do

    1. Update the mock setup in `beforeEach` (lines 10-15). Add `fetchAlertEvents` mock:
       ```typescript
       beforeEach(() => {
         vi.clearAllMocks()
         vi.mocked(api.fetchMetrics).mockResolvedValue([])
         vi.mocked(api.fetchAlerts).mockResolvedValue([])
         vi.mocked(api.fetchAlertEvents).mockResolvedValue([])
         vi.mocked(api.fetchMetricHistory).mockResolvedValue([])
       })
       ```

    2. The existing test "renders alerts when returned from API" (lines 47-62) should still work because AlertPanel renders the same CSS classes and text. Keep it as-is.

    3. The test "shows empty alerts section when no alerts" (lines 64-67) should still work because AlertPanel shows "No alerts configured." text. Keep it as-is.

    4. The test "polls both metrics and alerts synchronously" (lines 70-85) needs to also verify `fetchAlertEvents` is called. Update:
       ```typescript
       it('polls both metrics and alerts synchronously', async () => {
         vi.useFakeTimers()

         render(<App />)

         expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(1)
         expect(vi.mocked(api.fetchAlerts)).toHaveBeenCalledTimes(1)
         expect(vi.mocked(api.fetchAlertEvents)).toHaveBeenCalledTimes(1)

         await vi.advanceTimersByTimeAsync(5000)
         expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(2)
         expect(vi.mocked(api.fetchAlerts)).toHaveBeenCalledTimes(2)
         expect(vi.mocked(api.fetchAlertEvents)).toHaveBeenCalledTimes(2)

         await vi.advanceTimersByTimeAsync(5000)
         expect(vi.mocked(api.fetchMetrics)).toHaveBeenCalledTimes(3)
         expect(vi.mocked(api.fetchAlerts)).toHaveBeenCalledTimes(3)
         expect(vi.mocked(api.fetchAlertEvents)).toHaveBeenCalledTimes(3)
       })
       ```

    5. The test "handles alert fetch errors gracefully" (lines 87-107) should also mock `fetchAlertEvents` to return empty (already done in beforeEach). Keep as-is.

    6. The test "shows firing alert state" (lines 109-126) should still work. Keep as-is.

    7. Add new tests in a new `describe('AlertPanel Integration')` block after the existing Alert Integration Tests block (after line 127):

       ```typescript
       describe('AlertPanel Integration', () => {
         it('renders alert create form', async () => {
           render(<App />)
           expect(await screen.findByTestId('alert-metric-input')).toBeInTheDocument()
           expect(screen.getByTestId('alert-operator-select')).toBeInTheDocument()
           expect(screen.getByTestId('alert-threshold-input')).toBeInTheDocument()
           expect(screen.getByTestId('alert-submit-btn')).toBeInTheDocument()
           expect(screen.getByTestId('alert-submit-btn')).toHaveTextContent('Create Alert')
         })

         it('renders alert history when events exist', async () => {
           vi.mocked(api.fetchAlertEvents).mockResolvedValue([
             {
               rule_id: 'r1',
               metric_name: 'cpu',
               old_state: 'ok',
               new_state: 'firing',
               timestamp: new Date().toISOString(),
             },
           ])
           render(<App />)
           expect(await screen.findByText('Alert History')).toBeInTheDocument()
           expect(await screen.findByText('ok → firing')).toBeInTheDocument()
         })

         it('does not render history section when no events', async () => {
           render(<App />)
           // Wait for alerts section to render
           expect(await screen.findByText('Alerts')).toBeInTheDocument()
           expect(screen.queryByText('Alert History')).not.toBeInTheDocument()
         })

         it('handles fetchAlertEvents error gracefully', async () => {
           vi.mocked(api.fetchAlertEvents).mockRejectedValue(new Error('Events service down'))
           render(<App />)
           // Should still render the alerts section
           expect(await screen.findByText('Alerts')).toBeInTheDocument()
         })
       })
       ```

    ## Files to modify
    - `frontend/src/App.test.tsx` — Add `fetchAlertEvents` mock to beforeEach, update polling test, add AlertPanel Integration tests.

    ## Code patterns to follow
    Existing test patterns:
    - Mock setup: `vi.mocked(api.fetchAlerts).mockResolvedValue([])` in `beforeEach`
    - Async finding: `await screen.findByText('...')` for content that appears after async loading
    - TestId: `screen.getByTestId('...')` for targeting specific elements
    - Error handling: `vi.mocked(api.fetchAlerts).mockRejectedValue(new Error('...'))`

    ## Acceptance criteria
    - `fetchAlertEvents` is mocked in `beforeEach`
    - Polling test verifies `fetchAlertEvents` is called on each interval
    - New "AlertPanel Integration" test block with 4 tests
    - All existing tests still pass
    - All new tests pass
    - `npx tsc --noEmit` passes

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx vitest run --reporter=verbose 2>&1 | tail -30
    ```

### 10. Final Validation
- **Task ID**: validate-all
- **Role**: validator
- **Depends On**: add-backend-tests, update-frontend-tests
- **Assigned To**: validator
- **Description**: |
    Run all validation commands and verify all acceptance criteria for the complete alert management UI and history feature.

    ## Validation Commands
    Run ALL of these commands and verify they pass:

    1. Backend lint: `cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && ruff check .`
    2. Backend format: `cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && ruff format --check .`
    3. Backend full test suite: `cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && python3.11 -m pytest tests/ -v`
    4. Frontend typecheck: `cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx tsc --noEmit`
    5. Frontend tests: `cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx vitest run --reporter=verbose`
    6. Backend smoke — PUT alert: `cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && python3.11 -c "
    from fastapi.testclient import TestClient
    from main import app, store, alert_store
    store.clear(); alert_store.clear()
    c = TestClient(app)
    r = c.post('/alerts', json={'metric_name': 'cpu', 'operator': 'gt', 'threshold': 80.0})
    assert r.status_code == 201
    rid = r.json()['id']
    r2 = c.put(f'/alerts/{rid}', json={'threshold': 95.0})
    assert r2.status_code == 200
    assert r2.json()['threshold'] == 95.0
    assert r2.json()['state'] == 'ok'
    store.clear(); alert_store.clear()
    print('PUT OK')
    "`
    7. Backend smoke — events: `cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && python3.11 -c "
    from fastapi.testclient import TestClient
    from main import app, store, alert_store
    store.clear(); alert_store.clear()
    c = TestClient(app)
    c.post('/alerts', json={'metric_name': 'cpu', 'operator': 'gt', 'threshold': 80.0})
    c.post('/metrics', json={'name': 'cpu', 'value': 95.0})
    alert_store.evaluate(store)
    events = c.get('/alerts/events').json()
    assert len(events) == 1
    assert events[0]['old_state'] == 'ok'
    assert events[0]['new_state'] == 'firing'
    assert events[0]['metric_name'] == 'cpu'
    store.clear(); alert_store.clear()
    print('Events OK')
    "`
    8. Health endpoint: `cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && python3.11 -c "from fastapi.testclient import TestClient; from main import app; c = TestClient(app); assert c.get('/health').json() == {'status': 'ok'}; print('Health OK')"`
    9. Verify AlertPanel file exists: `test -f /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend/src/components/AlertPanel.tsx && echo 'AlertPanel exists'`

    ## Acceptance Criteria
    - `ruff check .` — 0 errors
    - `ruff format --check .` — no reformatting needed
    - All backend tests pass with 0 failures
    - Frontend TypeScript compilation passes with no errors
    - All frontend tests pass with 0 failures
    - `PUT /alerts/{id}` works: updates threshold, resets state to "ok", returns 404 for nonexistent
    - `GET /alerts/events` works: returns event list with rule_id, metric_name, old_state, new_state, timestamp
    - Event deque caps at 200 entries
    - `AlertPanel.tsx` exists and exports `AlertPanel` component
    - AlertPanel renders: create form, rules list with state badges, edit/delete buttons, history timeline
    - App.tsx imports and renders AlertPanel (inline alerts section removed)
    - App.tsx polls alert events alongside metrics and alerts
    - No regressions in existing functionality (metrics CRUD, history, export, tag filtering, time range)
    - Health endpoint returns `{"status": "ok"}`

### 11. Update Design Doc
- **Task ID**: update-design-metrics
- **Role**: design-updater
- **Depends On**: validate-all
- **Assigned To**: design-updater
- **Description**: |
    Update the living design document for the metrics domain to reflect
    what was actually built in this plan.

    ## Target Design Doc
    docs/design/metrics.md

    ## Spec File
    specs/alert-management-ui-and-history.md

    ## Scope
    Alert event logging, alert rule editing (PUT endpoint), alert events API,
    AlertPanel frontend component replacing inline alerts section, alert events
    polling in App.tsx.

    ## Prior Decisions to Check
    - Phase 1 alerting architecture (AlertStore, evaluate() returning transitions, background eval loop)
    - DD-004: Tag state lifted to App.tsx pattern — AlertPanel follows same pattern with lifted alerts/events state
    - DD-013: TimeRange state lifted pattern — alertEvents follows the same lifted-state-with-polling approach

    ## What to Record
    Read git diff HEAD~1 HEAD, then the changed source files, then the existing
    design doc. Update Current Design to match the implementation. Append a
    Design Decision entry for each non-trivial architectural choice made in
    this build. Every claim must cite a file:line from the actual code.

    Specific areas to document:
    1. AlertEvent model and capped deque(maxlen=200) in AlertStore
    2. PUT /alerts/{id} endpoint with state reset behavior
    3. GET /alerts/events endpoint and route ordering (must come before DELETE /alerts/{rule_id})
    4. AlertPanel component architecture (props-based with lifted state)
    5. Alert events polling added to App.tsx loadData()
    6. AlertRuleUpdate model with all-optional fields for partial updates

## Acceptance Criteria

1. `PUT /alerts/{id}` with valid body returns 200 with updated `AlertRuleOut` (state reset to "ok")
2. `PUT /alerts/{id}` with nonexistent ID returns 404
3. `PUT /alerts/{id}` supports partial updates (only fields provided are changed)
4. `GET /alerts/events` returns 200 with list of `AlertEvent` objects
5. Alert events include: `rule_id`, `metric_name`, `old_state`, `new_state`, `timestamp`
6. Event deque is capped at 200 entries (oldest evicted when full)
7. Events are recorded on every state transition in `evaluate()`
8. `AlertPanel` component renders: create form, edit form, delete button, rules list with state badges, history timeline
9. `AlertPanel` replaces the inline alerts section in `App.tsx`
10. App.tsx polls alert events alongside metrics and alerts every 5 seconds
11. All backend tests pass (existing + new)
12. All frontend tests pass (existing + new)
13. `ruff check .` and `ruff format --check .` pass
14. `npx tsc --noEmit` passes
15. No regressions in existing metric CRUD, history, export, filtering, or alerting endpoints

## Validation Commands

Execute these commands to validate the task is complete:

```bash
# Backend lint
cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && ruff check .

# Backend format
cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && ruff format --check .

# Backend tests
cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && python3.11 -m pytest tests/ -v

# Frontend typecheck
cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx tsc --noEmit

# Frontend tests
cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx vitest run --reporter=verbose

# Smoke test — full alert lifecycle
cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && python3.11 -c "
from fastapi.testclient import TestClient
from main import app, store, alert_store
store.clear(); alert_store.clear()
c = TestClient(app)
# Create
r = c.post('/alerts', json={'metric_name': 'cpu', 'operator': 'gt', 'threshold': 80.0})
assert r.status_code == 201
rid = r.json()['id']
# Update
r2 = c.put(f'/alerts/{rid}', json={'threshold': 95.0})
assert r2.status_code == 200
assert r2.json()['threshold'] == 95.0
assert r2.json()['state'] == 'ok'
# Trigger firing
c.post('/metrics', json={'name': 'cpu', 'value': 100.0})
alert_store.evaluate(store)
# Check events
events = c.get('/alerts/events').json()
assert len(events) == 1
assert events[0]['new_state'] == 'firing'
# Verify alert state
alerts = c.get('/alerts').json()
assert alerts[0]['state'] == 'firing'
# Delete
d = c.delete(f'/alerts/{rid}')
assert d.json() == {'deleted': 1}
store.clear(); alert_store.clear()
print('FULL LIFECYCLE PASSED')
"
```

## Notes

- **python3.11**: All backend commands use `python3.11` explicitly — `python3` points to 3.14 on this system which lacks pydantic.
- **ESLint**: `npm run lint` is known to fail (pre-existing: no `eslint.config.js`). Frontend validation uses `npx tsc --noEmit` and `npx vitest run` only.
- **Route ordering**: `GET /alerts/events` MUST be declared before `DELETE /alerts/{rule_id}` in `main.py` to prevent FastAPI from matching "events" as a `{rule_id}` path parameter.
- **Event deque cap**: 200 entries is sufficient for a dashboard that evaluates every 10 seconds. At maximum churn (every eval produces a transition), this covers ~33 minutes of history.
- **AlertPanel follows lifted-state pattern**: Alerts and events state are owned by `App.tsx` (consistent with DD-004, DD-013) and passed as props to `AlertPanel`. The `onAlertChange` callback triggers a re-fetch of both alerts and events.
- **Partial updates via AlertRuleUpdate**: All fields are optional (`| None = None`). The `update_rule()` method only modifies fields that are not None. State is always reset to "ok" on any edit.
