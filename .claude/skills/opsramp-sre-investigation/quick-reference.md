# OpsRamp Investigation Quick Reference

## Common Investigation Scenarios

### Scenario 1: High Latency

**Socratic Questions:**
1. "What's the current latency vs baseline?"
2. "Is it P50 (everyone) or P99 (tail)?"
3. "When did it start?"
4. "Which service in the call chain is slow?"

**OpsRamp Checks:**
- Service Health Dashboard → Latency panel
- Distributed Traces → Sort by duration
- Service Map → Check edge latencies
- Compare with 24h rolling average

**Hypotheses to Test:**
| Hypothesis | OpsRamp Evidence |
|------------|------------------|
| Resource contention | CPU/Memory near limits |
| Database slow | DB latency in traces |
| External dependency | External call duration |
| Traffic spike | Request rate increase |

---

### Scenario 2: High Error Rate

**Socratic Questions:**
1. "What type of errors? 4xx or 5xx?"
2. "Are they retryable or permanent failures?"
3. "Which endpoint is affected?"
4. "Is it all requests or a subset?"

**OpsRamp Checks:**
- Error rate trend line
- Error breakdown by status code
- Logs filtered for errors
- Traces with error spans

**Hypotheses to Test:**
| Hypothesis | OpsRamp Evidence |
|------------|------------------|
| Application bug | Stack traces in logs |
| Dependency failure | Downstream errors in traces |
| Configuration error | Errors after config change |
| Resource exhaustion | 503s + resource metrics high |

---

### Scenario 3: Pod Crashes / Restarts

**Socratic Questions:**
1. "What's the exit code?"
2. "Is it OOMKilled or application error?"
3. "How frequently is it restarting?"
4. "What do the previous logs show?"

**OpsRamp Checks:**
- Container restart count metric
- Memory usage vs limits
- Container state history
- Last log lines before crash

**Hypotheses to Test:**
| Hypothesis | OpsRamp Evidence |
|------------|------------------|
| Memory leak | Growing memory before OOM |
| Startup failure | Crash within seconds of start |
| Dependency timeout | Timeout errors in logs |
| Liveness probe failure | Probe failure events |

---

### Scenario 4: Service Unavailable

**Socratic Questions:**
1. "Is it completely down or partial?"
2. "Are pods running?"
3. "Are endpoints registered?"
4. "Is traffic reaching the service?"

**OpsRamp Checks:**
- Service health score
- Pod status in Kubernetes view
- Endpoint count
- Request rate (is it zero?)

**Hypotheses to Test:**
| Hypothesis | OpsRamp Evidence |
|------------|------------------|
| No healthy pods | All pods in CrashLoop |
| Service misconfigured | Zero endpoints |
| Network policy | Traffic blocked |
| DNS failure | DNS errors in logs |

---

## OpsRamp Dashboard Patterns

### Golden Signals Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  SERVICE: payment-service                                   │
├──────────────┬──────────────┬───────────────┬──────────────┤
│   LATENCY    │    ERRORS    │    TRAFFIC    │  SATURATION  │
│   P99: 250ms │   Rate: 0.1% │   Rate: 1.2k  │  CPU: 45%    │
│   P50: 45ms  │   Total: 12  │   RPM         │  Mem: 62%    │
│   Trend: ↑   │   Trend: ↔   │   Trend: ↑    │  Trend: ↔    │
└──────────────┴──────────────┴───────────────┴──────────────┘
```

### What to Look For

| Signal | Normal | Warning | Critical |
|--------|--------|---------|----------|
| P99 Latency | < 500ms | 500ms-2s | > 2s |
| Error Rate | < 1% | 1-5% | > 5% |
| CPU Usage | < 60% | 60-80% | > 80% |
| Memory Usage | < 70% | 70-85% | > 85% |

---

## Socratic Question Templates

### For Vague Reports

| User Says | Ask This |
|-----------|----------|
| "It's slow" | "What's the latency in milliseconds? Which endpoint?" |
| "It's broken" | "What error are you seeing? What behavior changed?" |
| "It's down" | "Are you getting errors or timeouts? What percentage?" |
| "It's acting weird" | "What's the expected behavior vs actual behavior?" |

### For Diving Deeper

| Situation | Follow-up Questions |
|-----------|-------------------|
| High latency found | "Is it network, compute, or I/O bound?" |
| Errors found | "Are they client errors or server errors?" |
| Resource spike | "Is it gradual (leak) or sudden (traffic)?" |
| Dependency slow | "Is it that service or its dependencies?" |

### For Validating Root Cause

| Before Acting | Ask |
|---------------|-----|
| Ready to restart | "What evidence shows restart will help?" |
| Ready to scale | "What evidence shows we need more capacity?" |
| Ready to rollback | "What evidence shows the new version caused this?" |
| Ready to change config | "What evidence shows config is wrong?" |

---

## Red Flags Checklist

### Stop and Re-examine If:

- [ ] You've been investigating for > 30 min without progress
- [ ] Your "root cause" doesn't explain all symptoms
- [ ] Fix didn't work as expected
- [ ] You're making assumptions without data
- [ ] You've only considered one hypothesis

### When to Escalate:

- [ ] Data loss risk
- [ ] Security incident possible
- [ ] Multiple services affected
- [ ] No progress after 1 hour
- [ ] Customer-facing SEV1 impact

---

## Post-Incident Questions

After every investigation, ask:

1. "Could we have detected this earlier?"
2. "What monitoring should we add?"
3. "What runbook should we create/update?"
4. "What made this hard to diagnose?"
5. "How do we prevent recurrence?"

