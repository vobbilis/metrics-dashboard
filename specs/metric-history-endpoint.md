# Plan: Metric History Endpoint

> **EXECUTION DIRECTIVE**: This is a team-orchestrated plan.
> **FORBIDDEN**: Direct implementation by the main agent. If you are the main conversation agent and a user asks you to implement this plan, you MUST use the `build` prompt with this spec file — do NOT implement it yourself.
> **REQUIRED**: Execute ONLY via the `build` prompt, which orchestrates sub-agents to do the work.

## Task Description

Add metric history tracking to the metrics dashboard. The backend should store the last 20 values submitted for each metric name using a separate `dict[str, deque[MetricOut]]` data structure (alongside the existing flat `_data` list). Expose a new `GET /metrics/{name}/history?limit=N` endpoint that returns the most recent N entries (default 20, max 20) for a given metric name. The frontend needs a new `fetchMetricHistory()` API client function. Include comprehensive backend tests for the new endpoint and the history storage logic.

## Objective

When this plan is complete:
- `POST /metrics` still works as before AND also appends to a per-name history deque (capped at 20)
- `GET /metrics/{name}/history` returns the last N values for that metric name (default N=20)
- `GET /metrics/{name}/history?limit=5` returns only the last 5
- `DELETE /metrics/{name}` clears the history for that name too
- `store.clear()` clears the history dict too
- All existing tests still pass
- New tests cover history storage, the endpoint, limit parameter, 404 for unknown names, and interaction with delete

## Problem Statement

The dashboard currently stores all metrics in a flat list. There's no way to see the recent trend for a single metric name (e.g., "what were the last 10 CPU readings?"). Users need a history endpoint that returns only the latest N values per metric, capped at 20 to bound memory.

## Solution Approach

Use option (b) from brainstorming: add a **separate `_history: dict[str, deque[MetricOut]]`** with `maxlen=20` to `MetricStore`. The existing `_data` flat list stays untouched — all current methods (`all()`, `by_name()`, `summary()`) continue to work against `_data`. The `add()` method additionally appends to `_history[name]`. A new `history(name, limit)` method reads from `_history`. The `delete()` and `clear()` methods are extended to also clean history.

This approach:
- Zero risk to existing functionality (flat list untouched)
- O(1) append to deque, automatic eviction when >20
- Clean separation of concerns

## Relevant Files

Use these files to complete the task:

- `backend/store.py` — add `_history` dict and `history()` method, update `add()`, `delete()`, `clear()`
- `backend/models.py` — add `HistoryResponse` model (optional, for typed response)
- `backend/main.py` — add `GET /metrics/{name}/history` route with `limit` query param
- `backend/tests/test_api.py` — add tests for the history endpoint and edge cases
- `frontend/src/api.ts` — add `fetchMetricHistory()` function

### New Files

None — all changes are to existing files.

## Implementation Phases

### Phase 1: Foundation
Add the `_history` deque to `MetricStore` and wire it into `add()`, `delete()`, `clear()`.

### Phase 2: Core Implementation
Add the `history()` store method, the `GET /metrics/{name}/history` route, and the frontend API function.

### Phase 3: Integration & Polish
Write comprehensive tests covering happy path, limits, 404s, delete interaction, and deque cap behavior.

## Team Orchestration

- The `build` prompt instructs the main agent to act as a **sequential orchestrator**, dispatching sub-agents one task at a time in dependency order.
- The plan is the **single source of truth**. The orchestrator does NOT make decisions. Everything must be specified here: team members, task assignments, dependencies, and exhaustive task descriptions.
- Agents are stateless and cannot ask for clarification. Every task description must be fully self-contained with all context needed for autonomous execution.

### Team Members

- Builder
  - Name: builder-1
  - Role: Backend implementation (store, models, routes, tests) and frontend API client
  - Agent Type: builder
- Validator
  - Name: validator
  - Role: Validates all acceptance criteria and runs validation commands
  - Agent Type: validator

## Step by Step Tasks

- These tasks are executed by the orchestrator dispatching sub-agents sequentially in dependency order.
- Task descriptions must be **exhaustive** — agents cannot ask for clarification. Include ALL context: file paths, code patterns, acceptance criteria, and validation commands.
- Start with foundational work, then core implementation, then validation.

### 1. Add History Deque to MetricStore
- **Task ID**: add-history-deque
- **Role**: builder
- **Depends On**: none
- **Assigned To**: builder-1
- **Description**: |
    Add a per-name history deque to `MetricStore` in `backend/store.py`. This is the foundational
    data structure that all other tasks depend on.

    ## What to do
    1. Add `from collections import deque` to the imports in `backend/store.py`.
    2. In `MetricStore.__init__`, add: `self._history: dict[str, deque[MetricOut]] = {}`
    3. In `MetricStore.add()`, after `self._data.append(out)`, add logic to append to history:
       ```python
       if metric.name not in self._history:
           self._history[metric.name] = deque(maxlen=20)
       self._history[metric.name].append(out)
       ```
    4. In `MetricStore.delete()`, after filtering `self._data`, also pop the name from `_history`:
       ```python
       self._history.pop(name, None)
       ```
    5. In `MetricStore.clear()`, add: `self._history = {}`

    ## Files to modify
    - `backend/store.py` — add import, add `_history` field, update `add()`, `delete()`, `clear()`

    ## Code patterns to follow
    - Follow the existing pattern in `store.py`: simple methods, type hints, no threading.
    - `_data` is a plain list; `_history` is a dict of deques. Both are private with `_` prefix.

    ## Acceptance criteria
    - `MetricStore()` has a `_history` attribute that is an empty dict
    - After calling `add(MetricIn(name="cpu", value=1.0))` three times, `store._history["cpu"]` has 3 entries
    - After calling `delete("cpu")`, `store._history` does not contain "cpu"
    - After calling `clear()`, `store._history` is empty
    - All existing tests still pass (the flat `_data` list is unchanged)

    ## Validation command
    ```bash
    cd backend && python -c "
    from store import MetricStore
    from models import MetricIn
    s = MetricStore()
    s.add(MetricIn(name='cpu', value=1.0))
    s.add(MetricIn(name='cpu', value=2.0))
    assert len(s._history['cpu']) == 2, f'Expected 2, got {len(s._history[\"cpu\"])}'
    s.delete('cpu')
    assert 'cpu' not in s._history, 'cpu should be deleted from history'
    s.add(MetricIn(name='mem', value=50.0))
    s.clear()
    assert s._history == {}, 'history should be empty after clear'
    print('ALL CHECKS PASSED')
    " && pytest tests/ -v
    ```

### 2. Add History Store Method
- **Task ID**: add-history-method
- **Role**: builder
- **Depends On**: add-history-deque
- **Assigned To**: builder-1
- **Description**: |
    Add a `history(name, limit)` method to `MetricStore` that returns the last N entries
    from the per-name history deque.

    ## What to do
    1. In `backend/store.py`, add this method to `MetricStore`:
       ```python
       def history(self, name: str, limit: int = 20) -> list[MetricOut]:
           entries = self._history.get(name)
           if entries is None:
               return []
           limit = max(1, min(limit, 20))
           return list(entries)[-limit:]
       ```
    2. The method returns an empty list if the name is not found (not an error at store level).
    3. The `limit` is clamped between 1 and 20.
    4. `list(entries)[-limit:]` returns the most recent `limit` entries (deque is ordered oldest→newest).

    ## Files to modify
    - `backend/store.py` — add `history()` method

    ## Code patterns to follow
    - Follow the pattern of `by_name()`: returns `list[MetricOut]`, takes `name: str`.
    - Return type is `list[MetricOut]` (not deque).

    ## Acceptance criteria
    - `store.history("cpu")` returns empty list when no "cpu" metrics exist
    - After adding 5 "cpu" metrics, `store.history("cpu")` returns all 5 (newest last)
    - `store.history("cpu", limit=2)` returns only the last 2 entries
    - After adding 25 "cpu" metrics, `store.history("cpu")` returns exactly 20 (deque cap)
    - `store.history("cpu", limit=0)` returns 1 entry (clamped to min 1)
    - `store.history("cpu", limit=100)` returns 20 entries (clamped to max 20)

    ## Validation command
    ```bash
    cd backend && python -c "
    from store import MetricStore
    from models import MetricIn
    s = MetricStore()
    assert s.history('cpu') == [], 'empty history expected'
    for i in range(25):
        s.add(MetricIn(name='cpu', value=float(i)))
    h = s.history('cpu')
    assert len(h) == 20, f'Expected 20, got {len(h)}'
    assert h[-1].value == 24.0, f'Last value should be 24.0, got {h[-1].value}'
    assert h[0].value == 5.0, f'First value should be 5.0, got {h[0].value}'
    h2 = s.history('cpu', limit=3)
    assert len(h2) == 3, f'Expected 3, got {len(h2)}'
    assert h2[-1].value == 24.0
    print('ALL CHECKS PASSED')
    "
    ```

### 3. Add History Route to FastAPI
- **Task ID**: add-history-route
- **Role**: builder
- **Depends On**: add-history-method
- **Assigned To**: builder-1
- **Description**: |
    Add a `GET /metrics/{name}/history` endpoint to `backend/main.py` that returns
    the last N metric values for a given name.

    ## What to do
    1. In `backend/main.py`, add this route BEFORE the existing `@app.get("/metrics/{name}")` route
       (so FastAPI matches `/metrics/{name}/history` before `{name}` catches "history"):
       ```python
       @app.get("/metrics/{name}/history", response_model=list[MetricOut])
       def get_metric_history(name: str, limit: int = 20) -> list[MetricOut]:
           results = store.history(name, limit)
           if not results:
               raise HTTPException(status_code=404, detail=f"No history found for '{name}'")
           return results
       ```
    2. The `limit` query parameter defaults to 20. FastAPI will parse `?limit=5` automatically.
    3. Return 404 if no history exists for that name (empty list from store).
    4. IMPORTANT: This route MUST be defined before `@app.get("/metrics/{name}")` in the file,
       otherwise FastAPI will match `{name}="history"` first.

    ## Files to modify
    - `backend/main.py` — add the `/metrics/{name}/history` route before the `/{name}` route

    ## Code patterns to follow
    - Follow the existing `get_metric()` route pattern: same error style, same `response_model`.
    - Use `HTTPException(status_code=404, detail=f"No history found for '{name}'")`.
    - Return type annotation `list[MetricOut]`.

    ## Acceptance criteria
    - `GET /metrics/cpu/history` returns 200 with a list of MetricOut objects (after posting some cpu metrics)
    - `GET /metrics/cpu/history?limit=3` returns at most 3 entries
    - `GET /metrics/nonexistent/history` returns 404 with `{"detail": "No history found for 'nonexistent'"}`
    - The existing `GET /metrics/{name}` route still works (not shadowed)
    - `GET /metrics/summary` still works (not broken by route ordering)

    ## Validation command
    ```bash
    cd backend && python -c "
    from fastapi.testclient import TestClient
    from main import app, store
    store.clear()
    c = TestClient(app)
    c.post('/metrics', json={'name': 'cpu', 'value': 10.0})
    c.post('/metrics', json={'name': 'cpu', 'value': 20.0})
    r = c.get('/metrics/cpu/history')
    assert r.status_code == 200, f'Expected 200, got {r.status_code}'
    assert len(r.json()) == 2, f'Expected 2, got {len(r.json())}'
    r2 = c.get('/metrics/cpu/history?limit=1')
    assert len(r2.json()) == 1, f'Expected 1, got {len(r2.json())}'
    r3 = c.get('/metrics/nonexistent/history')
    assert r3.status_code == 404, f'Expected 404, got {r3.status_code}'
    r4 = c.get('/metrics/summary')
    assert r4.status_code == 200, f'Summary broken, got {r4.status_code}'
    r5 = c.get('/metrics/cpu')
    assert r5.status_code == 200, f'by_name broken, got {r5.status_code}'
    store.clear()
    print('ALL CHECKS PASSED')
    "
    ```

### 4. Add Frontend API Client Function
- **Task ID**: add-frontend-api
- **Role**: builder
- **Depends On**: add-history-route
- **Assigned To**: builder-1
- **Description**: |
    Add a `fetchMetricHistory()` function to the frontend API client in `frontend/src/api.ts`.

    ## What to do
    1. In `frontend/src/api.ts`, add this function after the existing `deleteMetric()` function:
       ```typescript
       export async function fetchMetricHistory(
         name: string,
         limit: number = 20,
       ): Promise<Metric[]> {
         const res = await fetch(`${BASE}/metrics/${name}/history?limit=${limit}`)
         if (!res.ok) throw new Error(`Failed to fetch metric history: ${res.status}`)
         return res.json()
       }
       ```
    2. The function reuses the existing `Metric` interface (no new types needed).
    3. Follow the exact same pattern as `fetchMetrics()`: same error handling, same return type.

    ## Files to modify
    - `frontend/src/api.ts` — add `fetchMetricHistory()` function

    ## Code patterns to follow
    - Follow the existing `fetchMetrics()` pattern exactly: raw `fetch()`, throw on `!res.ok`, return `res.json()`.
    - Use the existing `Metric` interface as return type.
    - Base URL is `'/api'` (the `BASE` constant).

    ## Acceptance criteria
    - `fetchMetricHistory` is exported from `frontend/src/api.ts`
    - Function signature: `(name: string, limit?: number) => Promise<Metric[]>`
    - Uses `${BASE}/metrics/${name}/history?limit=${limit}` URL pattern
    - Throws on non-ok response
    - TypeScript compiles without errors

    ## Validation command
    ```bash
    cd frontend && npx tsc --noEmit && echo "TYPECHECK PASSED"
    ```

### 5. Add Backend Tests for History
- **Task ID**: add-history-tests
- **Role**: builder
- **Depends On**: add-history-route
- **Assigned To**: builder-1
- **Description**: |
    Add comprehensive tests for the metric history feature in `backend/tests/test_api.py`.
    These tests verify the endpoint, limit parameter, 404 behavior, delete interaction,
    and deque cap.

    ## What to do
    1. In `backend/tests/test_api.py`, add these test functions after the existing tests:

    ```python
    def test_history_returns_submitted_metrics():
        client.post("/metrics", json={"name": "cpu", "value": 10.0})
        client.post("/metrics", json={"name": "cpu", "value": 20.0})
        client.post("/metrics", json={"name": "cpu", "value": 30.0})
        r = client.get("/metrics/cpu/history")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        assert data[0]["value"] == 10.0
        assert data[2]["value"] == 30.0


    def test_history_limit_parameter():
        for i in range(10):
            client.post("/metrics", json={"name": "cpu", "value": float(i)})
        r = client.get("/metrics/cpu/history?limit=3")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        assert data[-1]["value"] == 9.0


    def test_history_not_found():
        r = client.get("/metrics/nonexistent/history")
        assert r.status_code == 404
        assert "nonexistent" in r.json()["detail"]


    def test_history_caps_at_20():
        for i in range(30):
            client.post("/metrics", json={"name": "cpu", "value": float(i)})
        r = client.get("/metrics/cpu/history")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 20
        assert data[0]["value"] == 10.0  # oldest kept (30 - 20 = 10)
        assert data[-1]["value"] == 29.0  # newest


    def test_history_cleared_by_delete():
        client.post("/metrics", json={"name": "cpu", "value": 10.0})
        client.delete("/metrics/cpu")
        r = client.get("/metrics/cpu/history")
        assert r.status_code == 404


    def test_history_default_limit_is_20():
        for i in range(25):
            client.post("/metrics", json={"name": "cpu", "value": float(i)})
        r = client.get("/metrics/cpu/history")
        data = r.json()
        assert len(data) == 20


    def test_history_does_not_mix_metric_names():
        client.post("/metrics", json={"name": "cpu", "value": 1.0})
        client.post("/metrics", json={"name": "mem", "value": 2.0})
        client.post("/metrics", json={"name": "cpu", "value": 3.0})
        r = client.get("/metrics/cpu/history")
        data = r.json()
        assert len(data) == 2
        assert all(d["name"] == "cpu" for d in data)
    ```

    2. Ensure all tests use the existing `client` and `clear_store` fixture (autouse, already defined).
    3. Do NOT modify any existing tests.

    ## Files to modify
    - `backend/tests/test_api.py` — append 7 new test functions

    ## Code patterns to follow
    - Follow the existing test pattern: `client.post()` to create data, `client.get()` to fetch, assert status and body.
    - Use the same fixture pattern (`store.clear()` via autouse fixture).
    - No mocking — tests hit real routes via TestClient.

    ## Acceptance criteria
    - 7 new test functions exist in `test_api.py`
    - All 7 new tests pass
    - All existing tests still pass (no regressions)
    - Tests cover: basic history, limit param, 404, deque cap, delete clears history, default limit, name isolation

    ## Validation command
    ```bash
    cd backend && pytest tests/test_api.py -v
    ```

### 6. Final Validation
- **Task ID**: validate-all
- **Role**: validator
- **Depends On**: add-history-deque, add-history-method, add-history-route, add-frontend-api, add-history-tests
- **Assigned To**: validator
- **Description**: |
    Run all validation commands and verify all acceptance criteria.

    ## Validation Commands
    1. `cd backend && ruff check .` — Python lint passes
    2. `cd backend && pytest tests/test_api.py -v` — all tests pass (existing + 7 new)
    3. `cd frontend && npm run typecheck` — TypeScript compiles
    4. `cd frontend && npm run lint` — no lint errors

    ## Acceptance Criteria
    - `MetricStore._history` exists as `dict[str, deque[MetricOut]]`
    - `POST /metrics` appends to both `_data` and `_history`
    - `GET /metrics/{name}/history` returns 200 with list of metrics
    - `GET /metrics/{name}/history?limit=3` returns at most 3 entries
    - `GET /metrics/nonexistent/history` returns 404
    - `DELETE /metrics/{name}` clears history for that name
    - History is capped at 20 entries per name
    - All existing tests pass (no regressions)
    - 7 new history tests pass
    - `fetchMetricHistory` exported from `frontend/src/api.ts`
    - Python lint clean, TypeScript types clean, frontend lint clean

## Acceptance Criteria

- `POST /metrics` still returns 201 and works exactly as before
- `GET /metrics/{name}/history` returns 200 with a JSON array of MetricOut objects
- `GET /metrics/{name}/history?limit=N` returns at most N entries (N clamped 1–20)
- `GET /metrics/nonexistent/history` returns 404 with detail message
- `DELETE /metrics/{name}` also clears history for that name
- History is capped at 20 entries per metric name (oldest evicted)
- All existing tests pass unchanged
- 7 new tests cover: basic history, limit, 404, deque cap, delete clears, default limit, name isolation
- `fetchMetricHistory()` exists in `frontend/src/api.ts` and typechecks
- `ruff check .` passes, `npm run typecheck` passes, `npm run lint` passes

## Validation Commands

Execute these commands to validate the task is complete:

- `cd backend && ruff check .` — Python lint
- `cd backend && pytest tests/test_api.py -v` — all backend tests
- `cd frontend && npm run typecheck` — TypeScript compilation
- `cd frontend && npm run lint` — frontend lint

## Notes

- **Brainstorming result**: Option (b) chosen — separate `_history` dict with `deque(maxlen=20)`. Rationale: zero risk to existing `_data` list, O(1) append with automatic eviction, clean separation.
- **No new dependencies**: `collections.deque` is stdlib. No pip/npm installs needed.
- **Route ordering matters**: `/metrics/{name}/history` must be defined before `/metrics/{name}` in `main.py` to avoid FastAPI matching `{name}="history"`.
- **Frontend**: Only the API client function is added. No UI component for history display — that would be a separate plan.
