# Metrics Domain — Living Design Document

> **Last Updated:** 2026-03-17
> **Updated By:** design-updater (build: specs/alert-management-ui-and-history.md)
> **Code Baseline:** 91e53dd + uncommitted alert-management build

## Current Design

The metrics dashboard is a full-stack application with a Python/FastAPI backend and a React/TypeScript frontend. The backend stores metrics in memory and exposes a REST API. The frontend polls the API and renders metrics in a card grid with support for submission, deletion, tag filtering, time-range filtering, alerting with rule management and event history, CSV export, and per-metric sparkline trend charts.

### Key Files

| File | Purpose |
|------|---------|
| `backend/models.py` | Pydantic models: `MetricIn`, `MetricOut`, `MetricSummary`, `AlertRuleIn`, `AlertRuleOut`, `AlertRuleUpdate`, `AlertEvent` |
| `backend/store.py` | `MetricStore` — in-memory storage with query, filter, history, and delete |
| `backend/main.py` | FastAPI app with all REST endpoints and CORS middleware |
| `backend/alert_store.py` | `AlertStore` — alert rule CRUD, event deque, evaluation loop with state transitions |
| `frontend/src/api.ts` | API client: `fetchMetrics()`, `submitMetric()`, `deleteMetric()`, `fetchMetricHistory()`, `createAlert()`, `updateAlert()`, `deleteAlert()`, `fetchAlerts()`, `fetchAlertEvents()` |
| `frontend/src/App.tsx` | Root component: state management, polling, layout composition |
| `frontend/src/components/AlertPanel.tsx` | Alert management UI: rule CRUD form, rule list, event history timeline |
| `frontend/src/components/TagFilterBar.tsx` | Tag filter UI: input, validation, chips, lifted state |
| `frontend/src/components/TimeRangeBar.tsx` | Time range filter UI: start/end datetime-local inputs, clear button |
| `frontend/src/components/MetricCard.tsx` | Metric display card with sparkline history visualization |
| `frontend/src/components/SparklineChart.tsx` | Compact line chart using Recharts — renders trend line with no axes, tooltip, or legend |
| `frontend/src/components/MetricForm.tsx` | Metric submission form |

### Data Model

Metrics carry a `tags` field of type `dict[str, str]` (backend, `models.py:14`) / `Record<string, string>` (frontend, `api.ts:25`). Tags are optional on submission (`default_factory=dict`, `models.py:14`) and always present on output (`models.py:21`).

### Storage Layer

`MetricStore` (`store.py:8-82`) uses an in-memory `dict[str, MetricOut]` keyed by metric name (`store.py:10`) with a parallel `dict[str, deque[MetricOut]]` for history (`store.py:11`). Query methods:

- `all()` (`store.py:27-28`) — returns a copy of all latest-per-name metrics
- `filter_by_tags(tags, start?, end?)` (`store.py:30-46`) — filters by tag key/value pairs using AND logic; optionally filters by timestamp window. Both `start` and `end` are optional `datetime | None` (`store.py:33-34`); omitting either means unbounded on that side. Time filtering applies `>=` for start (`store.py:43`) and `<=` for end (`store.py:45`)
- `by_name(name)` (`store.py:48-50`) — filters by metric name
- `history(name, limit, start?, end?)` (`store.py:52-68`) — returns last N entries from a per-name `deque(maxlen=20)`, optionally filtered by timestamp window. Time filtering is applied before the limit slice (`store.py:64-66`, then `store.py:67-68`)
- `delete(name)` (`store.py:70-74`) — removes metrics and history by name

### API Layer

A shared `_parse_dt(value)` helper (`main.py:44-60`) converts ISO-8601 string query parameters to `datetime` objects. It handles URL-encoded `+` signs (replacing space with `+` at `main.py:47`), adds UTC timezone to naive inputs (`main.py:50-51`), and returns HTTP 400 with a descriptive error for invalid formats (`main.py:54-60`). This helper is used by all time-filtered endpoints.

The `GET /metrics` endpoint (`main.py:83-98`) accepts optional `tag`, `start`, and `end` query parameters (`main.py:85-87`). Each tag must be in `key:value` format. The endpoint:

1. Iterates over `tag` params, validates each contains `:` (`main.py:91`)
2. Returns HTTP 400 with descriptive error if format is invalid (`main.py:92-95`)
3. Splits on first colon via `t.split(":", 1)` to allow colons in values (`main.py:96`)
4. Delegates to `store.filter_by_tags(parsed_tags, _parse_dt(start), _parse_dt(end))` (`main.py:98`)

The `GET /metrics/{name}/history` endpoint (`main.py:152-162`) accepts optional `start` and `end` query parameters (`main.py:156-157`) in addition to the existing `limit` parameter. These are parsed via `_parse_dt()` and passed to `store.history()` (`main.py:159`).

The `GET /metrics/export` endpoint (`main.py:107-149`) also accepts `start` and `end` parameters (`main.py:111-112`) and passes them through `_parse_dt()` to `store.filter_by_tags()` (`main.py:129`), ensuring CSV exports respect the same time-range filtering as the metrics list.

When no `start`/`end` params are provided, `None` flows through all methods — preserving full backward compatibility.

### Frontend API Client

`fetchMetrics(tags?, start?, end?)` (`api.ts:35-49`) constructs the request URL with optional tag and time-range parameters:

1. Creates a `URLSearchParams` instance (`api.ts:36`)
2. Appends each tag as a `tag` parameter (`api.ts:38-41`)
3. Appends `start` and `end` as ISO-8601 strings when provided (`api.ts:42-43`)
4. Appends the query string to the base URL (`api.ts:45`)

When called without arguments, the URL has no query string — backward compatible.

`fetchMetricHistory(name, limit, start?, end?)` (`api.ts:73-86`) fetches the last N data points for a specific metric from `GET /api/metrics/{name}/history`. Now accepts optional `start` and `end` ISO-8601 strings (`api.ts:76-77`) appended as query parameters (`api.ts:81-82`). Returns `Promise<Metric[]>`. Used by `MetricCard` to populate sparkline charts with time-range-aware data (`MetricCard.tsx:22`).

### Frontend State & UI

Tag filter and time-range state are both lifted to `App.tsx`:

- `activeTags` state (`App.tsx:16`) holds the current `string[]` of active tag filters
- `timeRange` state (`App.tsx:19`) holds `{ start: string, end: string }` from datetime-local inputs
- Both use `useRef` mirrors (`App.tsx:17-18`, `App.tsx:20-21`) so the stable polling closure always reads current values without re-creating the interval
- `loadMetrics()` converts `timeRange` values to ISO-8601 via `toISOParam()` (`App.tsx:23-24`) and passes them to `fetchMetrics(tags, start, end)` (`App.tsx:29-33`)
- A separate `useEffect` depends on `[activeTags, timeRange]` (`App.tsx:71`) — changing either triggers an immediate one-time re-fetch (skipping initial mount via `isInitialMount` ref, `App.tsx:64-66`)
- `TagFilterBar` is rendered between `MetricForm` and the loading/error status (`App.tsx:97`)
- `TimeRangeBar` is rendered immediately after `TagFilterBar` (`App.tsx:99`)
- The CSV export link builds its URL with both tag and time-range parameters (`App.tsx:82-87`)

`TagFilterBar` (`TagFilterBar.tsx:8-67`) is a controlled component:

- Props: `tags: string[]` and `onTagsChange: (tags: string[]) => void` (`TagFilterBar.tsx:4-5`)
- Local state for input text and validation error (`TagFilterBar.tsx:9-10`)
- Validates input contains `:` before adding (`TagFilterBar.tsx:14`)
- Prevents duplicate tags (`TagFilterBar.tsx:18`)
- Renders active filters as removable chip elements (`TagFilterBar.tsx:53-63`)
- Supports Enter key submission (`TagFilterBar.tsx:31-36`)

### TimeRangeBar Component

`TimeRangeBar` (`TimeRangeBar.tsx:11-45`) is a controlled component following the same pattern as `TagFilterBar` (DD-004):

- Props: `timeRange: TimeRange` and `onTimeRangeChange: (range: TimeRange) => void` (`TimeRangeBar.tsx:7-9`)
- `TimeRange` interface: `{ start: string, end: string }` (`TimeRangeBar.tsx:1-4`) — empty strings mean unbounded
- Uses native `<input type="datetime-local">` (`TimeRangeBar.tsx:19, 28`) for browser-native date picking with no external dependencies
- Each input has a `data-testid` attribute (`TimeRangeBar.tsx:20, 29`) for test targeting
- A "Clear" button appears only when at least one field has a value (`TimeRangeBar.tsx:34-40`), resetting both to empty strings

### Per-Card History Fetching & Sparklines

Each `MetricCard` independently fetches its own history data using a `useEffect` with `[metric.name, timeRange]` dependency (`MetricCard.tsx:16-40`). The pattern:

- Local state: `historyData` (`MetricCard.tsx:13`) and `historyLoading` (`MetricCard.tsx:14`)
- `useEffect` converts `timeRange` values to ISO-8601 (`MetricCard.tsx:20-21`) and calls `fetchMetricHistory(metric.name, 20, startISO, endISO)` (`MetricCard.tsx:22`)
- Re-fetches when `timeRange` changes, ensuring sparklines reflect the active time window
- Cleanup uses a `cancelled` flag (`MetricCard.tsx:17, 37-39`) to prevent state updates after unmount
- Error handling: catch block silently sets empty data (`MetricCard.tsx:26-29`) — the card continues to show the current value
- The sparkline renders only when loading is complete and data is non-empty (`MetricCard.tsx:60-64`)

`SparklineChart` (`SparklineChart.tsx:9-30`) is a pure presentational component:

- Uses Recharts `LineChart`, `Line`, and `ResponsiveContainer` (`SparklineChart.tsx:1`)
- No axes, tooltip, legend, or cartesian grid — only the trend line (`SparklineChart.tsx:18-28`)
- Returns `null` for empty data (`SparklineChart.tsx:10-12`)
- Duplicates single data points to render a flat line (`SparklineChart.tsx:14`)
- Animation disabled (`isAnimationActive={false}`, `SparklineChart.tsx:25`) for testability
- Default height 60px (`SparklineChart.tsx:9`), responsive width via `ResponsiveContainer` (`SparklineChart.tsx:17`)

### Alert Data Model

Alert rules are defined by `AlertRuleIn` (`models.py:30-33`) for creation and `AlertRuleUpdate` (`models.py:53-56`) for partial updates. All three fields (`metric_name`, `operator`, `threshold`) are optional on update (`models.py:54-56`), using `None` to indicate "no change". `AlertRuleOut` (`models.py:36-42`) adds `id`, `state` (Literal `"ok" | "firing"`, `models.py:41`), and `created_at` timestamp (`models.py:42`).

`AlertEvent` (`models.py:45-50`) records state transitions with `rule_id`, `metric_name`, `old_state`, `new_state`, and a UTC `timestamp` (`models.py:50`). Events are immutable records — once created during evaluation, they are never modified.

### Alert Storage Layer

`AlertStore` (`alert_store.py:9-96`) manages alert rules and events:

- `_rules: list[AlertRuleOut]` (`alert_store.py:11`) — mutable list of alert rules
- `_events: deque[AlertEvent]` with `maxlen=200` (`alert_store.py:12`) — bounded event log that auto-evicts oldest entries
- `add_rule(rule)` (`alert_store.py:14-23`) — creates a new rule with UUID and initial state `"ok"`
- `update_rule(rule_id, update)` (`alert_store.py:38-49`) — applies partial update fields, resets `state` to `"ok"` (`alert_store.py:47`) regardless of which fields changed, returns `None` for unknown IDs
- `all_events()` (`alert_store.py:51-52`) — returns a copy of the event deque as a list
- `evaluate(metric_store)` (`alert_store.py:58-96`) — iterates all rules, compares latest metric value against threshold using the rule's operator. For `"eq"` operator, uses `math.isclose(latest, threshold, rel_tol=1e-6)` (`alert_store.py:78`) to handle float comparison. On state transitions, appends an `AlertEvent` to `_events` (`alert_store.py:85-92`) and updates `rule.state` (`alert_store.py:94`)

The evaluation loop runs as a background `asyncio.Task` every 10 seconds (`main.py:65-71`), with exception guarding (`main.py:70-71`) to prevent loop termination on errors.

### Alert API Layer

- `POST /alerts` (`main.py:223-225`) — creates a new alert rule, returns 201
- `GET /alerts` (`main.py:228-230`) — returns all alert rules
- `GET /alerts/events` (`main.py:233-235`) — returns all alert events (most recent up to 200)
- `PUT /alerts/{rule_id}` (`main.py:238-243`) — partial update of an alert rule via `AlertRuleUpdate` body; returns 404 if rule not found
- `DELETE /alerts/{rule_id}` (`main.py:246-249`) — deletes a single alert rule

The `PUT` endpoint resets the rule's state to `"ok"` on any update (delegated to `alert_store.update_rule`, `alert_store.py:47`), so that changed thresholds are re-evaluated cleanly in the next cycle.

### Frontend Alert API Client

The alert API client (`api.ts:81-133`) provides five functions:

- `fetchAlerts()` (`api.ts:81-85`) — `GET /api/alerts`, returns `AlertRule[]`
- `createAlert(rule)` (`api.ts:102-111`) — `POST /api/alerts` with `AlertRuleIn` body, validates 201 status
- `updateAlert(ruleId, update)` (`api.ts:119-127`) — `PUT /api/alerts/{ruleId}` with `AlertRuleUpdate` body
- `deleteAlert(ruleId)` (`api.ts:113-117`) — `DELETE /api/alerts/{ruleId}`
- `fetchAlertEvents()` (`api.ts:129-133`) — `GET /api/alerts/events`, returns `AlertEvent[]`

Frontend TypeScript types mirror backend models: `AlertRule` (`api.ts:6-13`), `AlertRuleIn` (`api.ts:15-19`), `AlertRuleUpdate` (`api.ts:21-25`), `AlertEvent` (`api.ts:27-33`), `AlertOperator` (`api.ts:3`), `AlertState` (`api.ts:4`).

### AlertPanel Component

`AlertPanel` (`AlertPanel.tsx:21-185`) is a self-contained component managing alert rule CRUD and event history display:

- Props: `alerts: AlertRule[]`, `events: AlertEvent[]`, `onAlertChange: () => void` (`AlertPanel.tsx:13-17`)
- **Form state**: `metricName`, `operator`, `threshold`, `editingId`, `error`, `submitting` — six local state variables (`AlertPanel.tsx:22-27`)
- **Create/Update flow**: The form doubles as both create and edit. When `editingId` is set (`AlertPanel.tsx:51`), `handleSubmit` calls `updateAlert()` (`AlertPanel.tsx:57`); otherwise `createAlert()` (`AlertPanel.tsx:64`). After success, `resetForm()` clears state and `onAlertChange()` triggers parent re-fetch (`AlertPanel.tsx:66-67`)
- **Edit mode**: `handleEdit(alert)` (`AlertPanel.tsx:37-43`) pre-fills form fields from an existing rule and sets `editingId`. A "Cancel" button appears to exit edit mode (`AlertPanel.tsx:118-122`)
- **Rule list**: Maps `alerts` to rows with metric name, operator symbol, threshold, state badge, and edit/delete buttons (`AlertPanel.tsx:130-158`). Firing rules get a red left border (`alert-row--firing`), ok rules get green (`alert-row--ok`)
- **Event timeline**: Renders when `events.length > 0` (`AlertPanel.tsx:162`). Events are reversed for newest-first display (`AlertPanel.tsx:166`). Each item shows timestamp, metric name, and state transition (`AlertPanel.tsx:167-179`)
- **Operator display**: `opSymbol()` helper (`AlertPanel.tsx:19`) maps `"gt"` to `>`, `"lt"` to `<`, `"eq"` to `=`

### Alert State in App.tsx

`App.tsx` manages three alert-related state variables:

- `alerts` (`App.tsx:14`) — `AlertRule[]` from `fetchAlerts()`
- `alertEvents` (`App.tsx:15`) — `AlertEvent[]` from `fetchAlertEvents()`
- `loadAlerts()` (`App.tsx:45-52`) and `loadAlertEvents()` (`App.tsx:54-61`) — independent fetch functions with silent error handling
- `handleAlertChange()` (`App.tsx:89-92`) — callback passed to `AlertPanel` that re-fetches both alerts and events after any CRUD operation
- `AlertPanel` is rendered after the metric grid (`App.tsx:134`) with `alerts`, `alertEvents`, and `handleAlertChange` as props

### Polling

The app polls metrics, alerts, and alert events every 5 seconds (`App.tsx:10`). The polling `useEffect` has an empty dependency array (`App.tsx:70`) — it runs once on mount. The `loadData` function calls `loadMetrics()`, `loadAlerts()`, and `loadAlertEvents()` in parallel via `Promise.all` (`App.tsx:65`). The `loadMetrics()` closure reads current `activeTags` and `timeRange` via `useRef` mirrors (`App.tsx:19-20`, `App.tsx:22-23`) instead of depending on them directly, avoiding interval recreation on every filter change.

---

## Design Decisions

### DD-001: Tag query parameter format — `key:value` with colon separator

**Date:** 2026-03-15

**Context:** The `GET /metrics` endpoint needed a way to accept tag filters as query parameters. Tags are stored as `dict[str, str]` key-value pairs.

**Options considered:**
1. `?tag=env:prod` — colon-separated key:value in a single param
2. `?tag_key=env&tag_value=prod` — separate params for key and value
3. `?tags={"env":"prod"}` — JSON-encoded object

**Decision:** Option 1 — `key:value` format with colon separator.

**Rationale:** Simple, human-readable, composable with repeated params (`?tag=a:b&tag=c:d`). Split on first colon (`main.py:65`) allows colons in values (e.g., URLs).

**Tradeoffs:** Keys cannot contain colons. This is acceptable for typical tag keys (env, service, region, etc.).

**Code evidence:** `backend/main.py:57-67`, `backend/tests/test_api.py:759-766` (colon-in-value test)

---

### DD-002: AND logic for multiple tag filters

**Date:** 2026-03-15

**Context:** When multiple tag filters are specified, the system needs a combining strategy.

**Options considered:**
1. AND — metrics must match ALL specified tags
2. OR — metrics must match ANY specified tag

**Decision:** AND logic — all specified tags must match.

**Rationale:** AND is the more common filtering semantic (narrowing results). Users can always remove filters to broaden results. OR logic would be harder to use for precise filtering.

**Tradeoffs:** Cannot express "env:prod OR env:staging" in a single query. This could be added later with an explicit OR operator if needed.

**Code evidence:** `backend/store.py:35` (`all(m.tags.get(k) == v for k, v in tags)`), `backend/tests/test_api.py:732-741` (multi-tag AND test)

---

### DD-003: `filter_by_tags()` as a separate method from `all()`

**Date:** 2026-03-15

**Context:** Tag filtering could be implemented by modifying the existing `all()` method or as a new method.

**Options considered:**
1. Add optional `tags` parameter to `all()`
2. Create a new `filter_by_tags()` method

**Decision:** Option 2 — new `filter_by_tags()` method, later extended with time-range parameters.

**Rationale:** Keeps `all()` simple and backward compatible. The filtering method has distinct semantics (AND logic, tuple-based input) that deserve their own method signature. When time-range filtering was added, `filter_by_tags()` was extended with optional `start`/`end` parameters (`store.py:33-34`) rather than creating a third method — the method name still accurately describes its primary role, and the optional datetime parameters compose naturally with the existing tag filtering.

**Tradeoffs:** Two methods that can return "all metrics" (`all()` and `filter_by_tags([])`). Acceptable because `filter_by_tags([])` explicitly documents intent.

**Code evidence:** `backend/store.py:27-28` (`all()`), `backend/store.py:30-46` (`filter_by_tags()` with time-range), `backend/main.py:98` (endpoint uses `filter_by_tags`)

---

### DD-004: Tag state lifted to App.tsx with TagFilterBar as controlled component

**Date:** 2026-03-15

**Context:** The tag filter state needs to be accessible to both the filter UI and the data-fetching logic.

**Options considered:**
1. Tag state owned by `TagFilterBar`, communicated via callback
2. Tag state lifted to `App.tsx`, `TagFilterBar` as controlled component

**Decision:** Option 2 — lifted state.

**Rationale:** `App.tsx` owns the fetch logic and needs direct access to `activeTags` for `fetchMetrics(activeTags)` (`App.tsx:19`). Lifting state avoids prop-drilling callbacks and keeps the data flow unidirectional.

**Tradeoffs:** `App.tsx` gains another piece of state. Acceptable given the component's existing role as state coordinator.

**Code evidence:** `frontend/src/App.tsx:15` (`activeTags` state), `frontend/src/App.tsx:62` (controlled prop passing), `frontend/src/components/TagFilterBar.tsx:4-5` (Props interface)

---

### DD-005: `useEffect` dependency on `activeTags` and `timeRange` for automatic re-fetch

**Date:** 2026-03-15 (updated 2026-03-16)

**Context:** When the user changes tag filters or time-range selection, metrics should update immediately rather than waiting for the next poll cycle.

**Options considered:**
1. Manual re-fetch via callback when filters change
2. Include filter state in `useEffect` dependency array

**Decision:** Option 2 — `useEffect` dependency on `[activeTags, timeRange]` (`App.tsx:71`).

**Rationale:** A separate `useEffect` watches `activeTags` and `timeRange` and triggers an immediate `loadMetrics()` call. It skips the initial mount using an `isInitialMount` ref (`App.tsx:64-66`) to avoid double-fetching on startup. The polling interval `useEffect` has an empty dependency array (`App.tsx:61`) and reads current filter values through `useRef` mirrors (`App.tsx:17-18`, `App.tsx:20-21`), avoiding interval recreation when filters change.

**Tradeoffs:** Two separate `useEffect` hooks for polling vs. filter-change response adds mild complexity but cleanly separates concerns: one for the stable 5s interval, one for immediate filter reactivity.

**Code evidence:** `frontend/src/App.tsx:54-61` (stable polling useEffect), `frontend/src/App.tsx:64-71` (filter-change useEffect), `frontend/src/App.tsx:17-21` (useRef mirrors)

---

### DD-006: Recharts for sparkline visualization — minimal line chart with no chrome

**Date:** 2026-03-15

**Context:** MetricCard needed a compact trend visualization. A charting library was required to render SVG line charts from `{ value: number }[]` data.

**Options considered:**
1. Recharts — React-native composable charting library built on D3; provides `LineChart`, `Line`, `ResponsiveContainer` components
2. Chart.js / react-chartjs-2 — canvas-based charting, heavier bundle, less React-idiomatic
3. Custom SVG — manual `<polyline>` rendering from data points

**Decision:** Option 1 — Recharts (`recharts` ^3.8.0, `frontend/package.json:17`).

**Rationale:** Recharts is purpose-built for React with composable components. A sparkline requires only `LineChart`, `Line`, and `ResponsiveContainer` — three imports (`SparklineChart.tsx:1`). No axes (`XAxis`, `YAxis`), no tooltip, no legend, no grid are rendered. The `dot={false}` prop removes data point markers (`SparklineChart.tsx:24`). Animation is disabled with `isAnimationActive={false}` (`SparklineChart.tsx:25`) to ensure deterministic rendering and testable output.

**Tradeoffs accepted:** Recharts adds ~200KB to the production bundle. Acceptable for a dashboard application that already bundles React and React-DOM. A custom SVG polyline would be lighter but harder to maintain and extend.

**Code evidence:** `frontend/src/components/SparklineChart.tsx:1` (imports), `frontend/src/components/SparklineChart.tsx:17-28` (minimal LineChart with no chrome), `frontend/package.json:17` (recharts dependency)

**Build:** `specs/metric-history-sparklines.md`

---

### DD-007: Per-card history fetching in MetricCard vs. lifting to App.tsx

**Date:** 2026-03-15

**Context:** Each MetricCard needs historical data to render its sparkline. The data could be fetched at the card level or lifted to the parent `App.tsx`.

**Options considered:**
1. Fetch history in each `MetricCard` via `useEffect` — each card manages its own loading/error state
2. Fetch all history in `App.tsx` and pass as props — centralized data management, single loading state

**Decision:** Option 1 — per-card fetching in `MetricCard` (`MetricCard.tsx:16-40`).

**Rationale:** History is card-specific data tied to `metric.name`. Lifting to `App.tsx` would require N parallel API calls coordinated at the parent level, adding complexity to an already state-heavy component. Per-card fetching keeps the data collocated with its consumer and allows independent loading/error handling. The `useEffect` cleanup with a `cancelled` flag (`MetricCard.tsx:17, 37-39`) prevents state updates on unmounted components. Error handling is silent — the card still shows its current value without a sparkline (`MetricCard.tsx:26-29`). The `timeRange` prop (`MetricCard.tsx:8`) is included in the `useEffect` dependency array (`MetricCard.tsx:40`) so sparklines re-fetch when the time window changes.

**Tradeoffs accepted:** Each card makes an independent API call on mount and on every time-range change, which could mean many concurrent requests if many cards are visible. Acceptable because the history endpoint (`GET /metrics/{name}/history`) is lightweight (returns max 20 entries from an in-memory deque). If card count grows significantly, a batched fetch could be introduced later.

**Code evidence:** `frontend/src/components/MetricCard.tsx:16-40` (useEffect with per-card fetch), `frontend/src/components/MetricCard.tsx:13-14` (local state), `frontend/src/components/MetricCard.tsx:60-64` (conditional sparkline rendering)

**Build:** `specs/metric-history-sparklines.md`

---

### DD-008: ISO-8601 datetime strings for time-range query parameters

**Date:** 2026-03-16

**Context:** The API needed a format for `start` and `end` query parameters. Choices include Unix timestamps, ISO-8601 strings, or custom formats.

**Options considered:**
1. Unix timestamps (integer seconds or milliseconds) — compact, unambiguous
2. ISO-8601 strings (e.g., `2026-03-15T14:00:00`) — human-readable, standard
3. Custom date format (e.g., `YYYY-MM-DD HH:MM`) — simpler but non-standard

**Decision:** Option 2 — ISO-8601 strings parsed by `datetime.fromisoformat()`.

**Rationale:** ISO-8601 is the standard for date interchange in REST APIs. Python's `datetime.fromisoformat()` handles it natively (`main.py:49`). The frontend's `Date.toISOString()` produces compatible output (`App.tsx:23-24`). The `datetime-local` HTML input type produces ISO-compatible values (`TimeRangeBar.tsx:19`).

**Tradeoffs:** URL-encoded `+` in timezone offsets (e.g., `+00:00`) gets decoded as a space by query-string parsers. The `_parse_dt` helper compensates by replacing space with `+` (`main.py:47`).

**Code evidence:** `backend/main.py:44-60` (`_parse_dt` helper), `frontend/src/App.tsx:23-24` (`toISOParam` conversion), `frontend/src/components/TimeRangeBar.tsx:19` (datetime-local input)

**Build:** `specs/time-range-querying.md`

---

### DD-009: Both `start` and `end` optional — omitting means unbounded

**Date:** 2026-03-16

**Context:** Time-range filtering could require both bounds, one bound, or neither. The API needed a convention for missing bounds.

**Options considered:**
1. Require both `start` and `end` when either is provided
2. Each is independently optional — omitted means unbounded on that side

**Decision:** Option 2 — independently optional with `None` semantics.

**Rationale:** Users commonly want "everything after X" or "everything before Y" without specifying the other bound. The store methods accept `datetime | None` (`store.py:33-34`, `store.py:57-58`) and only apply filtering when the value is not `None` (`store.py:42-45`, `store.py:64-66`). The frontend sends empty strings for unset values (`TimeRangeBar.tsx:1-4`), which the API client omits from query parameters (`api.ts:42-43`).

**Tradeoffs:** None significant. The pattern is standard for range queries.

**Code evidence:** `backend/store.py:33-34` (optional params), `backend/store.py:42-45` (conditional filtering), `frontend/src/api.ts:42-43` (conditional param append)

**Build:** `specs/time-range-querying.md`

---

### DD-010: Extend `filter_by_tags()` with time-range rather than creating a new method

**Date:** 2026-03-16

**Context:** Time-range filtering could be implemented as a new store method or by extending the existing `filter_by_tags()` method.

**Options considered:**
1. New `filter_by_time_range()` method — separate concerns
2. Add `start`/`end` parameters to `filter_by_tags()` — single method composes all filters

**Decision:** Option 2 — extend `filter_by_tags()` with optional `start` and `end` parameters (`store.py:30-46`).

**Rationale:** All three API endpoints that filter metrics (`GET /metrics`, `GET /metrics/export`, `GET /metrics/{name}/history`) need both tag and time-range filtering applied together. A single method avoids the caller needing to chain two filter calls and reduces the risk of one filter being forgotten. The new parameters default to `None` (`store.py:33-34`), preserving backward compatibility for all existing callers.

**Tradeoffs:** `filter_by_tags` name no longer fully describes the method's capability. Acceptable because tag filtering remains the primary use case and the time-range parameters are clearly optional additions.

**Code evidence:** `backend/store.py:30-46` (`filter_by_tags` with time params), `backend/main.py:98` (metrics endpoint), `backend/main.py:129` (export endpoint)

**Build:** `specs/time-range-querying.md`

---

### DD-011: `_parse_dt` helper adds UTC timezone to naive datetime inputs

**Date:** 2026-03-16

**Context:** Users may submit datetime strings with or without timezone information. The store compares timestamps using timezone-aware `datetime` objects (created with `datetime.now(UTC)` at `store.py:19`).

**Options considered:**
1. Reject naive (timezone-less) datetime inputs with HTTP 400
2. Assume UTC for naive inputs

**Decision:** Option 2 — assume UTC via `dt.replace(tzinfo=UTC)` (`main.py:51`).

**Rationale:** The `datetime-local` HTML input produces naive strings (e.g., `2026-03-15T14:00:00`). Rejecting them would force the frontend to always append `Z` or `+00:00`, adding unnecessary complexity. Since all stored timestamps use UTC (`store.py:19`), assuming UTC for naive inputs is the least surprising behavior.

**Tradeoffs:** Users in non-UTC timezones who provide timezone-naive strings will get UTC interpretation, not local time. The frontend mitigates this by converting through `new Date(val).toISOString()` (`App.tsx:23-24`), which produces UTC-based ISO strings.

**Code evidence:** `backend/main.py:50-51` (naive to UTC), `backend/store.py:19` (stored as UTC), `frontend/src/App.tsx:23-24` (frontend UTC conversion)

**Build:** `specs/time-range-querying.md`

---

### DD-012: `datetime-local` HTML input for native browser date picker

**Date:** 2026-03-16

**Context:** The frontend needed a date/time picker for the time-range filter UI.

**Options considered:**
1. Native `<input type="datetime-local">` — built-in browser date picker
2. Third-party date picker library (e.g., react-datepicker, MUI DateTimePicker)
3. Text input with manual ISO-8601 parsing

**Decision:** Option 1 — native `datetime-local` input (`TimeRangeBar.tsx:19, 28`).

**Rationale:** Zero additional dependencies. Modern browsers provide a consistent date picker UI with calendar, time selection, and keyboard navigation. The output format is directly compatible with ISO-8601 parsing. The `TimeRangeBar` component stays lightweight (45 lines) with no external imports beyond React.

**Tradeoffs:** Minor visual inconsistency across browsers (Chrome, Firefox, Safari render slightly different pickers). Acceptable for a developer-facing dashboard where functionality matters more than pixel-perfect design. No time zone selector — the frontend converts to UTC via `new Date(val).toISOString()` before sending to the API.

**Code evidence:** `frontend/src/components/TimeRangeBar.tsx:19` (start input), `frontend/src/components/TimeRangeBar.tsx:28` (end input), `frontend/src/App.tsx:23-24` (UTC conversion)

**Build:** `specs/time-range-querying.md`

---

### DD-013: TimeRange state lifted to App.tsx following DD-004 pattern

**Date:** 2026-03-16

**Context:** The time-range filter state needs to be accessible to the data-fetching logic in `App.tsx`, the `TimeRangeBar` UI, the `MetricCard` sparklines, and the CSV export link.

**Decision:** Lift `timeRange` state to `App.tsx` (`App.tsx:19`), following the same controlled-component pattern established in DD-004 for tag filters.

**Rationale:** Four consumers need the time-range state: (1) `loadMetrics()` for polling (`App.tsx:28-33`), (2) `TimeRangeBar` for the input UI (`App.tsx:99`), (3) `MetricCard` for sparkline history fetching (`App.tsx:110`), and (4) the CSV export link (`App.tsx:84-86`). Lifting state to `App.tsx` is the minimal solution that serves all consumers. The `useRef` mirror pattern (`App.tsx:20-21`) allows the stable polling closure to read current values without adding `timeRange` to the polling `useEffect` dependency array.

**Tradeoffs:** `App.tsx` gains another piece of state and another `useRef` mirror. Consistent with the existing pattern for `activeTags` (`App.tsx:16-18`).

**Code evidence:** `frontend/src/App.tsx:19` (timeRange state), `frontend/src/App.tsx:20-21` (useRef mirror), `frontend/src/App.tsx:99` (TimeRangeBar rendering), `frontend/src/App.tsx:110` (MetricCard receives timeRange prop)

**Build:** `specs/time-range-querying.md`

---

### DD-014: `AlertEvent` model with `deque(maxlen=200)` for bounded event log

**Date:** 2026-03-17

**Context:** Alert state transitions need to be recorded for a history view. The system needed a storage strategy for event records.

**Options considered:**
1. Unbounded list — simple but grows without limit in memory
2. `deque(maxlen=200)` — bounded FIFO buffer that auto-evicts oldest entries
3. Time-based retention (e.g., last 24 hours) — requires periodic cleanup

**Decision:** Option 2 — `deque(maxlen=200)` (`alert_store.py:12`).

**Rationale:** The dashboard is an in-memory system with no persistence layer. A bounded deque provides automatic eviction with O(1) append, no cleanup needed. 200 entries is sufficient for a dashboard history view while preventing unbounded memory growth. The `AlertEvent` model (`models.py:45-50`) is immutable — once created during `evaluate()`, events are never modified.

**Tradeoffs:** Oldest events are silently dropped when the buffer is full. Acceptable for a real-time dashboard where recent history is most relevant.

**Code evidence:** `backend/alert_store.py:12` (deque maxlen=200), `backend/models.py:45-50` (AlertEvent model), `backend/alert_store.py:85-92` (event creation during evaluate)

**Build:** `specs/alert-management-ui-and-history.md`

---

### DD-015: `update_rule()` resets state to `"ok"` on any field change

**Date:** 2026-03-17

**Context:** When an alert rule's threshold or operator is modified via `PUT /alerts/{id}`, the existing `state` may no longer be valid (e.g., the rule was `"firing"` at threshold 50, now threshold is 100).

**Options considered:**
1. Keep existing state — let the next evaluation cycle determine the new state
2. Reset state to `"ok"` on any update — immediate clean slate
3. Re-evaluate immediately on update — most accurate but adds complexity

**Decision:** Option 2 — reset `state` to `"ok"` unconditionally (`alert_store.py:47`).

**Rationale:** The evaluation loop runs every 10 seconds (`main.py:67`). Resetting to `"ok"` ensures the rule is cleanly re-evaluated in the next cycle. This avoids a window where a rule shows `"firing"` with a threshold it no longer matches. The `AlertRuleUpdate` model (`models.py:53-56`) uses `None` defaults for all fields, so only provided fields are applied (`alert_store.py:41-46`), but state is always reset regardless.

**Tradeoffs:** A brief `"ok"` state between update and next evaluation (up to 10s). Acceptable because the alternative — re-evaluating inline — would couple the update endpoint to the metric store.

**Code evidence:** `backend/alert_store.py:38-49` (update_rule with state reset), `backend/models.py:53-56` (AlertRuleUpdate), `backend/main.py:238-243` (PUT endpoint)

**Build:** `specs/alert-management-ui-and-history.md`

---

### DD-016: `math.isclose()` for float equality in alert evaluation

**Date:** 2026-03-17

**Context:** The `"eq"` operator compares a metric value to a threshold. Direct float comparison (`==`) is unreliable due to floating-point precision issues.

**Decision:** Use `math.isclose(latest, threshold, rel_tol=1e-6)` (`alert_store.py:78`).

**Rationale:** `math.isclose` with a relative tolerance of 1e-6 handles typical floating-point representation errors while being strict enough for meaningful equality checks on metric values (which are typically measurements like CPU%, memory%, etc.).

**Tradeoffs:** Values within 0.0001% of each other are considered equal. This could mask genuinely different values at extreme precision, but metric dashboard use cases don't require sub-ppm precision.

**Code evidence:** `backend/alert_store.py:78` (math.isclose), `backend/alert_store.py:1` (import math)

**Build:** `specs/alert-management-ui-and-history.md`

---

### DD-017: AlertPanel as self-contained CRUD component with dual-mode form

**Date:** 2026-03-17

**Context:** The alert management UI needed create, read, update, and delete capabilities for alert rules, plus event history display.

**Options considered:**
1. Separate components for create form, edit form, rule list, and event history
2. Single `AlertPanel` component with a dual-mode form (create/edit) and integrated list + timeline

**Decision:** Option 2 — single `AlertPanel` component (`AlertPanel.tsx:21-185`).

**Rationale:** Alert CRUD is a cohesive feature with tightly coupled state: editing a rule requires the same form fields as creating one, just pre-filled. Using `editingId` state (`AlertPanel.tsx:25`) to toggle between create and update modes (`AlertPanel.tsx:51`) keeps the form DRY. The component receives `alerts` and `events` as props from `App.tsx` and delegates data refreshing to `onAlertChange()` (`AlertPanel.tsx:16`), keeping it stateless for data but stateful for form interaction.

**Tradeoffs:** At 185 lines, the component is larger than most in the project. Acceptable because the state interactions (form, edit mode, error handling) are tightly coupled and would gain little from decomposition.

**Code evidence:** `frontend/src/components/AlertPanel.tsx:21-185` (full component), `frontend/src/components/AlertPanel.tsx:25` (editingId toggle), `frontend/src/components/AlertPanel.tsx:51` (create vs update branch), `frontend/src/App.tsx:134` (integration)

**Build:** `specs/alert-management-ui-and-history.md`

---

### DD-018: Alert and event polling unified with metrics in `Promise.all`

**Date:** 2026-03-17

**Context:** Alert rules and events need to be kept current in the UI. The polling strategy could be independent intervals or unified with the existing metrics poll.

**Options considered:**
1. Separate polling intervals for alerts and events
2. Unified polling — fetch metrics, alerts, and events together in the same interval

**Decision:** Option 2 — unified `Promise.all([loadMetrics(), loadAlerts(), loadAlertEvents()])` (`App.tsx:65`).

**Rationale:** A single 5-second interval (`App.tsx:10`) with `Promise.all` keeps all data in sync with minimal complexity. Three lightweight in-memory endpoints add negligible overhead. The `handleAlertChange()` callback (`App.tsx:89-92`) provides immediate refresh after CRUD operations without waiting for the next poll cycle.

**Tradeoffs:** Alert data is fetched even when unchanged. Acceptable for an in-memory backend with O(1) list copy operations.

**Code evidence:** `frontend/src/App.tsx:63-70` (unified polling useEffect), `frontend/src/App.tsx:65` (Promise.all), `frontend/src/App.tsx:89-92` (handleAlertChange callback), `frontend/src/App.tsx:134` (onAlertChange prop)

**Build:** `specs/alert-management-ui-and-history.md`
