---
name: nexus-db-debugging
description: Use when debugging ANY nexus-db issue - query failures, HTTP errors, missing data, quantile/histogram problems. MANDATORY before making any fix. FORBIDDEN is guessing, jumping to conclusions, running commands without checking output. REQUIRED is checking server logs at logs/nexus-db.log, using X-Scope-OrgID header, enabling debug logging, and terminal discipline.
---

# NexusDB Debugging Skill

## THE MANDATE

**Before changing ANY code to "fix" a bug:**
1. Reproduce the exact error
2. Check server logs at `logs/nexus-db.log`
3. Identify root cause with evidence
4. Then and only then, make a fix

---

## FORBIDDEN PATTERNS

### ❌ Guessing and Changing Code - BANNED

```markdown
❌ "Maybe the quantile calculation is wrong" → Change code
❌ "Perhaps the label isn't propagating" → Change code  
❌ "I think the window frame is off" → Change code

✅ REQUIRED: Read logs FIRST, identify exact error, THEN fix
```

### ❌ Forgetting Tenant Header - BANNED

```bash
# ❌ FORBIDDEN - Missing X-Scope-OrgID
curl http://localhost:9090/api/v1/query?query=up

# ✅ REQUIRED - Always include tenant header
curl -H "X-Scope-OrgID: default" http://localhost:9090/api/v1/query?query=up
```

### ❌ Ignoring Server Logs - BANNED

```markdown
❌ Query returns empty → Assume code is broken
✅ Query returns empty → Check logs/nexus-db.log for actual error
```

### ❌ Interrupting Long Commands - BANNED

```markdown
❌ Start cargo test → Get impatient → Ctrl+C → Start another
✅ Start cargo test → Wait for completion → Read full output
```

---

## THE NEXUS-DB DEBUGGING PROCESS

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: CHECK IF SERVER IS RUNNING                             │
│  pgrep -f "nexus-db" && echo "Running"                          │
│         ↓                                                       │
│  STEP 2: ENABLE DEBUG LOGGING (if needed)                       │
│  Set RUST_LOG=debug or edit config/nexus.yaml                   │
│         ↓                                                       │
│  STEP 3: REPRODUCE WITH CURL                                    │
│  curl -H "X-Scope-OrgID: default" http://localhost:9090/...     │
│         ↓                                                       │
│  STEP 4: READ SERVER LOGS                                       │
│  tail -100 logs/nexus-db.log | grep -i "error\|warn"            │
│         ↓                                                       │
│  STEP 5: IDENTIFY ROOT CAUSE                                    │
│  Match log error to code path                                   │
│         ↓                                                       │
│  STEP 6: FIX AND VERIFY                                         │
│  Make targeted fix → Restart server → Re-run curl               │
└─────────────────────────────────────────────────────────────────┘
```

---

## CRITICAL: SERVER LOG LOCATION

The nexus-db server logs to:
```
logs/nexus-db.log
```

**ALWAYS check this file when debugging query issues.**

### Log Checking Commands

```bash
# View last 100 lines
tail -100 logs/nexus-db.log

# Watch logs in real-time
tail -f logs/nexus-db.log

# Search for errors
grep -i "error\|panic\|fail" logs/nexus-db.log | tail -50

# Search for specific query
grep "quantile_over_time" logs/nexus-db.log | tail -20
```

---

## CRITICAL: TENANT HEADERS

NexusDB is multi-tenant. **ALL queries require X-Scope-OrgID header.**

### grafana_interop Uses `default` Tenant

```bash
# For grafana_interop validation
curl -H "X-Scope-OrgID: default" \
  "http://localhost:9090/api/v1/query?query=up"
```

### Common Tenant Values

| Context | Tenant ID |
|---------|-----------|
| grafana_interop | `default` |
| E2E tests | `test-tenant` |
| Local dev | `dev` or `default` |

---

## CRITICAL: ENABLE DEBUG LOGGING

### Option 1: Environment Variable

```bash
RUST_LOG=debug cargo run --bin nexus-db
```

### Option 2: Config File

Edit `config/nexus.yaml`:
```yaml
logging:
  level: debug
```

### Log Levels

| Level | Use When |
|-------|----------|
| `error` | Production - errors only |
| `warn` | Normal dev - warnings + errors |
| `info` | Default - basic operations |
| `debug` | Debugging - detailed query paths |
| `trace` | Deep dive - every function call |

---

## COMMON ERROR PATTERNS

### Error: "No data" from query

**Checklist:**
1. [ ] Server running? `pgrep -f nexus-db`
2. [ ] Correct tenant? `X-Scope-OrgID: default`
3. [ ] Data ingested? Check `data/wal/` has files
4. [ ] Metric exists? `curl ... /api/v1/label/__name__/values`
5. [ ] Time range valid? Check `start` and `end` params

### Error: 401/403 on queries

**Cause:** Missing or wrong tenant header
**Fix:** Add `X-Scope-OrgID: <tenant>` header

### Error: Query returns wrong values

**Checklist:**
1. [ ] Enable debug logging
2. [ ] Check logs for "plan" entries
3. [ ] Verify WindowFrame parameters
4. [ ] Check if aggregation uses correct column

### Error: histogram_quantile returns NaN

**Checklist:**
1. [ ] Histogram buckets exist? Check `_bucket` suffix metrics
2. [ ] `le` label present? Required for histogram_quantile
3. [ ] rate() applied? `histogram_quantile(0.99, rate(...[5m]))`
4. [ ] Window large enough? ≥ 2× scrape interval

### Error: quantile_over_time not recognized

**Checklist:**
1. [ ] UDF registered? Check `src/query/engine.rs` registration
2. [ ] Planner handles it? Check `src/query/planner.rs`
3. [ ] Server restarted after changes?

---

## TERMINAL DISCIPLINE

### Rule 1: One Command at a Time

```markdown
❌ Start build → Get bored → Start another build
✅ Start build → WAIT for completion → Read output
```

### Rule 2: Use isBackground for Long Commands

```markdown
For commands > 30 seconds:
- cargo build → isBackground=true
- cargo test (full suite) → isBackground=true
- Server startup → isBackground=true

Then use get_terminal_output to check status.
```

### Rule 3: Read FULL Output

```markdown
❌ See "test result: ok" → Assume all passed
✅ Read entire output → Check for warnings, skipped tests
```

---

## QUERY DEBUGGING WORKFLOW

### Step 1: Verify Server

```bash
pgrep -f "nexus-db" && curl -s http://localhost:9090/-/ready
```

### Step 2: Test Simple Query First

```bash
curl -H "X-Scope-OrgID: default" \
  "http://localhost:9090/api/v1/query?query=up" | jq '.data.result | length'
```

### Step 3: Build Up Complexity

```bash
# Start simple
curl ... "query=http_requests_total"

# Add function
curl ... "query=rate(http_requests_total[5m])"

# Add aggregation
curl ... "query=sum(rate(http_requests_total[5m])) by (service)"

# Add full complexity
curl ... "query=histogram_quantile(0.99, sum(rate(...[5m])) by (le))"
```

### Step 4: Check Logs After Each Step

```bash
tail -20 logs/nexus-db.log
```

---

## LESSONS LEARNED INTEGRATION

These lessons from `docs/design/LESSONS_LEARNED.md` are critical:

### 1. Label Hydration Pipeline

Labels are HYDRATED at query time, not stored in Parquet:
```
ParquetExec → HydrateLabelsExec → WindowFrame → Projection
```

**Debug:** If labels missing, check HydrateLabelsExec execution in logs.

### 2. Stable vs Unstable Labels

| Cardinality | Type | Storage |
|-------------|------|---------|
| < 5000 | Stable | CatalogCache (series_id) |
| > 5000 | Unstable | attributes column |

**Debug:** High-cardinality label missing? Check attributes column.

### 3. Scrape Interval Rule

```
rate() window ≥ 2× scrape interval
```

**Debug:** rate() returns empty? Window too small.

### 4. DDSketch vs histogram_quantile

| Function | Data Source | Algorithm |
|----------|-------------|-----------|
| `quantile_over_time()` | Raw values | DDSketch |
| `histogram_quantile()` | Pre-bucketed | Linear interpolation |

**Debug:** Wrong function for data type = wrong results.

---

## PRE-FIX CHECKLIST

Before making ANY code change to fix a bug:

- [ ] Reproduced the exact error
- [ ] Checked server logs (`logs/nexus-db.log`)
- [ ] Verified tenant header used (`X-Scope-OrgID`)
- [ ] Confirmed server is running with latest code
- [ ] Identified root cause (not just symptom)
- [ ] Can explain WHY the fix will work

---

## QUICK REFERENCE

| Task | Command |
|------|---------|
| Check server running | `pgrep -f nexus-db` |
| View recent logs | `tail -100 logs/nexus-db.log` |
| Watch logs live | `tail -f logs/nexus-db.log` |
| Query with tenant | `curl -H "X-Scope-OrgID: default" http://localhost:9090/...` |
| Enable debug | `RUST_LOG=debug cargo run --bin nexus-db` |
| List metrics | `curl -H "X-Scope-OrgID: default" "http://localhost:9090/api/v1/label/__name__/values"` |

---

*This skill prevents the most common debugging mistakes in nexus-db development.*
