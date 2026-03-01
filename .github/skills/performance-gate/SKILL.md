---
name: performance-gate
description: Use BEFORE and AFTER any code change that touches query path, storage, or hot paths. MANDATORY for optimizer rules, UDFs, execution changes. FORBIDDEN is merging without benchmark comparison. REQUIRED is baseline capture, change, re-benchmark, compare, gate on regression threshold.
---

# Performance Gate

## THE MANDATE

**No performance-sensitive change ships without before/after benchmarks.**

Before touching ANY code in hot paths:
- Query engines, planners, execution layers
- Storage layers, caching, indexing
- Ingestion/write paths
- Optimizer rules, UDFs, middleware

You MUST:
1. Capture baseline benchmark
2. Make change
3. Re-run benchmark
4. Compare: If p50 regression >10%, STOP

---

## WHY THIS SKILL EXISTS

### The Repeated Pattern

```
Day 1: Add optimizer rule → 3x regression → debug 2 hours → revert
Day 2: Re-add with "fix" → Still slow → debug 1 hour → partial revert missed
Day 3: Find missed code → Full revert → Finally back to baseline
```

**Hours wasted: 4+**

### The Fix

```
Step 1: Run benchmark, save baseline (2 min)
Step 2: Make change (X min)
Step 3: Run benchmark, compare (2 min)
Step 4: If regression: STOP before debugging
```

**Time saved: Hours**

---

## FORBIDDEN PATTERNS

### ❌ Changing Hot Paths Without Baseline - BANNED

```markdown
❌ FORBIDDEN:
"Let me add this optimizer rule"
*Adds rule*
*Runs tests*
"Why is it slow?"
*Debugs for an hour*

✅ REQUIRED:
"Let me capture baseline first"
*Runs benchmark, saves results*
*Adds rule*
*Runs benchmark, compares*
"p50 went from 150ms to 450ms - 3x regression. Not enabling."
```

### ❌ "It Should Be Fast" Assumptions - BANNED

```markdown
❌ FORBIDDEN:
"This is just a simple check, it won't affect performance"
"The optimizer should skip this quickly"
"It's only called once per request"

✅ REQUIRED:
Benchmark proves it's fast. Assumptions are worthless.
```

### ❌ Shipping Without Comparison - BANNED

```markdown
❌ FORBIDDEN:
*Makes change*
"Tests pass, looks good"
*Ships*
*User reports slowdown*

✅ REQUIRED:
*Captures baseline*
*Makes change*
*Compares: p50 150ms → 152ms (1.3% - OK)*
*Ships with confidence*
```

---

## REQUIRED WORKFLOW

### Step 1: Capture Baseline (BEFORE any change)

```bash
# Run your project's benchmark and save
# Examples:
./run_benchmark.sh 2>&1 | tee outputs/baseline_$(date +%Y%m%d_%H%M%S).log
cargo bench 2>&1 | tee outputs/baseline_$(date +%Y%m%d_%H%M%S).log
npm run bench 2>&1 | tee outputs/baseline_$(date +%Y%m%d_%H%M%S).log

# Extract and record key metrics (p50, p90, p99, throughput)
```

**Record these numbers. They are your gate.**

### Step 2: Make Your Change

Implement the feature, optimization, or fix.

### Step 3: Re-benchmark (AFTER change)

```bash
# Rebuild
cargo build --release  # or npm run build, etc.

# Run same benchmark
./run_benchmark.sh 2>&1 | tee outputs/after_change_$(date +%Y%m%d_%H%M%S).log

# Compare key metrics
```

### Step 4: Gate Decision

| Metric | Baseline | After | Change | Decision |
|--------|----------|-------|--------|----------|
| p50 | 150ms | 155ms | +3% | ✅ PASS |
| p50 | 150ms | 180ms | +20% | ❌ FAIL |
| p50 | 150ms | 450ms | +200% | ❌ FAIL - DO NOT SHIP |

**Thresholds:**
- p50 regression ≤10%: ✅ OK to proceed
- p50 regression 10-20%: ⚠️ Investigate, justify, or optimize
- p50 regression >20%: ❌ BLOCKED - Must fix or abandon

---

## FEATURE FLAG PATTERN

For risky features, use a feature flag so you can disable without code changes:

```rust
// Rust example
let enable_feature = std::env::var("ENABLE_NEW_OPTIMIZER")
    .map(|v| v == "true")
    .unwrap_or(false);
```

```typescript
// TypeScript example
const enableFeature = process.env.ENABLE_NEW_OPTIMIZER === 'true';
```

This allows:
- Testing with flag on in dev
- Quick disable if regression found
- Gradual rollout in production

---

## CHECKLIST

### Before ANY Hot Path Change

- [ ] Identify the benchmark to use
- [ ] Run baseline benchmark
- [ ] Record p50, p90, p99 (or relevant metrics)
- [ ] Save log file with timestamp

### After Making Change

- [ ] Rebuild in release/production mode
- [ ] Run same benchmark
- [ ] Compare metrics to baseline
- [ ] Calculate % change

### Gate Decision

- [ ] p50 regression ≤10%? → Proceed
- [ ] p50 regression 10-20%? → Investigate/optimize
- [ ] p50 regression >20%? → STOP, do not ship

### If Blocked

- [ ] Profile to find bottleneck
- [ ] Optimize or redesign
- [ ] Re-benchmark
- [ ] Repeat until passing gate

---

## INTEGRATION WITH OTHER SKILLS

- **verification-before-completion**: Benchmark comparison IS verification
- **safe-rollback**: If regression found, use git rollback
- **terminal-discipline**: Benchmarks are long-running, use isBackground=true

---

## THE GOLDEN RULE

> "If you didn't benchmark it, you don't know if it's fast."

Assumptions kill performance. Data saves it.
