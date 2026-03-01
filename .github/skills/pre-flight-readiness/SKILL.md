---
skill: pre-flight-readiness
description: "Use BEFORE executing ANY E2E test, integration test, deployment, or multi-system operation. MANDATORY for operations involving >1 component. FORBIDDEN is executing without risk assessment. REQUIRED is the 5-phase 'What If' analysis with mitigations for each failure mode."
mandatory_when:
  - E2E testing involving multiple systems
  - Integration tests crossing component boundaries
  - Deployments to any environment
  - Data migrations
  - Performance benchmarks
  - Any operation that cannot be easily undone
forbidden_patterns:
  - Executing E2E tests without pre-flight check
  - "Let's just run it and see what happens"
  - Assuming components will work together because they work individually
  - Skipping risk assessment for "simple" multi-component operations
required_patterns:
  - 5-phase pre-flight assessment
  - What-If analysis with mitigation matrix
  - Health checks for all participating systems
  - Rollback/cleanup plan before execution
  - Wait-for-readiness strategy with timeouts
---

# Pre-Flight Readiness Skill

## Purpose

This skill ensures you **never execute multi-component operations blind**. 
It mandates anticipatory risk assessment through "What If" questions, 
ensuring failures are **planned for, not reacted to**.

> "Hope is not a strategy. Plan for failure before it plans for you."

---

## The Anti-Pattern We're Preventing

```
❌ BAD: "The tests pass individually, let's run E2E!"
   → Server fails to start
   → Port conflict
   → Data not queryable
   → 2 hours of debugging

✅ GOOD: "Let me run pre-flight checks first"
   → All issues caught in 10 seconds
   → Mitigations applied before execution
   → E2E runs smoothly
```

---

## 5-Phase Pre-Flight Assessment

### Phase 1: Component Inventory
**Question: What systems are involved?**

List EVERY component that must work for the operation to succeed:
- [ ] Source system(s)
- [ ] Target system(s)  
- [ ] Network/transport
- [ ] Storage/persistence
- [ ] Configuration
- [ ] External dependencies

### Phase 2: What-If Analysis
**Question: How can each component fail?**

For EACH component, ask:
1. **What if it won't start?**
2. **What if it's already running (conflict)?**
3. **What if it starts but isn't ready?**
4. **What if it rejects our data/requests?**
5. **What if it's slow?**
6. **What if it crashes mid-operation?**

### Phase 3: Mitigation Matrix
**Question: What's our response to each failure?**

| Component | Failure Mode | Detection | Mitigation |
|-----------|--------------|-----------|------------|
| Server | Won't start | Check stderr | Build first |
| Server | Port conflict | Port check | Kill/change port |
| Data | Not queryable | Poll query | Wait with timeout |
| ... | ... | ... | ... |

### Phase 4: Pre-Checks Script
**Question: Can we automate the detection?**

Turn the mitigation matrix into executable checks:
```python
def preflight():
    check_binary_exists()
    check_port_available()
    check_disk_space()
    check_config_alignment()
    check_dependencies()
    # FAIL FAST if any critical check fails
```

### Phase 5: Rollback Plan
**Question: If we fail mid-operation, how do we recover?**

- [ ] Data cleanup procedure
- [ ] Process termination
- [ ] State reset
- [ ] Verification that we're back to clean state

---

## Pre-Flight Check Categories

### 1. Build Artifacts
- [ ] All binaries exist
- [ ] All binaries are executable
- [ ] Dependencies resolved
- [ ] No compilation errors

### 2. System Resources
- [ ] Sufficient disk space
- [ ] Required ports available
- [ ] Memory headroom
- [ ] Network connectivity

### 3. Configuration
- [ ] All configs present
- [ ] Config values aligned across components
- [ ] Environment variables set
- [ ] Secrets/credentials valid

### 4. Data Contracts
- [ ] Producer outputs match consumer expectations
- [ ] Schemas compatible
- [ ] Tenant IDs aligned
- [ ] Timestamp strategies aligned

### 5. External Dependencies
- [ ] Required services reachable
- [ ] APIs responding
- [ ] Rate limits understood
- [ ] Auth tokens valid

---

## Wait-for-Readiness Strategies

### Pattern: Poll Until Ready
```python
def wait_for_ready(check_fn, timeout=60, interval=1):
    """Poll until check passes or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        if check_fn():
            return True
        time.sleep(interval)
    raise TimeoutError(f"Not ready after {timeout}s")
```

### Pattern: Health Endpoint
```python
def is_healthy(url):
    try:
        r = requests.get(f"{url}/health", timeout=5)
        return r.status_code == 200
    except:
        return False
```

### Pattern: Data Availability Check
```python
def data_available(url, query):
    """Check if data is queryable."""
    r = requests.get(url, params={"query": query})
    data = r.json()
    return len(data.get("data", {}).get("result", [])) > 0
```

---

## E2E Test Pre-Flight Template

```markdown
## E2E Pre-Flight Checklist

### 1. Component Inventory
- [ ] Server: {name} v{version}
- [ ] Client/Injector: {name}
- [ ] Validator: {name}

### 2. What-If Matrix

| What If? | Impact | Mitigation |
|----------|--------|------------|
| Server won't start | BLOCKER | Pre-build, check logs |
| Port in use | BLOCKER | lsof check, kill/reconfig |
| Data not queryable | BLOCKER | Poll with timeout |
| Config mismatch | SILENT FAIL | Contract validation |

### 3. Automated Pre-Checks
- [ ] `./scripts/e2e_preflight.py` passes

### 4. Rollback Plan
- Stop server: `kill $(pgrep nexus-db)`
- Clean data: `rm -rf data/`
- Reset state: `git checkout -- config/`

### 5. GO/NO-GO
- [ ] All critical checks pass
- [ ] Rollback plan documented
- [ ] Expected duration: {X} minutes
- [ ] Max timeout before abort: {Y} minutes
```

---

## Integration with Other Skills

### → From `data-contract-validation`
Run contract validation as part of pre-flight

### → From `terminal-discipline`
Use isBackground=true for long-running processes
Check output with get_terminal_output

### → From `verification-before-completion`
Never declare E2E complete without verification output

### → From `systematic-debugging`
If pre-flight fails, use systematic debugging to find root cause

---

## Self-Audit Checklist

Before executing the multi-component operation, verify:

- [ ] I have listed ALL participating systems
- [ ] I have asked "What If?" for each component
- [ ] I have a mitigation for each failure mode
- [ ] I have automated pre-checks that fail fast
- [ ] I have a wait-for-readiness strategy
- [ ] I have a rollback/cleanup plan
- [ ] I know how long this should take
- [ ] I know when to abort if stuck

---

## Red Flags (Stop and Fix)

🚩 "It worked on my machine" - Not E2E tested
🚩 "Let's just try it" - No risk assessment
🚩 "It's probably fine" - Assumption, not verification
🚩 "We can debug if it fails" - Reactive, not proactive
🚩 "The unit tests pass" - Doesn't validate integration

---

## Example: NexusDB E2E Pre-Flight

```bash
# Run automated pre-flight
./scripts/e2e_preflight.py --skip-server-check

# If server not running, start it
./target/release/nexus-db &

# Wait for health
./scripts/e2e_preflight.py  # Full check including server

# Only NOW run E2E
./scripts/run_e2e.py
```

---

## Key Takeaway

> **Pre-flight is NOT overhead. It's insurance.**
> 
> 5 minutes of pre-flight checks saves 2 hours of debugging.
> A failed pre-flight is a SUCCESS - you caught it before it hurt.
