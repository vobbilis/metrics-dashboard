# Plan: Metric Alerting — Phase 1 (Threshold Rules + Background Evaluation)

> **EXECUTION DIRECTIVE**: This is a team-orchestrated plan.
> **FORBIDDEN**: Direct implementation by the main agent. If you are the main conversation agent and a user asks you to implement this plan, you MUST use the `build` prompt with this spec file — do NOT implement it yourself.
> **REQUIRED**: Execute ONLY via the `build` prompt, which orchestrates sub-agents to do the work.

## Task Description

Add a Phase 1 alerting system to the metrics dashboard. Users create threshold alert rules via `POST /alerts` specifying a metric name, comparison operator (`gt`, `lt`, `eq`), and a threshold value. A FastAPI lifespan background task evaluates all rules every 10 seconds against the latest metric value in `MetricStore`. `GET /alerts` returns all rules with their current state (`ok` or `firing`). `DELETE /alerts/{id}` removes a rule. `POST /metrics` is **not** modified — evaluation is decoupled via the background loop. This is Phase 1 of 2; Phase 2 will add SSE streaming of state transitions, so the evaluate method should track transitions for future extensibility.

## Objective

When this plan is complete, the backend will support full CRUD for alert rules, a background evaluator that checks rules every 10 seconds, and a comprehensive test suite covering CRUD operations, evaluation logic, edge cases, and regressions against existing functionality.

## Problem Statement

The metrics dashboard currently has no way to define conditions that should trigger alerts. Users must manually watch metric values to detect anomalies. An alerting layer allows users to declaratively define threshold-based rules and have the system automatically evaluate and surface firing alerts.

## Solution Approach

**Separate AlertStore class** (`backend/alert_store.py`) holds alert rules and evaluation logic, completely independent of `MetricStore`. A module-level singleton `alert_store` is created in `main.py` alongside the existing `store` singleton. Three new routes (`POST /alerts`, `GET /alerts`, `DELETE /alerts/{id}`) handle rule CRUD. A FastAPI lifespan context manager starts an `asyncio` background task that calls `alert_store.evaluate(store)` every 10 seconds. The `evaluate()` method iterates all rules, retrieves the latest metric value from `MetricStore.by_name()`, compares using the rule's operator, and updates the rule's state field. Evaluation returns a list of state transitions (for future SSE use in Phase 2).

## Relevant Files

Use these files to complete the task:

- `backend/models.py` — Add `AlertRuleIn`, `AlertRuleOut`, and supporting types. Follow existing `MetricIn`/`MetricOut` pattern with `Field(...)` for required, `default_factory` for defaults.
- `backend/store.py` — Read-only reference. `MetricStore.by_name(name)` returns `list[MetricOut]` — the evaluator will use `[-1]` to get the latest value. Do NOT modify this file.
- `backend/main.py` — Add alert routes, `alert_store` singleton, and lifespan background task. Currently has no lifespan — needs to be added to the `FastAPI(...)` constructor.
- `backend/tests/test_api.py` — Add alert tests. Currently has 19 tests with an `autouse` fixture that calls `store.clear()`. The alert store must also be cleared in this fixture.
- `frontend/src/api.ts` — NOT modified in Phase 1 (frontend alert UI is out of scope).

### New Files

- `backend/alert_store.py` — New `AlertStore` class with rule CRUD and evaluate logic.

## Implementation Phases

### Phase 1: Foundation
Define all Pydantic models for alert rules and create the `AlertStore` class with CRUD methods and the `evaluate()` method. This is the data layer that all routes and tests depend on.

### Phase 2: Core API
Wire up the three alert routes in `main.py`, create the `alert_store` singleton, and add the FastAPI lifespan background task that drives periodic evaluation.

### Phase 3: Tests
Comprehensive test suite covering alert CRUD, evaluation logic (all three operators, state transitions, no-metric-found edge case), and regression checks against all 19 existing tests.

## Team Orchestration

- The `build` prompt instructs the main agent to act as a **sequential orchestrator**, dispatching sub-agents one task at a time in dependency order.
- The plan is the **single source of truth**. The orchestrator does NOT make decisions. Everything must be specified here: team members, task assignments, dependencies, and exhaustive task descriptions.
- Agents are stateless and cannot ask for clarification. Every task description must be fully self-contained with all context needed for autonomous execution.

### Team Members

- Builder
  - Name: builder-models
  - Role: Data models in `models.py` and alert store in `alert_store.py`
  - Agent Type: builder
- Builder
  - Name: builder-api
  - Role: Alert routes in `main.py` and background evaluation lifespan
  - Agent Type: builder
- Builder
  - Name: builder-tests
  - Role: Comprehensive test suite in `tests/test_api.py`
  - Agent Type: builder
- Validator
  - Name: validator
  - Role: Validates all acceptance criteria and runs validation commands
  - Agent Type: validator

## Step by Step Tasks

- These tasks are executed by the orchestrator dispatching sub-agents sequentially in dependency order.
- Task descriptions must be **exhaustive** — agents cannot ask for clarification. Include ALL context: file paths, code patterns, acceptance criteria, and validation commands.
- Start with foundational work, then core implementation, then validation.

### 1. Add Alert Models to models.py
- **Task ID**: add-alert-models
- **Role**: builder
- **Depends On**: none
- **Assigned To**: builder-models
- **Description**: |
    Add four new types to `backend/models.py` for the alerting feature. These follow the existing `MetricIn`/`MetricOut` pattern already in the file: Pydantic v2 `BaseModel` with `Field(...)` for required fields and `default_factory` for defaults.

    ## What to do
    1. Add a `Literal` type alias `AlertOperator = Literal["gt", "lt", "eq"]` near the top of the file (after imports).
    2. Add a `Literal` type alias `AlertState = Literal["ok", "firing"]` right after `AlertOperator`.
    3. Add `AlertRuleIn(BaseModel)` with fields: `metric_name: str = Field(..., min_length=1, max_length=128)`, `operator: AlertOperator`, `threshold: float`.
    4. Add `AlertRuleOut(BaseModel)` with fields: `id: str`, `metric_name: str`, `operator: AlertOperator`, `threshold: float`, `state: AlertState = "ok"`, `created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))`.
    5. Import `Literal` from `typing` at the top of the file.

    ## Files to modify
    - `backend/models.py` — Add the `Literal` import, `AlertOperator`, `AlertState`, `AlertRuleIn`, and `AlertRuleOut` types after the existing `MetricSummary` class.

    ## Code patterns to follow
    Existing pattern in `backend/models.py`:
    ```python
    class MetricIn(BaseModel):
        name: str = Field(..., min_length=1, max_length=128)
        value: float
        tags: dict[str, str] = Field(default_factory=dict)
    ```
    Follow the same style: `Field(...)` for required with constraints, `default_factory` for computed defaults, explicit type annotations on every field.

    ## Acceptance criteria
    - `AlertOperator` is a `Literal["gt", "lt", "eq"]` type alias
    - `AlertState` is a `Literal["ok", "firing"]` type alias
    - `AlertRuleIn` has fields `metric_name` (str, min 1 / max 128), `operator` (AlertOperator), `threshold` (float) — all required
    - `AlertRuleOut` has fields `id` (str), `metric_name` (str), `operator` (AlertOperator), `threshold` (float), `state` (AlertState, default "ok"), `created_at` (datetime, auto-filled)
    - `from models import AlertRuleIn, AlertRuleOut, AlertOperator, AlertState` succeeds in a Python import check

    ## Validation command
    ```bash
    cd backend && python3.11 -c "from models import AlertRuleIn, AlertRuleOut, AlertOperator, AlertState; r = AlertRuleIn(metric_name='cpu', operator='gt', threshold=90.0); print(r); o = AlertRuleOut(id='x', metric_name='cpu', operator='gt', threshold=90.0); print(o); print('OK')"
    ```

### 2. Create AlertStore with CRUD Methods
- **Task ID**: create-alert-store-crud
- **Role**: builder
- **Depends On**: add-alert-models
- **Assigned To**: builder-models
- **Description**: |
    Create a new file `backend/alert_store.py` containing an `AlertStore` class with CRUD methods for alert rules. This class is independent of `MetricStore` and will be instantiated as a module-level singleton in `main.py` (that happens in a later task — do NOT modify `main.py` here).

    ## What to do
    1. Create `backend/alert_store.py`.
    2. Import `uuid` and the alert models: `from models import AlertRuleIn, AlertRuleOut`.
    3. Define `class AlertStore` with:
       - `__init__(self) -> None` — initializes `self._rules: list[AlertRuleOut] = []`
       - `add_rule(self, rule: AlertRuleIn) -> AlertRuleOut` — creates an `AlertRuleOut` with a new UUID `id`, copies fields from `rule`, sets `state="ok"`, appends to `self._rules`, returns it
       - `all_rules(self) -> list[AlertRuleOut]` — returns `list(self._rules)` (shallow copy)
       - `delete_rule(self, rule_id: str) -> int` — removes the rule with matching `id` from `self._rules`, returns `1` if found, `0` if not found (no error on missing — matches DELETE /metrics/{name} pattern)
       - `clear(self) -> None` — resets `self._rules = []`
    4. All methods must have explicit return type annotations.

    ## Files to modify
    - `backend/alert_store.py` — Create this new file.

    ## Code patterns to follow
    Follow the `MetricStore` pattern in `backend/store.py`:
    ```python
    class MetricStore:
        def __init__(self) -> None:
            self._data: list[MetricOut] = []
        def add(self, metric: MetricIn) -> MetricOut:
            out = MetricOut(id=str(uuid.uuid4()), ...)
            self._data.append(out)
            return out
        def delete(self, name: str) -> int:
            before = len(self._data)
            self._data = [m for m in self._data if m.name != name]
            return before - len(self._data)
        def clear(self) -> None:
            self._data = []
    ```

    ## Acceptance criteria
    - File `backend/alert_store.py` exists
    - `AlertStore` has `__init__`, `add_rule`, `all_rules`, `delete_rule`, and `clear` methods
    - `add_rule` returns an `AlertRuleOut` with a UUID `id` and `state="ok"`
    - `all_rules` returns a shallow copy (not the internal list reference)
    - `delete_rule` returns `1` when rule exists, `0` when it doesn't (never raises)
    - `clear` resets the internal list to empty
    - `ruff check backend/alert_store.py` passes with no errors

    ## Validation command
    ```bash
    cd backend && python3.11 -c "
    from alert_store import AlertStore
    from models import AlertRuleIn
    s = AlertStore()
    r = s.add_rule(AlertRuleIn(metric_name='cpu', operator='gt', threshold=90.0))
    assert r.state == 'ok'
    assert r.metric_name == 'cpu'
    assert len(s.all_rules()) == 1
    assert s.delete_rule(r.id) == 1
    assert s.delete_rule(r.id) == 0
    assert len(s.all_rules()) == 0
    s.clear()
    print('OK')
    " && ruff check alert_store.py
    ```

### 3. Add evaluate() Method to AlertStore
- **Task ID**: add-evaluate-method
- **Role**: builder
- **Depends On**: create-alert-store-crud
- **Assigned To**: builder-models
- **Description**: |
    Add an `evaluate()` method to `AlertStore` in `backend/alert_store.py` that checks all rules against the latest metric values from a `MetricStore` instance. This method is called periodically by the background task (wired in a later task). It must also track state transitions for future SSE use in Phase 2.

    ## What to do
    1. Add `from store import MetricStore` at the top of `backend/alert_store.py`.
    2. Add a type alias or simple dataclass for transitions: for now, just use `list[tuple[str, str, str]]` where each tuple is `(rule_id, old_state, new_state)`. Keep it simple — Phase 2 will formalize this.
    3. Add method `evaluate(self, metric_store: MetricStore) -> list[tuple[str, str, str]]`:
       - Initialize `transitions: list[tuple[str, str, str]] = []`
       - For each rule in `self._rules`:
         - Get metrics: `metrics = metric_store.by_name(rule.metric_name)`
         - If `metrics` is empty: `new_state = "ok"` (no data → not firing)
         - Else: get latest value `latest = metrics[-1].value` and compare:
           - `"gt"`: `new_state = "firing" if latest > rule.threshold else "ok"`
           - `"lt"`: `new_state = "firing" if latest < rule.threshold else "ok"`
           - `"eq"`: `new_state = "firing" if latest == rule.threshold else "ok"`
         - If `new_state != rule.state`: append `(rule.id, rule.state, new_state)` to transitions and update `rule.state = new_state`
       - Return `transitions`
    4. Explicit return type: `-> list[tuple[str, str, str]]`

    ## Files to modify
    - `backend/alert_store.py` — Add `from store import MetricStore` import and the `evaluate()` method to the `AlertStore` class.

    ## Code patterns to follow
    The `MetricStore.by_name()` method returns `list[MetricOut]` — use `metrics[-1].value` for the latest value. Simple if/elif chain for operator comparison. Mutate `rule.state` in place since `AlertRuleOut` is a Pydantic model — use `rule.state = new_state` (Pydantic v2 models are mutable by default).

    ## Acceptance criteria
    - `evaluate(metric_store)` iterates all rules and compares latest metric value against threshold using the specified operator
    - Returns a list of `(rule_id, old_state, new_state)` tuples for every rule that changed state
    - Rules with no matching metrics stay in `"ok"` state
    - `"gt"` operator: fires when `latest > threshold`
    - `"lt"` operator: fires when `latest < threshold`
    - `"eq"` operator: fires when `latest == threshold`
    - State is mutated in place on the rule object
    - `ruff check backend/alert_store.py` passes

    ## Validation command
    ```bash
    cd backend && python3.11 -c "
    from alert_store import AlertStore
    from store import MetricStore
    from models import AlertRuleIn, MetricIn
    ms = MetricStore()
    als = AlertStore()
    rule = als.add_rule(AlertRuleIn(metric_name='cpu', operator='gt', threshold=80.0))
    # No metrics yet — should stay ok
    t1 = als.evaluate(ms)
    assert len(t1) == 0
    assert rule.state == 'ok'
    # Add metric above threshold
    ms.add(MetricIn(name='cpu', value=95.0))
    t2 = als.evaluate(ms)
    assert len(t2) == 1
    assert t2[0] == (rule.id, 'ok', 'firing')
    assert rule.state == 'firing'
    # Evaluate again — no change
    t3 = als.evaluate(ms)
    assert len(t3) == 0
    # Add metric below threshold
    ms.add(MetricIn(name='cpu', value=50.0))
    t4 = als.evaluate(ms)
    assert len(t4) == 1
    assert t4[0] == (rule.id, 'firing', 'ok')
    print('OK')
    " && ruff check alert_store.py
    ```

### 4. Add POST /alerts Route and alert_store Singleton
- **Task ID**: add-post-alerts-route
- **Role**: builder
- **Depends On**: add-evaluate-method
- **Assigned To**: builder-api
- **Description**: |
    Add the `POST /alerts` route to `backend/main.py` and create the `alert_store` module-level singleton. This is the first route modification — subsequent tasks add `GET` and `DELETE`.

    ## What to do
    1. At the top of `backend/main.py`, add imports: `from models import AlertRuleIn, AlertRuleOut` (extend the existing import line) and `from alert_store import AlertStore`.
    2. After the existing `store = MetricStore()` line, add: `alert_store = AlertStore()`
    3. Add a new route after the existing `delete_metric` function:
       ```python
       @app.post("/alerts", response_model=AlertRuleOut, status_code=201)
       def create_alert(rule: AlertRuleIn) -> AlertRuleOut:
           return alert_store.add_rule(rule)
       ```
    4. Ensure the new import line merges cleanly with the existing `from models import MetricIn, MetricOut, MetricSummary` — it should become `from models import AlertRuleIn, AlertRuleOut, MetricIn, MetricOut, MetricSummary` (alphabetical order for ruff's isort).

    ## Files to modify
    - `backend/main.py` — Add imports, `alert_store` singleton, and `POST /alerts` route.

    ## Code patterns to follow
    Existing route pattern in `backend/main.py`:
    ```python
    @app.post("/metrics", response_model=MetricOut, status_code=201)
    def submit_metric(metric: MetricIn) -> MetricOut:
        return store.add(metric)
    ```
    Follow the same style: decorator with `response_model` and `status_code=201`, function with type hints.

    ## Acceptance criteria
    - `alert_store = AlertStore()` exists as a module-level singleton in `main.py`
    - `POST /alerts` accepts `AlertRuleIn` body and returns `AlertRuleOut` with status 201
    - Response includes `id`, `metric_name`, `operator`, `threshold`, `state` ("ok"), and `created_at`
    - `POST /alerts` with `{"metric_name": "cpu", "operator": "gt", "threshold": 90.0}` returns 201 with correct fields
    - `POST /alerts` with `{}` returns 422 (Pydantic validation error)
    - `ruff check backend/main.py` passes

    ## Validation command
    ```bash
    cd backend && python3.11 -c "
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    r = c.post('/alerts', json={'metric_name': 'cpu', 'operator': 'gt', 'threshold': 90.0})
    assert r.status_code == 201, f'Expected 201, got {r.status_code}: {r.text}'
    d = r.json()
    assert d['metric_name'] == 'cpu'
    assert d['operator'] == 'gt'
    assert d['threshold'] == 90.0
    assert d['state'] == 'ok'
    assert 'id' in d
    assert 'created_at' in d
    # Validation error
    r2 = c.post('/alerts', json={})
    assert r2.status_code == 422
    print('OK')
    " && ruff check main.py
    ```

### 5. Add GET /alerts and DELETE /alerts/{id} Routes
- **Task ID**: add-get-delete-alerts-routes
- **Role**: builder
- **Depends On**: add-post-alerts-route
- **Assigned To**: builder-api
- **Description**: |
    Add `GET /alerts` and `DELETE /alerts/{id}` routes to `backend/main.py`. These complete the alert CRUD API.

    ## What to do
    1. Add `GET /alerts` route after the `POST /alerts` route:
       ```python
       @app.get("/alerts", response_model=list[AlertRuleOut])
       def list_alerts() -> list[AlertRuleOut]:
           return alert_store.all_rules()
       ```
    2. Add `DELETE /alerts/{rule_id}` route after `GET /alerts`:
       ```python
       @app.delete("/alerts/{rule_id}")
       def delete_alert(rule_id: str) -> dict[str, int]:
           deleted = alert_store.delete_rule(rule_id)
           return {"deleted": deleted}
       ```
    3. The DELETE route returns `{"deleted": 0}` if the rule doesn't exist (no 404) — matching the existing `DELETE /metrics/{name}` convention.

    ## Files to modify
    - `backend/main.py` — Add `GET /alerts` and `DELETE /alerts/{rule_id}` routes after the existing `POST /alerts` route.

    ## Code patterns to follow
    Existing DELETE pattern in `backend/main.py`:
    ```python
    @app.delete("/metrics/{name}")
    def delete_metric(name: str) -> dict[str, int]:
        deleted = store.delete(name)
        return {"deleted": deleted}
    ```
    Follow the same style: no 404 on missing, return `{"deleted": N}`.

    ## Acceptance criteria
    - `GET /alerts` returns 200 with a JSON array of all alert rules
    - `GET /alerts` returns `[]` when no rules exist
    - `DELETE /alerts/{rule_id}` returns `{"deleted": 1}` when rule exists
    - `DELETE /alerts/{rule_id}` returns `{"deleted": 0}` when rule doesn't exist (no 404)
    - After deleting a rule, `GET /alerts` no longer includes it
    - `ruff check backend/main.py` passes

    ## Validation command
    ```bash
    cd backend && python3.11 -c "
    from fastapi.testclient import TestClient
    from main import app, alert_store
    alert_store.clear()
    c = TestClient(app)
    # Empty initially
    assert c.get('/alerts').json() == []
    # Create one
    r = c.post('/alerts', json={'metric_name': 'cpu', 'operator': 'gt', 'threshold': 90.0})
    rule_id = r.json()['id']
    # GET returns it
    alerts = c.get('/alerts').json()
    assert len(alerts) == 1
    assert alerts[0]['id'] == rule_id
    # DELETE it
    dr = c.delete(f'/alerts/{rule_id}')
    assert dr.json() == {'deleted': 1}
    # DELETE again — 0, no 404
    dr2 = c.delete(f'/alerts/{rule_id}')
    assert dr2.json() == {'deleted': 0}
    assert dr2.status_code == 200
    # Gone
    assert c.get('/alerts').json() == []
    alert_store.clear()
    print('OK')
    " && ruff check main.py
    ```

### 6. Add Background Evaluation with FastAPI Lifespan
- **Task ID**: add-background-evaluation
- **Role**: builder
- **Depends On**: add-get-delete-alerts-routes
- **Assigned To**: builder-api
- **Description**: |
    Add a FastAPI lifespan context manager to `backend/main.py` that starts an asyncio background task to evaluate alert rules every 10 seconds. The current `app = FastAPI(...)` does NOT have a lifespan — this task adds one.

    ## What to do
    1. Add imports at the top of `backend/main.py`:
       ```python
       import asyncio
       from contextlib import asynccontextmanager
       ```
    2. Before the `app = FastAPI(...)` line, define the lifespan and background task:
       ```python
       async def _evaluate_loop() -> None:
           while True:
               await asyncio.sleep(10)
               alert_store.evaluate(store)

       @asynccontextmanager
       async def lifespan(app: FastAPI):
           task = asyncio.create_task(_evaluate_loop())
           yield
           task.cancel()
           try:
               await task
           except asyncio.CancelledError:
               pass
       ```
    3. Modify the `FastAPI(...)` constructor to include the lifespan:
       ```python
       app = FastAPI(title="Metrics Dashboard API", version="0.1.0", lifespan=lifespan)
       ```
    4. Note: The `_evaluate_loop` sleeps FIRST, then evaluates. This avoids evaluating with empty state on startup. The 10-second interval is hardcoded for Phase 1; Phase 2 may make it configurable.
    5. The `lifespan` function parameter is named `app` (shadowing the module-level `app`). This is the FastAPI convention — use `app: FastAPI` as the parameter name. Add a `# noqa: ARG001` comment if ruff complains about unused parameter, OR rename it to `_app` to suppress the warning.

    ## Files to modify
    - `backend/main.py` — Add `asyncio` and `asynccontextmanager` imports, define `_evaluate_loop()` and `lifespan()`, modify `FastAPI(...)` constructor.

    ## Code patterns to follow
    FastAPI lifespan pattern (official):
    ```python
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # startup logic
        yield
        # shutdown logic
    app = FastAPI(lifespan=lifespan)
    ```

    ## Acceptance criteria
    - `_evaluate_loop()` is an async function that loops forever: sleep 10s, then call `alert_store.evaluate(store)`
    - `lifespan()` creates the task on startup and cancels it on shutdown
    - `app = FastAPI(... lifespan=lifespan)` passes the lifespan to the app
    - The app still starts and serves requests normally (existing routes unaffected)
    - `ruff check backend/main.py` passes
    - All 19 existing tests still pass: `cd backend && python3.11 -m pytest tests/ -v`

    ## Validation command
    ```bash
    cd backend && ruff check main.py && python3.11 -m pytest tests/ -v --tb=short 2>&1 | tail -5
    ```

### 7. Intermediate Validation — Phase 1 & 2
- **Task ID**: validate-phase-1-2
- **Role**: validator
- **Depends On**: add-background-evaluation
- **Assigned To**: validator
- **Description**: |
    Intermediate validation after Phase 1 (Foundation) and Phase 2 (Core API) to catch regressions before adding tests. This checks that all new code is correct and all existing tests still pass.

    ## Validation Commands
    Run these commands and verify all pass:
    1. Python lint (entire backend): `cd backend && ruff check .`
    2. All existing tests pass (19 tests): `cd backend && python3.11 -m pytest tests/ -v`
    3. Alert models import correctly: `cd backend && python3.11 -c "from models import AlertRuleIn, AlertRuleOut, AlertOperator, AlertState; print('Models OK')"`
    4. AlertStore works end-to-end: `cd backend && python3.11 -c "from alert_store import AlertStore; from store import MetricStore; from models import AlertRuleIn, MetricIn; ms=MetricStore(); als=AlertStore(); r=als.add_rule(AlertRuleIn(metric_name='cpu',operator='gt',threshold=80.0)); ms.add(MetricIn(name='cpu',value=95.0)); t=als.evaluate(ms); assert len(t)==1; print('Store OK')"`
    5. Alert routes respond correctly: `cd backend && python3.11 -c "from fastapi.testclient import TestClient; from main import app, alert_store; alert_store.clear(); c=TestClient(app); r=c.post('/alerts',json={'metric_name':'cpu','operator':'gt','threshold':90.0}); assert r.status_code==201; assert len(c.get('/alerts').json())==1; alert_store.clear(); print('Routes OK')"`
    6. App starts with lifespan: `cd backend && python3.11 -c "from main import app; assert app.router.lifespan_context is not None; print('Lifespan OK')"`

    ## Acceptance Criteria
    - `ruff check .` reports 0 errors across all backend files
    - All 19 existing tests pass with 0 failures
    - Alert models (`AlertRuleIn`, `AlertRuleOut`, `AlertOperator`, `AlertState`) import successfully
    - `AlertStore` CRUD + evaluate works correctly in isolation
    - `POST /alerts`, `GET /alerts`, `DELETE /alerts/{id}` routes respond with correct status codes
    - App has a lifespan context manager configured

### 8. Alert CRUD Tests
- **Task ID**: add-alert-crud-tests
- **Role**: builder
- **Depends On**: validate-phase-1-2
- **Assigned To**: builder-tests
- **Description**: |
    Add alert CRUD tests to `backend/tests/test_api.py`. These tests cover creating, listing, and deleting alert rules via the API.

    ## What to do
    1. First, update the existing `clear_store` autouse fixture to also clear the alert store. Add `from main import alert_store` to the imports at the top of the file (alongside the existing `from main import app, store`). Then modify the fixture:
       ```python
       @pytest.fixture(autouse=True)
       def clear_store():
           store.clear()
           alert_store.clear()
           yield
           store.clear()
           alert_store.clear()
       ```
    2. Add these test functions at the bottom of the file:

       **test_create_alert_rule**: POST `/alerts` with `{"metric_name": "cpu", "operator": "gt", "threshold": 90.0}`. Assert: status 201, response has `id`, `metric_name == "cpu"`, `operator == "gt"`, `threshold == 90.0`, `state == "ok"`, `created_at` is present.

       **test_create_alert_rule_validation_error**: POST `/alerts` with `{}`. Assert: status 422.

       **test_create_alert_rule_invalid_operator**: POST `/alerts` with `{"metric_name": "cpu", "operator": "invalid", "threshold": 90.0}`. Assert: status 422.

       **test_list_alerts_empty**: GET `/alerts`. Assert: status 200, body is `[]`.

       **test_list_alerts**: POST two rules, then GET `/alerts`. Assert: status 200, body has 2 items.

       **test_delete_alert_rule**: POST a rule, capture `id`, DELETE `/alerts/{id}`. Assert: status 200, `{"deleted": 1}`. Then GET `/alerts` and assert empty.

       **test_delete_alert_rule_not_found**: DELETE `/alerts/nonexistent-id`. Assert: status 200, `{"deleted": 0}`.

    3. Use the existing `client = TestClient(app)` module-level variable — do NOT create a new one.

    ## Files to modify
    - `backend/tests/test_api.py` — Update imports and `clear_store` fixture, add 7 new test functions.

    ## Code patterns to follow
    Existing test pattern in the file:
    ```python
    def test_submit_metric():
        r = client.post("/metrics", json={"name": "cpu", "value": 42.5})
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "cpu"
    ```
    Follow the same style: plain functions, `client.post/get/delete`, assert on status code, then assert on response body fields.

    ## Acceptance criteria
    - `clear_store` fixture clears both `store` and `alert_store`
    - 7 new test functions exist for alert CRUD
    - `test_create_alert_rule` verifies all 6 response fields
    - `test_create_alert_rule_validation_error` verifies 422 on empty body
    - `test_create_alert_rule_invalid_operator` verifies 422 on bad operator
    - `test_list_alerts_empty` verifies empty list
    - `test_list_alerts` verifies correct count
    - `test_delete_alert_rule` verifies deletion and subsequent GET
    - `test_delete_alert_rule_not_found` verifies `{"deleted": 0}` without 404
    - All new tests pass: `cd backend && python3.11 -m pytest tests/test_api.py -v -k alert`

    ## Validation command
    ```bash
    cd backend && python3.11 -m pytest tests/test_api.py -v -k "alert" --tb=short
    ```

### 9. Alert Evaluation Tests
- **Task ID**: add-alert-evaluation-tests
- **Role**: builder
- **Depends On**: add-alert-crud-tests
- **Assigned To**: builder-tests
- **Description**: |
    Add tests for the alert evaluation logic to `backend/tests/test_api.py`. These tests verify that rules transition between `ok` and `firing` states correctly when metrics are submitted and `evaluate()` is called.

    ## What to do
    Add these test functions at the bottom of `backend/tests/test_api.py`:

    **test_evaluate_gt_fires**: Create a rule `{metric_name: "cpu", operator: "gt", threshold: 80.0}`. Submit metric `{name: "cpu", value: 95.0}`. Call `alert_store.evaluate(store)` directly (import `alert_store` from `main`). GET `/alerts` and assert the rule's state is `"firing"`.

    **test_evaluate_gt_ok**: Create a rule `{metric_name: "cpu", operator: "gt", threshold: 80.0}`. Submit metric `{name: "cpu", value: 50.0}`. Evaluate. Assert state is `"ok"`.

    **test_evaluate_lt_fires**: Create a rule `{metric_name: "mem", operator: "lt", threshold: 20.0}`. Submit metric `{name: "mem", value: 10.0}`. Evaluate. Assert state is `"firing"`.

    **test_evaluate_eq_fires**: Create a rule `{metric_name: "disk", operator: "eq", threshold: 100.0}`. Submit metric `{name: "disk", value: 100.0}`. Evaluate. Assert state is `"firing"`.

    **test_evaluate_no_metrics_stays_ok**: Create a rule `{metric_name: "cpu", operator: "gt", threshold: 80.0}`. Evaluate without submitting any metrics. Assert state is `"ok"`.

    **test_evaluate_state_transition**: Create a rule `{metric_name: "cpu", operator: "gt", threshold: 80.0}`. Submit `value: 95.0`, evaluate → firing. Submit `value: 50.0`, evaluate → ok. Submit `value: 99.0`, evaluate → firing. Assert state transitions at each step.

    Important implementation detail: the tests call `alert_store.evaluate(store)` directly using the imported singletons from `main`. They do NOT rely on the background task. The `alert_store` import was already added to the file in task 8 (`from main import alert_store`).

    ## Files to modify
    - `backend/tests/test_api.py` — Add 6 new evaluation test functions at the bottom of the file.

    ## Code patterns to follow
    Pattern for evaluation tests:
    ```python
    def test_evaluate_gt_fires():
        # Create rule via API
        r = client.post("/alerts", json={"metric_name": "cpu", "operator": "gt", "threshold": 80.0})
        # Submit metric via API
        client.post("/metrics", json={"name": "cpu", "value": 95.0})
        # Evaluate directly
        alert_store.evaluate(store)
        # Check state via API
        alerts = client.get("/alerts").json()
        assert alerts[0]["state"] == "firing"
    ```

    ## Acceptance criteria
    - 6 new test functions exist for evaluation logic
    - `test_evaluate_gt_fires` verifies `>` threshold → `"firing"`
    - `test_evaluate_gt_ok` verifies `≤` threshold → `"ok"`
    - `test_evaluate_lt_fires` verifies `<` threshold → `"firing"`
    - `test_evaluate_eq_fires` verifies `==` threshold → `"firing"`
    - `test_evaluate_no_metrics_stays_ok` verifies no metrics → `"ok"`
    - `test_evaluate_state_transition` verifies full cycle: ok → firing → ok → firing
    - All new tests pass: `cd backend && python3.11 -m pytest tests/test_api.py -v -k evaluate`

    ## Validation command
    ```bash
    cd backend && python3.11 -m pytest tests/test_api.py -v -k "evaluate" --tb=short
    ```

### 10. Edge Case and Regression Tests
- **Task ID**: add-edge-case-tests
- **Role**: builder
- **Depends On**: add-alert-evaluation-tests
- **Assigned To**: builder-tests
- **Description**: |
    Add edge case tests and verify no regressions in existing functionality. These tests cover boundary conditions and confirm that the alerting feature doesn't break any existing metric operations.

    ## What to do
    Add these test functions at the bottom of `backend/tests/test_api.py`:

    **test_alert_rule_with_long_metric_name**: POST `/alerts` with `metric_name` of 128 characters (max allowed). Assert 201. Then POST with 129 characters — assert 422.

    **test_alert_rule_empty_metric_name**: POST `/alerts` with `metric_name: ""`. Assert 422 (min_length=1).

    **test_multiple_rules_same_metric**: Create two rules for "cpu": one `gt 80`, one `lt 20`. Submit `value: 95.0`, evaluate. Assert first rule is `"firing"`, second is `"ok"`. Submit `value: 10.0`, evaluate. Assert first is `"ok"`, second is `"firing"`.

    **test_delete_metric_does_not_affect_alert_rules**: Create alert rule for "cpu". Submit metric "cpu". Delete metric "cpu" via `DELETE /metrics/cpu`. Assert alert rule still exists in `GET /alerts`. Evaluate — rule should be `"ok"` (no metrics to compare).

    **test_existing_metrics_unaffected_by_alerts**: Submit metrics, create alert rules, evaluate. Then verify `GET /metrics`, `GET /metrics/{name}`, `GET /metrics/{name}/history`, `DELETE /metrics/{name}` all work as before.

    ## Files to modify
    - `backend/tests/test_api.py` — Add 5 new test functions at the bottom of the file.

    ## Code patterns to follow
    Follow the same test pattern used throughout the file. For validation error tests:
    ```python
    def test_get_metric_not_found():
        r = client.get("/metrics/nonexistent")
        assert r.status_code == 404
    ```

    ## Acceptance criteria
    - 5 new edge case test functions exist
    - Max length metric name (128 chars) is accepted; 129 chars is rejected
    - Empty metric name is rejected with 422
    - Multiple rules on same metric evaluate independently
    - Deleting a metric doesn't delete or break its alert rules
    - Existing metric operations (CRUD, history, summary) work normally alongside alerts
    - ALL tests pass (existing 19 + new 18 = 37 total): `cd backend && python3.11 -m pytest tests/ -v`

    ## Validation command
    ```bash
    cd backend && python3.11 -m pytest tests/ -v --tb=short 2>&1 | tail -10
    ```

### 11. Final Validation
- **Task ID**: validate-all
- **Role**: validator
- **Depends On**: add-edge-case-tests
- **Assigned To**: validator
- **Description**: |
    Run all validation commands and verify all acceptance criteria for the complete metric alerting Phase 1 feature.

    ## Validation Commands
    Run ALL of these commands and verify they pass:
    1. Python lint entire backend: `cd backend && ruff check .`
    2. Python format check: `cd backend && ruff format --check .`
    3. Full test suite (expect 37 tests, 0 failures): `cd backend && python3.11 -m pytest tests/ -v`
    4. Frontend typecheck (no regressions): `cd frontend && npx tsc --noEmit`
    5. Alert models import: `cd backend && python3.11 -c "from models import AlertRuleIn, AlertRuleOut, AlertOperator, AlertState; print('Models OK')"`
    6. AlertStore import and CRUD: `cd backend && python3.11 -c "from alert_store import AlertStore; from models import AlertRuleIn; s=AlertStore(); r=s.add_rule(AlertRuleIn(metric_name='cpu',operator='gt',threshold=90.0)); assert r.state=='ok'; assert s.delete_rule(r.id)==1; print('Store OK')"`
    7. All three alert routes work: `cd backend && python3.11 -c "from fastapi.testclient import TestClient; from main import app, alert_store; alert_store.clear(); c=TestClient(app); r=c.post('/alerts',json={'metric_name':'cpu','operator':'gt','threshold':90.0}); assert r.status_code==201; rid=r.json()['id']; assert len(c.get('/alerts').json())==1; d=c.delete(f'/alerts/{rid}'); assert d.json()=={'deleted':1}; alert_store.clear(); print('Routes OK')"`
    8. Evaluation works end-to-end: `cd backend && python3.11 -c "from fastapi.testclient import TestClient; from main import app, store, alert_store; store.clear(); alert_store.clear(); c=TestClient(app); c.post('/alerts',json={'metric_name':'cpu','operator':'gt','threshold':80.0}); c.post('/metrics',json={'name':'cpu','value':95.0}); alert_store.evaluate(store); alerts=c.get('/alerts').json(); assert alerts[0]['state']=='firing'; store.clear(); alert_store.clear(); print('Evaluation OK')"`
    9. Health endpoint still works: `cd backend && python3.11 -c "from fastapi.testclient import TestClient; from main import app; c=TestClient(app); assert c.get('/health').json()=={'status':'ok'}; print('Health OK')"`

    ## Acceptance Criteria
    - `ruff check .` — 0 errors
    - `ruff format --check .` — no reformatting needed
    - `pytest tests/ -v` — 37 tests pass, 0 failures, 0 errors
    - `npx tsc --noEmit` — no TypeScript errors (frontend unchanged but verify no regressions)
    - Alert models exist with correct types and fields
    - AlertStore CRUD works (add, list, delete, clear)
    - Three alert routes respond correctly (POST 201, GET 200, DELETE 200)
    - Evaluation transitions rules between "ok" and "firing" based on latest metric value
    - Health endpoint returns `{"status": "ok"}`
    - No regressions in any existing functionality (metrics CRUD, history, summary)
    - `backend/alert_store.py` exists as a new file
    - `backend/models.py` contains `AlertRuleIn`, `AlertRuleOut`, `AlertOperator`, `AlertState`
    - `backend/main.py` has `alert_store` singleton and lifespan background task

## Acceptance Criteria

1. `POST /alerts` with `{"metric_name": "cpu", "operator": "gt", "threshold": 90.0}` returns 201 with `id`, `metric_name`, `operator`, `threshold`, `state` ("ok"), and `created_at`
2. `POST /alerts` with invalid body returns 422
3. `GET /alerts` returns 200 with list of all alert rules and their current state
4. `DELETE /alerts/{id}` returns `{"deleted": 1}` when rule exists, `{"deleted": 0}` when not (no 404)
5. Background evaluation runs every 10 seconds via FastAPI lifespan
6. `"gt"` operator fires when latest metric value > threshold
7. `"lt"` operator fires when latest metric value < threshold
8. `"eq"` operator fires when latest metric value == threshold
9. Rules with no matching metrics stay in `"ok"` state
10. State transitions are tracked (ok → firing, firing → ok) for future SSE use
11. All 37 tests pass (19 existing + 18 new)
12. `ruff check .` and `ruff format --check .` pass
13. No regressions in existing metric CRUD, history, or summary endpoints

## Validation Commands

Execute these commands to validate the task is complete:

```bash
# Lint
cd backend && ruff check .

# Format
cd backend && ruff format --check .

# Full test suite (37 tests expected)
cd backend && python3.11 -m pytest tests/ -v

# Frontend typecheck (no regressions)
cd frontend && npx tsc --noEmit

# Smoke test — alert CRUD + evaluation
cd backend && python3.11 -c "
from fastapi.testclient import TestClient
from main import app, store, alert_store
store.clear(); alert_store.clear()
c = TestClient(app)
# Create rule
r = c.post('/alerts', json={'metric_name': 'cpu', 'operator': 'gt', 'threshold': 80.0})
assert r.status_code == 201
# Submit metric above threshold
c.post('/metrics', json={'name': 'cpu', 'value': 95.0})
# Evaluate
alert_store.evaluate(store)
# Check state
alerts = c.get('/alerts').json()
assert alerts[0]['state'] == 'firing', f'Expected firing, got {alerts[0][\"state\"]}'
# Cleanup
store.clear(); alert_store.clear()
print('ALL SMOKE TESTS PASSED')
"
```

## Notes

- **Phase 2 extensibility**: The `evaluate()` method returns `list[tuple[str, str, str]]` (rule_id, old_state, new_state) for state transitions. Phase 2 will use this to stream transitions via SSE.
- **Brainstorming outcome**: User chose background task approach (d) over inline evaluation on POST /metrics. The 10-second interval is hardcoded; Phase 2 may make it configurable.
- **Float equality**: The `"eq"` operator uses exact float comparison (`==`). This is acceptable for the testbed scope. Production systems would use epsilon-based comparison.
- **No frontend changes**: Phase 1 is backend-only. Frontend alert UI would be a separate plan.
- **python3.11**: All commands use `python3.11` explicitly — `python3` points to 3.14 on this system which lacks pydantic.
- **ESLint**: `npm run lint` is known to fail (pre-existing: no `eslint.config.js`). Frontend validation uses `npx tsc --noEmit` only.
