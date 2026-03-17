# Plan: Time-Range Querying for Metrics Dashboard

> **Status:** COMPLETE (2026-03-16)
> All 11 tasks completed. 72/72 backend tests passing, 51/51 frontend tests passing. Validated by agent team with build evidence.

## Build Evidence

> **Status:** COMPLETE
> **Date:** 2026-03-16
> **Team:** time-range-querying-20260316-0115

### Test Results
- backend/tests/test_api.py — 72/72 PASSED (13 new time-range tests + 59 existing)
- frontend/src/api.test.ts — 14/14 PASSED
- frontend/src/components/TimeRangeBar.test.tsx — 5/5 PASSED (all new)
- frontend/src/components/SparklineChart.test.tsx — 4/4 PASSED
- frontend/src/components/MetricCard.test.tsx — 9/9 PASSED
- frontend/src/App.test.tsx — 19/19 PASSED

### Validation Commands
- `cd backend && ruff check .` — PASS (All checks passed!)
- `cd backend && pytest tests/test_api.py -v` — PASS (72 passed in 2.96s)
- `cd frontend && npx tsc --noEmit` — PASS (no errors)
- `cd frontend && npm run lint` — PASS (eslint 0 warnings)
- `cd frontend && npx vitest run` — PASS (5 files, 51 tests passed in 1.77s)

### Acceptance Criteria Verification
- [x] GET /metrics?start=...&end=... filters by time range — VERIFIED (main.py:86-87 adds start/end Query params; test_list_metrics_with_start_filter, test_list_metrics_with_end_filter, test_list_metrics_with_start_and_end_filter all pass)
- [x] GET /metrics/{name}/history?start=...&end=... filters history — VERIFIED (main.py:111-112 adds start/end Query params; test_history_with_start_filter, test_history_with_end_filter, test_history_with_start_and_limit all pass)
- [x] GET /metrics/export?start=...&end=... filters CSV export — VERIFIED (main.py:156-157 adds start/end Query params; test_export_with_time_range passes)
- [x] GET /metrics?start=invalid returns 400 — VERIFIED (test_list_metrics_invalid_start_format and test_list_metrics_invalid_end_format both assert status_code == 400)
- [x] All endpoints backward compatible without params — VERIFIED (test_list_metrics_no_time_params_backward_compat and test_history_no_time_params_backward_compat pass; all 59 pre-existing tests unchanged and passing)
- [x] Tag+time combine with AND logic — VERIFIED (test_list_metrics_time_and_tag_combined passes)
- [x] TimeRangeBar renders with datetime-local inputs and Clear button — VERIFIED (TimeRangeBar.tsx has 2 datetime-local inputs and Clear button; TimeRangeBar.test.tsx 5/5 pass)
- [x] Time range triggers immediate re-fetch — VERIFIED (App.tsx useEffect depends on timeRange state; changing timeRange triggers loadMetrics)
- [x] CSV export link includes time params when active — VERIFIED (App.tsx:84-85 appends start/end to export URL when timeRange is set)
- [x] All existing tests pass, 13 new backend + 5 new frontend tests pass — VERIFIED (72 backend total with 13 new time-range tests; 5 new TimeRangeBar tests; all passing)

### Files Changed
| File | Action | Verified |
|------|--------|----------|
| backend/store.py | Modified | Yes |
| backend/main.py | Modified | Yes |
| backend/tests/test_api.py | Modified | Yes |
| frontend/src/api.ts | Modified | Yes |
| frontend/src/api.test.ts | Modified | Yes |
| frontend/src/components/TimeRangeBar.tsx | Created | Yes |
| frontend/src/components/TimeRangeBar.test.tsx | Created | Yes |
| frontend/src/components/MetricCard.tsx | Modified | Yes |
| frontend/src/App.tsx | Modified | Yes |
| docs/design/metrics.md | Modified | Yes |

> **EXECUTION DIRECTIVE**: This is a team-orchestrated plan.
> **FORBIDDEN**: Direct implementation (Edit, Write, NotebookEdit) by the main agent. If you are the main conversation agent and a user asks you to implement this plan, you MUST invoke `/build_v2 specs/time-range-querying.md` -- do NOT implement it yourself.
> **REQUIRED**: Execute ONLY via the `/build_v2` command, which deploys team agents to do the work.

## Task Description

Add time-range querying to the metrics dashboard so users can filter metrics and history by start/end datetime. Currently the `GET /metrics` endpoint returns only latest-per-name values, and `GET /metrics/{name}/history` returns a fixed-count window (last N entries, max 20) with no way to scope by time. This plan adds optional `start` and `end` ISO-8601 query parameters to both the metrics list and history endpoints, a new `TimeRangeBar` UI component for selecting the time window, and wires the time range into polling, CSV export, and sparkline history fetching.

## Objective

When this plan is complete:
- `GET /metrics?start=...&end=...` filters the latest-per-name metrics by timestamp window
- `GET /metrics/{name}/history?start=...&end=...` filters history entries by timestamp window (can be combined with `limit`)
- `GET /metrics/export?start=...&end=...` respects time-range filters for CSV export
- The frontend has a `TimeRangeBar` component with start/end datetime-local inputs
- Active time range is passed through polling, sparkline fetching, and CSV export links
- All existing tests pass unchanged; new tests cover time-range filtering

## Problem Statement

Users can only view the latest metric values or the last N history entries. There is no mechanism to ask "show me all cpu metrics between 2pm and 3pm yesterday." This limits the dashboard's usefulness for debugging time-specific incidents. The `store.history()` method uses a deque capped at 20 entries — users cannot even get older data within that window by time. The metrics list endpoint (`GET /metrics`) returns only the single latest value per name, with no time awareness at all.

## Solution Approach

### Backend Changes

1. **Store layer** (`store.py`): Add two new methods:
   - `filter_by_time(start, end, tags)` — scans `_data` (latest-per-name values) and filters by timestamp range. This extends the existing `filter_by_tags` pattern but adds time bounds.
   - Update `history(name, limit, start, end)` — add optional `start`/`end` parameters that filter the deque entries by timestamp before applying the limit.

2. **API layer** (`main.py`): Add optional `start` and `end` query parameters (ISO-8601 strings parsed to `datetime`) to:
   - `GET /metrics` — filter latest-per-name metrics by time window
   - `GET /metrics/{name}/history` — filter history entries by time window
   - `GET /metrics/export` — filter exported metrics by time window

3. **Models** (`models.py`): No new models needed. The existing `MetricOut` already has a `timestamp: datetime` field. Query parameters are parsed inline via FastAPI's `Query`.

### Frontend Changes

4. **API client** (`api.ts`): Update `fetchMetrics()` and `fetchMetricHistory()` to accept optional `start`/`end` ISO string parameters and append them as query params.

5. **TimeRangeBar component**: New component with two `<input type="datetime-local">` fields and a "Clear" button. Lifted state pattern matching `TagFilterBar`.

6. **App.tsx**: Add `timeRange` state (`{start?: string, end?: string}`), wire it into `loadMetrics()`, the CSV export link, and pass it down so `MetricCard` can forward it to `fetchMetricHistory()`.

### Design Decisions

- **ISO-8601 strings for query params** — human-readable, natively supported by Python `datetime.fromisoformat()` and JavaScript `Date`. No unix timestamps.
- **Both start and end are optional** — omitting `start` means "from the beginning"; omitting `end` means "until now". This preserves full backward compatibility.
- **Time filtering happens in the store layer** — keeps endpoint handlers thin, consistent with the existing `filter_by_tags` pattern (see DD-003 in design doc).
- **History deque cap of 20 remains** — time-range filtering applies within the existing 20-entry deque. This plan does NOT increase storage. A future plan could add persistent storage.

## Relevant Files

- `backend/store.py` — Add time-range filtering to `filter_by_tags()` and `history()` methods. Core storage logic.
- `backend/main.py` — Add `start`/`end` query parameters to `GET /metrics`, `GET /metrics/{name}/history`, and `GET /metrics/export`.
- `backend/models.py` — No changes needed (MetricOut already has `timestamp: datetime`).
- `backend/tests/test_api.py` — Add tests for time-range filtering on all three endpoints.
- `frontend/src/api.ts` — Update `fetchMetrics()` and `fetchMetricHistory()` to accept and pass `start`/`end` params.
- `frontend/src/App.tsx` — Add `timeRange` state, wire into polling, CSV export link, and pass to MetricCard.
- `frontend/src/components/MetricCard.tsx` — Accept optional `timeRange` prop and forward to `fetchMetricHistory()`.
- `docs/design/metrics.md` — Update with new design decisions.

### New Files

- `frontend/src/components/TimeRangeBar.tsx` — New component for datetime range selection.
- `frontend/src/components/TimeRangeBar.test.tsx` — Unit tests for the TimeRangeBar component.

## Implementation Phases

### Phase 1: Foundation
Backend store methods — add time-range filtering capabilities to `MetricStore` without changing any API endpoints. All existing tests must continue to pass since the new parameters are optional.

### Phase 2: Core Implementation
Wire time-range parameters into the three API endpoints (`GET /metrics`, `GET /metrics/{name}/history`, `GET /metrics/export`). Build the frontend `TimeRangeBar` component and update the API client functions.

### Phase 3: Integration & Polish
Integrate time range into App.tsx state management, connect it to polling/export/sparklines. Write comprehensive backend and frontend tests. Update design docs.

## Team Orchestration

- The `/build_v2` command deploys a **self-organizing agent team**. Agents autonomously discover, claim, and execute tasks from a shared task list.
- You are responsible for designing the team composition and task graph so agents can work autonomously.
- IMPORTANT: The plan is the **single source of truth**. `/build_v2` is a pure executor — it does NOT make decisions. Everything must be specified here: team members, task assignments, dependencies, and exhaustive task descriptions.
- **`Assigned To` is enforced**: `/build_v2` injects each agent's name into their standing orders. Agents only claim tasks where `Assigned To` matches their own name. Every task MUST have an `Assigned To`.
- Agents cannot ask for clarification mid-task. Every task description must be fully self-contained with all context needed for autonomous execution.

### Team Members

- Builder
  - Name: builder-1
  - Role: Backend implementation — store methods, API endpoints, backend tests
  - Agent Type: general-purpose
- Builder
  - Name: builder-2
  - Role: Frontend implementation — API client, TimeRangeBar component, App.tsx integration
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

### 1. Add Time-Range Filtering to MetricStore
- **Task ID**: store-time-range
- **Role**: builder
- **Depends On**: none
- **Assigned To**: builder-1
- **Description**: |
    Add time-range filtering capabilities to `MetricStore` in `backend/store.py`. This is the
    foundational data layer change that all API endpoint tasks depend on.

    ## What to do

    1. Add `from datetime import datetime` to imports in `backend/store.py` (it is already imported as `from datetime import UTC, datetime` — confirm this import exists).

    2. Modify `filter_by_tags()` to accept optional time-range parameters. Change the signature and body:

    ```python
    def filter_by_tags(
        self,
        tags: list[tuple[str, str]],
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[MetricOut]:
        metrics = list(self._data.values())
        if tags:
            metrics = [
                m for m in metrics
                if all(m.tags.get(k) == v for k, v in tags)
            ]
        if start is not None:
            metrics = [m for m in metrics if m.timestamp >= start]
        if end is not None:
            metrics = [m for m in metrics if m.timestamp <= end]
        return metrics
    ```

    IMPORTANT: The existing behavior when `tags` is empty and `start`/`end` are None must be preserved exactly — it returns all metrics. The current code returns `list(self._data.values())` when `not tags`. The new code must do the same when tags is empty AND start/end are both None.

    3. Modify `history()` to accept optional time-range parameters:

    ```python
    def history(
        self,
        name: str,
        limit: int = 20,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[MetricOut]:
        entries = self._history.get(name)
        if entries is None:
            return []
        result = list(entries)
        if start is not None:
            result = [m for m in result if m.timestamp >= start]
        if end is not None:
            result = [m for m in result if m.timestamp <= end]
        limit = max(1, min(limit, len(result) if result else 20))
        return result[-limit:]
    ```

    IMPORTANT for the limit clamping: When time-range is applied, the result set may be smaller than 20. The limit should be clamped to `max(1, min(limit, len(result)))` so we don't over-slice. When no time range is applied, the existing behavior (clamp to 20) is preserved because `len(result)` will be at most 20 (deque maxlen).

    ## Files to modify
    - `backend/store.py` — modify `filter_by_tags()` and `history()` method signatures and bodies

    ## Code patterns to follow
    - The existing `filter_by_tags` method (`store.py:30-36`) uses list comprehension filtering. Follow the same pattern for time filtering.
    - The existing `history` method (`store.py:42-47`) converts deque to list and slices. Add filtering before slicing.
    - All parameters are optional with `None` defaults — preserving backward compatibility.
    - Type hint uses `datetime | None` (Python 3.11+ syntax, matching the project's `target-version = "py311"` in `pyproject.toml`).

    ## Acceptance criteria
    - `filter_by_tags([], None, None)` returns all metrics (backward compatible)
    - `filter_by_tags([], start=some_time)` returns only metrics with `timestamp >= some_time`
    - `filter_by_tags([], end=some_time)` returns only metrics with `timestamp <= some_time`
    - `filter_by_tags([], start=t1, end=t2)` returns metrics in the `[t1, t2]` range (inclusive)
    - `filter_by_tags(tags, start=t1, end=t2)` combines tag AND time filtering
    - `history("cpu")` still returns all history entries (backward compatible)
    - `history("cpu", start=t1, end=t2)` returns only entries within the time range
    - `history("cpu", limit=3, start=t1)` applies time filter first, then limit
    - All existing tests pass unchanged

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && python -c "
    from datetime import UTC, datetime, timedelta
    from store import MetricStore
    from models import MetricIn
    import time

    s = MetricStore()
    # Add metrics at different times
    s.add(MetricIn(name='cpu', value=1.0))
    time.sleep(0.05)
    t_mid = datetime.now(UTC)
    time.sleep(0.05)
    s.add(MetricIn(name='cpu', value=2.0))
    s.add(MetricIn(name='mem', value=50.0))

    # filter_by_tags backward compat
    assert len(s.filter_by_tags([])) == 2, 'Should return 2 latest-per-name'
    assert len(s.filter_by_tags([], None, None)) == 2

    # filter_by_tags with start
    recent = s.filter_by_tags([], start=t_mid)
    assert len(recent) == 2, f'Expected 2 recent metrics, got {len(recent)}'

    # history backward compat
    h = s.history('cpu')
    assert len(h) == 2, f'Expected 2 history entries, got {len(h)}'

    # history with start
    h_recent = s.history('cpu', start=t_mid)
    assert len(h_recent) == 1, f'Expected 1 recent history entry, got {len(h_recent)}'
    assert h_recent[0].value == 2.0

    print('ALL STORE CHECKS PASSED')
    " && pytest tests/ -v --tb=short
    ```

### 2. Add Time-Range Parameters to API Endpoints
- **Task ID**: api-time-range
- **Role**: builder
- **Depends On**: store-time-range
- **Assigned To**: builder-1
- **Description**: |
    Add optional `start` and `end` query parameters to the three relevant API endpoints in
    `backend/main.py`. These parameters accept ISO-8601 datetime strings and are parsed to
    `datetime` objects before being passed to the store layer.

    ## What to do

    1. Add `from datetime import datetime` to the imports in `backend/main.py` (check if already present — it is NOT currently imported there).

    2. Create a helper function at module level (after the `store` and `alert_store` declarations, before the routes) to parse ISO datetime strings:

    ```python
    def _parse_dt(value: str | None) -> datetime | None:
        if value is None:
            return None
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                from datetime import UTC
                dt = dt.replace(tzinfo=UTC)
            return dt
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid datetime format '{value}'. Use ISO-8601 (e.g., '2026-03-15T14:00:00').",
            )
    ```

    This helper:
    - Returns None for None input (parameter not provided)
    - Parses ISO-8601 strings via `datetime.fromisoformat()`
    - Adds UTC timezone if the input is naive (all stored timestamps are UTC)
    - Returns 400 with a descriptive error for unparseable strings

    3. Update `GET /metrics` endpoint (`list_metrics` function, currently at line ~63-74):

    ```python
    @app.get("/metrics", response_model=list[MetricOut])
    def list_metrics(
        tag: list[str] = Query(default=[]),
        start: str | None = Query(default=None),
        end: str | None = Query(default=None),
    ) -> list[MetricOut]:
        parsed_tags: list[tuple[str, str]] = []
        for t in tag:
            if ":" not in t:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid tag format '{t}'. Expected 'key:value'.",
                )
            key, value = t.split(":", 1)
            parsed_tags.append((key, value))
        return store.filter_by_tags(parsed_tags, _parse_dt(start), _parse_dt(end))
    ```

    The only change is adding `start` and `end` parameters and passing parsed values to `filter_by_tags`.

    4. Update `GET /metrics/{name}/history` endpoint (`get_metric_history`, currently at line ~123-128):

    ```python
    @app.get("/metrics/{name}/history", response_model=list[MetricOut])
    def get_metric_history(
        name: str,
        limit: int = 20,
        start: str | None = Query(default=None),
        end: str | None = Query(default=None),
    ) -> list[MetricOut]:
        results = store.history(name, limit, _parse_dt(start), _parse_dt(end))
        if not results:
            raise HTTPException(status_code=404, detail=f"No history found for '{name}'")
        return results
    ```

    5. Update `GET /metrics/export` endpoint (`export_metrics`, currently at line ~83-120):

    Add `start` and `end` parameters to the function signature:

    ```python
    @app.get("/metrics/export")
    def export_metrics(
        format: str = "csv",
        tag: list[str] = Query(default=[]),
        start: str | None = Query(default=None),
        end: str | None = Query(default=None),
    ) -> StreamingResponse:
    ```

    And update the `store.filter_by_tags` call at the end of that function (currently line ~100):

    ```python
        metrics = store.filter_by_tags(parsed_tags, _parse_dt(start), _parse_dt(end))
    ```

    ## Files to modify
    - `backend/main.py` — add `_parse_dt` helper, add `start`/`end` params to 3 endpoints

    ## Code patterns to follow
    - Existing endpoints use `Query(default=...)` for query parameters (see `tag: list[str] = Query(default=[])` at line 64).
    - Use `str | None = Query(default=None)` for optional string query params — this is the FastAPI convention.
    - Error handling follows the existing pattern: `HTTPException(status_code=400, detail=...)` (see tag validation at lines 68-71).
    - Keep the `_parse_dt` helper as a private module-level function (underscore prefix matches Python convention for internal helpers).

    ## Acceptance criteria
    - `GET /metrics` still works without start/end params (backward compatible)
    - `GET /metrics?start=2026-03-15T14:00:00` returns only metrics at or after that time
    - `GET /metrics?end=2026-03-15T15:00:00` returns only metrics at or before that time
    - `GET /metrics?start=2026-03-15T14:00:00&end=2026-03-15T15:00:00` returns metrics in range
    - `GET /metrics?start=not-a-date` returns 400 with descriptive error
    - `GET /metrics/{name}/history?start=...&end=...` filters history by time
    - `GET /metrics/export?start=...&end=...` filters exported CSV by time
    - Tag filtering and time filtering combine correctly (AND logic)
    - All existing tests pass unchanged

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && python -c "
    from fastapi.testclient import TestClient
    from main import app, store
    import time
    from datetime import UTC, datetime

    store.clear()
    c = TestClient(app)

    # Submit metrics
    c.post('/metrics', json={'name': 'cpu', 'value': 10.0})
    time.sleep(0.05)
    t_mid = datetime.now(UTC).isoformat()
    time.sleep(0.05)
    c.post('/metrics', json={'name': 'cpu', 'value': 20.0})
    c.post('/metrics', json={'name': 'mem', 'value': 50.0})

    # Backward compat
    r = c.get('/metrics')
    assert r.status_code == 200
    assert len(r.json()) == 2, f'Expected 2, got {len(r.json())}'

    # With start param
    r = c.get(f'/metrics?start={t_mid}')
    assert r.status_code == 200
    vals = [m['value'] for m in r.json()]
    assert 20.0 in vals, f'Expected 20.0 in {vals}'
    assert 50.0 in vals, f'Expected 50.0 in {vals}'

    # History with start
    r = c.get(f'/metrics/cpu/history?start={t_mid}')
    assert r.status_code == 200
    assert len(r.json()) == 1, f'Expected 1, got {len(r.json())}'
    assert r.json()[0]['value'] == 20.0

    # Invalid datetime
    r = c.get('/metrics?start=not-a-date')
    assert r.status_code == 400

    # Export with start
    r = c.get(f'/metrics/export?format=csv&start={t_mid}')
    assert r.status_code == 200

    store.clear()
    print('ALL API CHECKS PASSED')
    " && pytest tests/ -v --tb=short
    ```

### 3. Add Backend Tests for Time-Range Filtering
- **Task ID**: backend-time-tests
- **Role**: builder
- **Depends On**: api-time-range
- **Assigned To**: builder-1
- **Description**: |
    Add comprehensive tests for time-range filtering in `backend/tests/test_api.py`. These tests
    cover all three endpoints, edge cases, and interaction with existing tag filters.

    ## What to do

    1. Add `import time` and `from datetime import UTC, datetime` to the imports at the top of
       `backend/tests/test_api.py` if not already present.

    2. Append the following test functions at the END of `backend/tests/test_api.py` (after all
       existing tests). Do NOT modify any existing tests.

    ```python
    # --- Time-Range Filtering Tests ---

    def test_list_metrics_with_start_filter():
        """GET /metrics?start=... returns only metrics at or after start time."""
        client.post("/metrics", json={"name": "cpu", "value": 10.0})
        time.sleep(0.05)
        t_mid = datetime.now(UTC).isoformat()
        time.sleep(0.05)
        client.post("/metrics", json={"name": "cpu", "value": 20.0})
        client.post("/metrics", json={"name": "mem", "value": 50.0})
        r = client.get(f"/metrics?start={t_mid}")
        assert r.status_code == 200
        data = r.json()
        # cpu was updated after t_mid (value=20), mem was added after t_mid
        values = {m["name"]: m["value"] for m in data}
        assert values.get("cpu") == 20.0
        assert values.get("mem") == 50.0


    def test_list_metrics_with_end_filter():
        """GET /metrics?end=... returns only metrics at or before end time."""
        client.post("/metrics", json={"name": "cpu", "value": 10.0})
        t_mid = datetime.now(UTC).isoformat()
        time.sleep(0.05)
        client.post("/metrics", json={"name": "mem", "value": 50.0})
        r = client.get(f"/metrics?end={t_mid}")
        assert r.status_code == 200
        data = r.json()
        names = [m["name"] for m in data]
        assert "cpu" in names
        # mem was added after t_mid, but _data stores latest-per-name so
        # the cpu entry timestamp is before t_mid
        assert len(data) >= 1


    def test_list_metrics_with_start_and_end_filter():
        """GET /metrics?start=...&end=... returns metrics in time window."""
        client.post("/metrics", json={"name": "early", "value": 1.0})
        time.sleep(0.05)
        t_start = datetime.now(UTC).isoformat()
        time.sleep(0.05)
        client.post("/metrics", json={"name": "middle", "value": 2.0})
        time.sleep(0.05)
        t_end = datetime.now(UTC).isoformat()
        time.sleep(0.05)
        client.post("/metrics", json={"name": "late", "value": 3.0})
        r = client.get(f"/metrics?start={t_start}&end={t_end}")
        assert r.status_code == 200
        names = [m["name"] for m in r.json()]
        assert "middle" in names
        assert "early" not in names
        assert "late" not in names


    def test_list_metrics_time_and_tag_combined():
        """Time-range and tag filters combine with AND logic."""
        client.post("/metrics", json={"name": "cpu", "value": 10.0, "tags": {"env": "prod"}})
        time.sleep(0.05)
        t_mid = datetime.now(UTC).isoformat()
        time.sleep(0.05)
        client.post("/metrics", json={"name": "cpu", "value": 20.0, "tags": {"env": "prod"}})
        client.post("/metrics", json={"name": "mem", "value": 50.0, "tags": {"env": "staging"}})
        # Filter by time AND tag
        r = client.get(f"/metrics?start={t_mid}&tag=env:prod")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["name"] == "cpu"
        assert data[0]["value"] == 20.0


    def test_list_metrics_invalid_start_format():
        """Invalid start datetime returns 400."""
        r = client.get("/metrics?start=not-a-datetime")
        assert r.status_code == 400
        assert "Invalid datetime" in r.json()["detail"]


    def test_list_metrics_invalid_end_format():
        """Invalid end datetime returns 400."""
        r = client.get("/metrics?end=xyz")
        assert r.status_code == 400
        assert "Invalid datetime" in r.json()["detail"]


    def test_list_metrics_no_time_params_backward_compat():
        """Without start/end params, behavior is unchanged."""
        client.post("/metrics", json={"name": "cpu", "value": 10.0})
        client.post("/metrics", json={"name": "mem", "value": 20.0})
        r = client.get("/metrics")
        assert r.status_code == 200
        assert len(r.json()) == 2


    def test_history_with_start_filter():
        """GET /metrics/{name}/history?start=... filters history entries."""
        client.post("/metrics", json={"name": "cpu", "value": 1.0})
        time.sleep(0.05)
        t_mid = datetime.now(UTC).isoformat()
        time.sleep(0.05)
        client.post("/metrics", json={"name": "cpu", "value": 2.0})
        client.post("/metrics", json={"name": "cpu", "value": 3.0})
        r = client.get(f"/metrics/cpu/history?start={t_mid}")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert data[0]["value"] == 2.0
        assert data[1]["value"] == 3.0


    def test_history_with_end_filter():
        """GET /metrics/{name}/history?end=... filters history entries."""
        client.post("/metrics", json={"name": "cpu", "value": 1.0})
        client.post("/metrics", json={"name": "cpu", "value": 2.0})
        t_mid = datetime.now(UTC).isoformat()
        time.sleep(0.05)
        client.post("/metrics", json={"name": "cpu", "value": 3.0})
        r = client.get(f"/metrics/cpu/history?end={t_mid}")
        assert r.status_code == 200
        data = r.json()
        values = [d["value"] for d in data]
        assert 1.0 in values
        assert 2.0 in values
        assert 3.0 not in values


    def test_history_with_start_and_limit():
        """Time filter is applied before limit."""
        for i in range(5):
            client.post("/metrics", json={"name": "cpu", "value": float(i)})
        time.sleep(0.05)
        t_mid = datetime.now(UTC).isoformat()
        time.sleep(0.05)
        for i in range(5, 10):
            client.post("/metrics", json={"name": "cpu", "value": float(i)})
        r = client.get(f"/metrics/cpu/history?start={t_mid}&limit=2")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        # Should be the last 2 of the 5 entries after t_mid
        assert data[-1]["value"] == 9.0


    def test_history_no_time_params_backward_compat():
        """Without start/end params, history behavior is unchanged."""
        for i in range(5):
            client.post("/metrics", json={"name": "cpu", "value": float(i)})
        r = client.get("/metrics/cpu/history")
        assert r.status_code == 200
        assert len(r.json()) == 5


    def test_export_with_time_range():
        """GET /metrics/export?start=...&end=... filters CSV export."""
        client.post("/metrics", json={"name": "early", "value": 1.0})
        time.sleep(0.05)
        t_start = datetime.now(UTC).isoformat()
        time.sleep(0.05)
        client.post("/metrics", json={"name": "middle", "value": 2.0})
        time.sleep(0.05)
        t_end = datetime.now(UTC).isoformat()
        time.sleep(0.05)
        client.post("/metrics", json={"name": "late", "value": 3.0})
        r = client.get(f"/metrics/export?format=csv&start={t_start}&end={t_end}")
        assert r.status_code == 200
        content = r.text
        assert "middle" in content
        assert "early" not in content
        assert "late" not in content
    ```

    3. Ensure all tests use the existing `client` and `clear_store` fixture (autouse fixture already
       defined at the top of the file). Do NOT modify any existing tests or fixtures.

    ## Files to modify
    - `backend/tests/test_api.py` — add `import time` and `from datetime import UTC, datetime` to imports (if not present), append 13 new test functions

    ## Code patterns to follow
    - Follow the existing test pattern: `client.post()` to create data, `client.get()` to query, assert status and body.
    - Use `time.sleep(0.05)` between metric submissions to ensure distinct timestamps (existing tests in this file don't need this because they don't filter by time, but time-range tests do).
    - Use the existing `client` (TestClient) and `clear_store` fixture (autouse).
    - No mocking — tests hit real routes via TestClient.

    ## Acceptance criteria
    - 13 new test functions exist at the end of `test_api.py`
    - All 13 new tests pass
    - All existing tests still pass (no regressions)
    - Tests cover: start filter, end filter, start+end filter, tag+time combined, invalid datetime (400), backward compat (no params), history start, history end, history start+limit, history backward compat, export with time range

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && pytest tests/test_api.py -v --tb=short
    ```

### 4. Update Frontend API Client for Time Range
- **Task ID**: frontend-api-time-range
- **Role**: builder
- **Depends On**: none
- **Assigned To**: builder-2
- **Description**: |
    Update the frontend API client functions in `frontend/src/api.ts` to accept optional
    `start` and `end` ISO-8601 string parameters.

    ## What to do

    1. Update `fetchMetrics()` in `frontend/src/api.ts` (currently at lines 35-47) to accept
       an optional time range:

    ```typescript
    export async function fetchMetrics(
      tags?: string[],
      start?: string,
      end?: string,
    ): Promise<Metric[]> {
      let url = `${BASE}/metrics`
      const params = new URLSearchParams()
      if (tags && tags.length > 0) {
        for (const t of tags) {
          params.append('tag', t)
        }
      }
      if (start) {
        params.append('start', start)
      }
      if (end) {
        params.append('end', end)
      }
      const qs = params.toString()
      if (qs) {
        url += `?${qs}`
      }
      const res = await fetch(url)
      if (!res.ok) throw new Error(`Failed to fetch metrics: ${res.status}`)
      return res.json()
    }
    ```

    Key changes:
    - Added `start?: string` and `end?: string` parameters
    - Refactored to always use `URLSearchParams` (cleaner than conditional string building)
    - Only appends query string if there are actual params

    2. Update `fetchMetricHistory()` (currently at lines 71-78) to accept optional time range:

    ```typescript
    export async function fetchMetricHistory(
      name: string,
      limit: number = 20,
      start?: string,
      end?: string,
    ): Promise<Metric[]> {
      const params = new URLSearchParams()
      params.append('limit', String(limit))
      if (start) {
        params.append('start', start)
      }
      if (end) {
        params.append('end', end)
      }
      const res = await fetch(`${BASE}/metrics/${name}/history?${params.toString()}`)
      if (!res.ok) throw new Error(`Failed to fetch metric history: ${res.status}`)
      return res.json()
    }
    ```

    Key changes:
    - Added `start?: string` and `end?: string` parameters
    - Uses `URLSearchParams` for cleaner param building

    ## Files to modify
    - `frontend/src/api.ts` — update `fetchMetrics()` and `fetchMetricHistory()` function signatures and bodies

    ## Code patterns to follow
    - The existing `fetchMetrics()` already uses `URLSearchParams` for tag params (lines 38-41). Extend the same pattern.
    - All API functions follow the pattern: construct URL, `await fetch(url)`, check `!res.ok`, return `res.json()`.
    - Optional params use TypeScript's `?` syntax.
    - The `start` and `end` values are ISO-8601 strings — no conversion needed on the frontend side.

    ## Acceptance criteria
    - `fetchMetrics()` accepts optional `start` and `end` string params
    - `fetchMetrics(undefined, undefined, undefined)` produces URL `/api/metrics` (no query string) — backward compatible
    - `fetchMetrics(["env:prod"], "2026-03-15T14:00:00")` produces URL with both `tag=env:prod` and `start=2026-03-15T14:00:00`
    - `fetchMetricHistory("cpu", 20, "2026-03-15T14:00:00")` produces URL with `limit=20&start=2026-03-15T14:00:00`
    - TypeScript compiles without errors
    - No changes to any other functions or interfaces

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx tsc --noEmit && echo "TYPECHECK PASSED"
    ```

### 5. Create TimeRangeBar Component
- **Task ID**: time-range-bar
- **Role**: builder
- **Depends On**: none
- **Assigned To**: builder-2
- **Description**: |
    Create a new `TimeRangeBar` React component in `frontend/src/components/TimeRangeBar.tsx`
    that provides start/end datetime inputs for time-range filtering. Follow the same controlled
    component pattern as `TagFilterBar`.

    ## What to do

    1. Create `frontend/src/components/TimeRangeBar.tsx` with the following content:

    ```tsx
    interface TimeRange {
      start: string
      end: string
    }

    interface Props {
      timeRange: TimeRange
      onTimeRangeChange: (range: TimeRange) => void
    }

    export function TimeRangeBar({ timeRange, onTimeRangeChange }: Props) {
      const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onTimeRangeChange({ ...timeRange, start: e.target.value })
      }

      const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onTimeRangeChange({ ...timeRange, end: e.target.value })
      }

      const handleClear = () => {
        onTimeRangeChange({ start: '', end: '' })
      }

      const hasRange = timeRange.start !== '' || timeRange.end !== ''

      return (
        <div className="time-range-bar">
          <label>
            From:{' '}
            <input
              type="datetime-local"
              value={timeRange.start}
              onChange={handleStartChange}
              data-testid="time-range-start"
            />
          </label>
          <label>
            To:{' '}
            <input
              type="datetime-local"
              value={timeRange.end}
              onChange={handleEndChange}
              data-testid="time-range-end"
            />
          </label>
          {hasRange && (
            <button
              onClick={handleClear}
              className="time-range-clear"
              data-testid="time-range-clear"
            >
              Clear
            </button>
          )}
        </div>
      )
    }

    export type { TimeRange }
    ```

    Key design decisions:
    - `TimeRange` type uses empty strings for "not set" (matches HTML input value semantics)
    - `datetime-local` input type provides native browser date/time picker
    - Controlled component: parent owns state, component calls `onTimeRangeChange` on input change
    - Clear button only shows when at least one field has a value
    - `data-testid` attributes for testing

    2. Create `frontend/src/components/TimeRangeBar.test.tsx` with basic tests:

    ```tsx
    import { render, screen, fireEvent } from '@testing-library/react'
    import { TimeRangeBar } from './TimeRangeBar'

    describe('TimeRangeBar', () => {
      it('renders start and end inputs', () => {
        const onChange = vi.fn()
        render(
          <TimeRangeBar
            timeRange={{ start: '', end: '' }}
            onTimeRangeChange={onChange}
          />,
        )
        expect(screen.getByTestId('time-range-start')).toBeInTheDocument()
        expect(screen.getByTestId('time-range-end')).toBeInTheDocument()
      })

      it('does not show clear button when range is empty', () => {
        const onChange = vi.fn()
        render(
          <TimeRangeBar
            timeRange={{ start: '', end: '' }}
            onTimeRangeChange={onChange}
          />,
        )
        expect(screen.queryByTestId('time-range-clear')).not.toBeInTheDocument()
      })

      it('shows clear button when start has a value', () => {
        const onChange = vi.fn()
        render(
          <TimeRangeBar
            timeRange={{ start: '2026-03-15T14:00', end: '' }}
            onTimeRangeChange={onChange}
          />,
        )
        expect(screen.getByTestId('time-range-clear')).toBeInTheDocument()
      })

      it('calls onTimeRangeChange when start input changes', () => {
        const onChange = vi.fn()
        render(
          <TimeRangeBar
            timeRange={{ start: '', end: '' }}
            onTimeRangeChange={onChange}
          />,
        )
        fireEvent.change(screen.getByTestId('time-range-start'), {
          target: { value: '2026-03-15T14:00' },
        })
        expect(onChange).toHaveBeenCalledWith({
          start: '2026-03-15T14:00',
          end: '',
        })
      })

      it('calls onTimeRangeChange with empty values on clear', () => {
        const onChange = vi.fn()
        render(
          <TimeRangeBar
            timeRange={{ start: '2026-03-15T14:00', end: '2026-03-15T15:00' }}
            onTimeRangeChange={onChange}
          />,
        )
        fireEvent.click(screen.getByTestId('time-range-clear'))
        expect(onChange).toHaveBeenCalledWith({ start: '', end: '' })
      })
    })
    ```

    ## Files to modify
    - NONE — these are new files

    ### New files to create
    - `frontend/src/components/TimeRangeBar.tsx` — the component
    - `frontend/src/components/TimeRangeBar.test.tsx` — unit tests

    ## Code patterns to follow
    - Follow the `TagFilterBar.tsx` pattern exactly: interface for Props, controlled component, lifted state.
    - `TagFilterBar` Props (for reference): `{ tags: string[], onTagsChange: (tags: string[]) => void }`
    - `TimeRangeBar` Props: `{ timeRange: TimeRange, onTimeRangeChange: (range: TimeRange) => void }`
    - Export the `TimeRange` type so App.tsx can import it.
    - Test file follows existing `MetricCard.test.tsx` and `SparklineChart.test.tsx` patterns: `describe` block, `vi.fn()` for mocks, `@testing-library/react` for rendering.

    ## Acceptance criteria
    - `TimeRangeBar.tsx` exists and exports `TimeRangeBar` component and `TimeRange` type
    - Component renders two `datetime-local` inputs with `data-testid` attributes
    - Clear button appears only when at least one input has a value
    - Clear button resets both inputs to empty strings
    - All 5 tests pass
    - TypeScript compiles without errors

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx tsc --noEmit && npx vitest run src/components/TimeRangeBar.test.tsx && echo "ALL PASSED"
    ```

### 6. Integrate Time Range into App.tsx
- **Task ID**: app-integration
- **Role**: builder
- **Depends On**: frontend-api-time-range, time-range-bar
- **Assigned To**: builder-2
- **Description**: |
    Wire the time-range state into `App.tsx`, connecting it to metrics polling, the CSV export
    link, and the MetricCard component for sparkline history fetching.

    ## What to do

    1. In `frontend/src/App.tsx`, add imports:

    ```tsx
    import { TimeRangeBar, type TimeRange } from './components/TimeRangeBar'
    ```

    2. Add time range state after the existing `activeTags` state (currently at line 15):

    ```tsx
    const [timeRange, setTimeRange] = useState<TimeRange>({ start: '', end: '' })
    ```

    3. Create a helper to convert the `datetime-local` input value to an ISO-8601 string suitable
       for the API. The `datetime-local` input gives values like `"2026-03-15T14:00"` (no seconds,
       no timezone). The API expects ISO-8601 with timezone info. Add this helper inside the
       component, before `loadMetrics`:

    ```tsx
    const toISOParam = (val: string): string | undefined => {
      if (!val) return undefined
      // datetime-local gives "YYYY-MM-DDTHH:MM" — append seconds and Z for UTC
      return val.includes(':') ? `${val}:00Z` : undefined
    }
    ```

    4. Update `loadMetrics` to pass time range to `fetchMetrics()`. Currently (line 21):
    ```tsx
    const data = await fetchMetrics(activeTagsRef.current)
    ```
    Change to:
    ```tsx
    const data = await fetchMetrics(
      activeTagsRef.current,
      toISOParam(timeRange.start),
      toISOParam(timeRange.end),
    )
    ```

    IMPORTANT: `timeRange` is read directly here (not via ref) because we want the effect to
    re-run when it changes. BUT `loadMetrics` is also used inside the polling interval. To avoid
    stale closures, we need a ref for timeRange too. Add after the `activeTagsRef`:

    ```tsx
    const timeRangeRef = useRef(timeRange)
    timeRangeRef.current = timeRange
    ```

    And use the ref in `loadMetrics`:
    ```tsx
    const data = await fetchMetrics(
      activeTagsRef.current,
      toISOParam(timeRangeRef.current.start),
      toISOParam(timeRangeRef.current.end),
    )
    ```

    5. Add `timeRange` to the dependency array of the "immediate re-fetch on filter change" effect.
       Currently (lines 52-59):
    ```tsx
    useEffect(() => {
      if (isInitialMount.current) {
        isInitialMount.current = false
        return
      }
      loadMetrics()
    }, [activeTags])
    ```
    Change the dependency array to:
    ```tsx
    }, [activeTags, timeRange])
    ```

    6. Update the CSV export link to include time range params. Currently (lines 68-78):
    ```tsx
    <a
      href={
        activeTags.length === 0
          ? '/api/metrics/export?format=csv'
          : `/api/metrics/export?format=csv${activeTags.map(t => `&tag=${encodeURIComponent(t)}`).join('')}`
      }
      className="export-btn"
      download="metrics.csv"
    >
      Export CSV
    </a>
    ```

    Replace with:
    ```tsx
    <a
      href={(() => {
        let url = '/api/metrics/export?format=csv'
        for (const t of activeTags) {
          url += `&tag=${encodeURIComponent(t)}`
        }
        const startParam = toISOParam(timeRange.start)
        const endParam = toISOParam(timeRange.end)
        if (startParam) url += `&start=${encodeURIComponent(startParam)}`
        if (endParam) url += `&end=${encodeURIComponent(endParam)}`
        return url
      })()}
      className="export-btn"
      download="metrics.csv"
    >
      Export CSV
    </a>
    ```

    7. Render `TimeRangeBar` in the JSX, right after `TagFilterBar` (currently at line 83):

    ```tsx
    <TagFilterBar tags={activeTags} onTagsChange={setActiveTags} />
    <TimeRangeBar timeRange={timeRange} onTimeRangeChange={setTimeRange} />
    ```

    8. Update `MetricCard` to receive and use time range. Add a `timeRange` prop to MetricCard.
       In `frontend/src/components/MetricCard.tsx`:

    a. Update the Props interface:
    ```tsx
    interface Props {
      metric: Metric
      onDelete: () => void
      timeRange?: { start: string; end: string }
    }
    ```

    b. Update the component signature:
    ```tsx
    export function MetricCard({ metric, onDelete, timeRange }: Props) {
    ```

    c. Create the same `toISOParam` helper inside MetricCard (or extract it, but for simplicity
       duplicate it — it's 3 lines):
    ```tsx
    const toISOParam = (val: string): string | undefined => {
      if (!val) return undefined
      return val.includes(':') ? `${val}:00Z` : undefined
    }
    ```

    d. Update the `fetchMetricHistory` call in the useEffect (currently line 18):
    ```tsx
    const history = await fetchMetricHistory(metric.name)
    ```
    Change to:
    ```tsx
    const history = await fetchMetricHistory(
      metric.name,
      20,
      toISOParam(timeRange?.start ?? ''),
      toISOParam(timeRange?.end ?? ''),
    )
    ```

    e. Add `timeRange` to the useEffect dependency array. Currently `[metric.name]`, change to:
    ```tsx
    }, [metric.name, timeRange?.start, timeRange?.end])
    ```

    9. In `App.tsx`, pass `timeRange` to `MetricCard`. Currently (line 94):
    ```tsx
    <MetricCard key={m.name} metric={m} onDelete={() => setMetrics(prev => prev.filter(m2 => m2.name !== m.name))} />
    ```
    Change to:
    ```tsx
    <MetricCard key={m.name} metric={m} onDelete={() => setMetrics(prev => prev.filter(m2 => m2.name !== m.name))} timeRange={timeRange} />
    ```

    ## Files to modify
    - `frontend/src/App.tsx` — add TimeRange state, wire into loadMetrics, CSV export, MetricCard
    - `frontend/src/components/MetricCard.tsx` — add timeRange prop, pass to fetchMetricHistory

    ## Code patterns to follow
    - State lifting pattern: `timeRange` state lives in `App.tsx`, passed down as props — same as `activeTags` (DD-004 in design doc).
    - Ref pattern for stable polling: `timeRangeRef.current = timeRange` — same as `activeTagsRef` (avoids stale closure in setInterval callback).
    - Re-fetch on filter change: add `timeRange` to dependency array of the "immediate re-fetch" effect — same pattern as `activeTags` (DD-005 in design doc).
    - MetricCard per-card fetching: pass time range through to `fetchMetricHistory` — extends existing DD-007 pattern.

    ## Acceptance criteria
    - `TimeRangeBar` renders in the UI between `TagFilterBar` and the loading indicator
    - Setting a start datetime triggers an immediate metrics re-fetch
    - Setting an end datetime triggers an immediate metrics re-fetch
    - Clearing the time range triggers a re-fetch (returning all metrics)
    - CSV export link includes `start` and `end` query params when time range is active
    - MetricCard sparklines re-fetch when time range changes
    - Polling continues to work with time range (uses ref to avoid stale closures)
    - TypeScript compiles without errors
    - No changes to the polling interval (still 5s)

    ## Validation command
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx tsc --noEmit && npx vitest run && echo "ALL PASSED"
    ```

### 7. Final Validation
- **Task ID**: validate-all
- **Role**: validator
- **Depends On**: store-time-range, api-time-range, backend-time-tests, frontend-api-time-range, time-range-bar, app-integration
- **Assigned To**: validator
- **Description**: |
    Run all validation commands and verify all acceptance criteria.

    ## Validation Commands

    Run these commands in order. ALL must pass.

    1. Python lint:
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && ruff check .
    ```

    2. All backend tests (existing + 13 new time-range tests):
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && pytest tests/test_api.py -v --tb=short
    ```

    3. TypeScript compilation:
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx tsc --noEmit
    ```

    4. Frontend lint:
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npm run lint
    ```

    5. Frontend tests (including TimeRangeBar tests):
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/frontend && npx vitest run
    ```

    6. Integration smoke test — verify the API endpoints work end-to-end with time params:
    ```bash
    cd /Users/vobbilis/go/src/github.com/vobbilis/codegen/metrics-dashboard/backend && python -c "
    from fastapi.testclient import TestClient
    from main import app, store
    import time
    from datetime import UTC, datetime

    store.clear()
    c = TestClient(app)

    # Create metrics at different times
    c.post('/metrics', json={'name': 'cpu', 'value': 10.0})
    time.sleep(0.05)
    t_mid = datetime.now(UTC).isoformat()
    time.sleep(0.05)
    c.post('/metrics', json={'name': 'cpu', 'value': 20.0})

    # List with time filter
    r = c.get(f'/metrics?start={t_mid}')
    assert r.status_code == 200, f'list with start failed: {r.status_code}'
    assert r.json()[0]['value'] == 20.0, f'wrong value: {r.json()}'

    # History with time filter
    r = c.get(f'/metrics/cpu/history?start={t_mid}')
    assert r.status_code == 200, f'history with start failed: {r.status_code}'
    assert len(r.json()) == 1, f'expected 1 history entry, got {len(r.json())}'

    # Export with time filter
    r = c.get(f'/metrics/export?format=csv&start={t_mid}')
    assert r.status_code == 200, f'export with start failed: {r.status_code}'
    assert '10.0' not in r.text, f'early metric should be filtered out'

    # Invalid datetime
    r = c.get('/metrics?start=bad')
    assert r.status_code == 400, f'expected 400 for bad datetime, got {r.status_code}'

    # Backward compat (no params)
    r = c.get('/metrics')
    assert r.status_code == 200

    store.clear()
    print('INTEGRATION SMOKE TEST PASSED')
    "
    ```

    ## Acceptance Criteria

    Backend:
    - [ ] `store.filter_by_tags([], start=t, end=t)` filters by timestamp range
    - [ ] `store.history(name, start=t, end=t)` filters history by timestamp range
    - [ ] `GET /metrics?start=...&end=...` returns time-filtered metrics
    - [ ] `GET /metrics/{name}/history?start=...&end=...` returns time-filtered history
    - [ ] `GET /metrics/export?start=...&end=...` returns time-filtered CSV
    - [ ] `GET /metrics?start=bad-date` returns 400 with descriptive error
    - [ ] All endpoints work without start/end params (backward compatible)
    - [ ] Tag and time filters combine correctly (AND logic)
    - [ ] All existing tests pass (zero regressions)
    - [ ] 13 new time-range tests pass
    - [ ] `ruff check .` passes

    Frontend:
    - [ ] `fetchMetrics()` accepts optional `start`/`end` string params
    - [ ] `fetchMetricHistory()` accepts optional `start`/`end` string params
    - [ ] `TimeRangeBar` component renders two datetime-local inputs
    - [ ] `TimeRangeBar` clear button resets both inputs
    - [ ] App.tsx has `timeRange` state wired into loadMetrics, CSV export, and MetricCard
    - [ ] MetricCard re-fetches sparkline history when time range changes
    - [ ] `npx tsc --noEmit` passes
    - [ ] `npm run lint` passes
    - [ ] All frontend tests pass (including 5 new TimeRangeBar tests)

### 8. Update Metrics Design Document
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
    specs/time-range-querying.md

    ## Scope
    Time-range querying across the store layer, API layer, and frontend. New `TimeRangeBar`
    component. Changes to `filter_by_tags()`, `history()`, and three API endpoints.

    ## Prior Decisions to Check
    - DD-001: Tag query parameter format — time params use the same `Query(default=None)` pattern but with ISO-8601 strings
    - DD-003: `filter_by_tags()` as a separate method — this plan extends `filter_by_tags` with optional time params rather than creating a separate method, revisiting DD-003's philosophy
    - DD-004: Tag state lifted to App.tsx — timeRange follows the exact same lifted state pattern
    - DD-005: useEffect dependency for auto re-fetch — timeRange added to dependency array
    - DD-007: Per-card history fetching — MetricCard now receives timeRange prop and passes to fetchMetricHistory

    ## What to Record
    Read git diff HEAD~1 HEAD, then the changed source files, then the existing
    design doc. Update Current Design to match the implementation. Append a
    Design Decision entry for each non-trivial architectural choice made in
    this build. Every claim must cite a file:line from the actual code.

    Key design decisions to document:
    1. ISO-8601 datetime strings for query parameters (not unix timestamps)
    2. Both start and end are optional — omitting either means "unbounded on that side"
    3. Time filtering extends `filter_by_tags()` rather than creating a new method (pragmatic extension of DD-003)
    4. `_parse_dt` helper adds UTC timezone to naive datetime inputs
    5. `datetime-local` HTML input for native browser date picker — no external date library
    6. TimeRange state lifted to App.tsx following DD-004 pattern

## Acceptance Criteria

- `GET /metrics?start=<ISO>&end=<ISO>` returns only metrics whose timestamp falls within the specified range (inclusive)
- `GET /metrics/{name}/history?start=<ISO>&end=<ISO>` returns only history entries within the time range
- `GET /metrics/export?start=<ISO>&end=<ISO>` exports only metrics within the time range
- `GET /metrics?start=invalid` returns HTTP 400 with a descriptive error message
- All three endpoints work without start/end params (full backward compatibility)
- Tag filtering and time-range filtering combine with AND logic
- Frontend `TimeRangeBar` component renders start/end datetime-local inputs with a Clear button
- Time range state is lifted to App.tsx and triggers immediate re-fetch on change
- CSV export link includes time-range query params when active
- MetricCard sparklines re-fetch when time range changes
- All existing backend tests pass unchanged
- 13 new backend tests cover time-range filtering on all endpoints
- 5 new frontend tests cover TimeRangeBar component
- `ruff check .` passes, `npx tsc --noEmit` passes, `npm run lint` passes
- Design document updated with new design decisions

## Validation Commands

Execute these commands to validate the task is complete:

- `cd backend && ruff check .` — Python lint passes
- `cd backend && pytest tests/test_api.py -v` — All backend tests pass (existing + 13 new)
- `cd frontend && npx tsc --noEmit` — TypeScript compiles
- `cd frontend && npm run lint` — Frontend lint passes
- `cd frontend && npx vitest run` — Frontend tests pass (including TimeRangeBar tests)

## Notes

- **No new Python dependencies**: `datetime.fromisoformat()` is stdlib (Python 3.11+). No pip installs needed.
- **No new frontend dependencies**: Uses native `<input type="datetime-local">` — no date picker library needed. Supported in all modern browsers.
- **Storage limitation**: Time-range filtering operates within the existing 20-entry history deque. This plan does NOT add persistent storage or increase the deque size. Users can only filter within the last 20 data points per metric. A future plan could add database-backed storage for deeper history.
- **Timezone handling**: All backend timestamps are UTC (`datetime.now(UTC)` in `store.py:19`). The `_parse_dt` helper assumes naive inputs are UTC. Frontend `datetime-local` inputs produce local time — the `toISOParam` helper appends `Z` to treat them as UTC. This is a simplification; a future enhancement could add timezone-aware handling.
- **Performance**: Time filtering uses linear scans over in-memory data. With the 20-entry deque cap and small `_data` dict, this is negligible. No indexing needed.
