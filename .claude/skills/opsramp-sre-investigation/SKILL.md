---
name: opsramp-sre-investigation
description: Use when investigating performance degradation, availability issues, or service health problems using OpsRamp Observability. MANDATORY for SRE investigations with OpsRamp tooling. FORBIDDEN is jumping to conclusions, ignoring metrics context, or making changes without evidence. REQUIRED is the Socratic investigation method - ask probing questions, gather evidence, validate hypotheses systematically.
---

# OpsRamp SRE Investigation with Socratic Method

## THE MANDATE

**You are an SRE using OpsRamp Observability. Your role is to investigate, not guess.**

When investigating cloud-native application issues:
1. **ASK** - Use Socratic questioning to understand the problem
2. **OBSERVE** - Gather metrics, traces, logs from OpsRamp
3. **HYPOTHESIZE** - Form theories based on evidence
4. **VALIDATE** - Test each hypothesis with data
5. **ACT** - Remediate only with proven root cause

**The Socratic method means you guide yourself (and others) to the truth through deliberate questioning, not assumptions.**

---

## THE SOCRATIC SRE MINDSET

### What is Socratic Investigation?

Instead of: "The service is slow, let's restart it"

Ask: 
- "What does 'slow' mean? What's the latency?"
- "When did it start being slow?"
- "What was the latency before?"
- "What changed around that time?"
- "Which component is contributing most to latency?"

**Each answer leads to a more specific question until root cause emerges.**

```markdown
❌ REACTIVE SRE:
"Service is down!" → Restart pods → "Fixed!"
→ Happens again tomorrow → "Must be a bug"

✅ SOCRATIC SRE:
"Service is down!" 
→ Q: "What does 'down' mean - 503s? Timeouts? Connection refused?"
→ A: "503 errors"
→ Q: "What's returning 503 - the app or the load balancer?"
→ A: "The app pods"
→ Q: "Are pods running? What's their state?"
→ A: "CrashLoopBackOff"
→ Q: "What do the logs say? What's the exit code?"
→ A: "OOMKilled"
→ Q: "What's the memory limit vs actual usage?"
→ ROOT CAUSE: Memory limit too low for current traffic
```

---

## FORBIDDEN PATTERNS

### ❌ Jumping to Conclusions - BANNED

```markdown
❌ FORBIDDEN:
"CPU is high" → "Must be a memory leak"
"Latency increased" → "Database must be slow"
"Pods restarting" → "Must be a code bug"

✅ REQUIRED - Ask why:
"CPU is high" → Q: "Which process? Since when? What workload changed?"
"Latency increased" → Q: "Which endpoint? P50 or P99? At what time?"
"Pods restarting" → Q: "Exit code? Previous logs? Resource limits?"
```

### ❌ Ignoring OpsRamp's Full Context - BANNED

```markdown
❌ FORBIDDEN:
- Looking at one metric in isolation
- Ignoring correlated alerts
- Not checking topology/dependencies
- Missing the service map

✅ REQUIRED:
- Use OpsRamp's service topology to understand dependencies
- Check correlated metrics and alerts
- Review the full incident timeline
- Examine upstream and downstream services
```

### ❌ Making Changes Without Baseline - BANNED

```markdown
❌ FORBIDDEN:
- "Let's increase memory" (without knowing current usage)
- "Let's rollback" (without confirming it's version-related)

✅ REQUIRED: Always establish baseline first with Socratic questions.
```

---

## THE SOCRATIC INVESTIGATION FRAMEWORK

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: DEFINE THE PROBLEM                                    │
│  What EXACTLY is wrong? (Not assumptions)                       │
│         ↓                                                       │
│  PHASE 2: GATHER EVIDENCE                                       │
│  What does OpsRamp tell us?                                     │
│         ↓                                                       │
│  PHASE 3: FORM HYPOTHESES                                       │
│  What COULD explain this evidence?                              │
│         ↓                                                       │
│  PHASE 4: TEST HYPOTHESES                                       │
│  Which hypothesis does the data support?                        │
│         ↓                                                       │
│  PHASE 5: REMEDIATE WITH CONFIDENCE                             │
│  Fix the PROVEN root cause                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## PHASE 1: DEFINE THE PROBLEM (Socratic Questions)

**Goal: Convert vague symptoms into precise problem statements.**

### The Defining Questions

| Vague Report | Socratic Questions |
|--------------|-------------------|
| "It's slow" | What's the latency? Which endpoint? P50/P99? Since when? |
| "It's down" | What error? 5xx? Timeout? DNS? Which percentage of requests? |
| "It's broken" | What behavior changed? What's expected vs actual? |
| "Users complaining" | How many users? Which geography? Which feature? |

### Problem Definition Template

```markdown
## Problem Statement

- **Symptom**: [Exact observable behavior]
- **Impact**: [Who/what is affected, how severely]
- **Timeline**: [When it started, any patterns]
- **Scope**: [Which services, regions, user segments]

## NOT Assumed Yet

- Root cause
- Which component is at fault
- Whether it's code, config, or infrastructure
```

### Example Socratic Dialog

```markdown
Report: "The checkout service is slow"

Q: "How slow? What's the current P99 latency?"
A: "2.5 seconds"

Q: "What's normal for checkout P99?"
A: "Usually 400ms"

Q: "When did it increase to 2.5s?"
A: "About 2 hours ago"

Q: "What happened 2 hours ago? Any deployments, traffic changes?"
A: "There was a deployment at 14:00"

Q: "What was deployed? Which services?"
A: "New version of payment-service"

DEFINED PROBLEM: Checkout latency increased from 400ms to 2.5s (P99) 
starting 2 hours ago, correlating with payment-service deployment.
```

---

## PHASE 2: GATHER EVIDENCE (OpsRamp Observability)

### OpsRamp Evidence Collection Order

#### 1. Service Health Dashboard

```markdown
Questions to answer from OpsRamp:
- What's the current health score?
- Which SLIs are breached?
- What's the error rate trend?
- What's the latency distribution?
```

#### 2. Service Topology Map

```markdown
Questions to answer:
- What are this service's dependencies?
- Which upstream services call it?
- Are any dependencies showing degradation?
- Is the issue isolated or propagating?
```

#### 3. Metrics Analysis

```markdown
## Key Metrics to Check (OpsRamp)

### Performance Metrics
- Request latency (P50, P95, P99)
- Request rate (RPM/RPS)
- Error rate (4xx, 5xx)
- Throughput

### Resource Metrics
- CPU utilization (% of limit)
- Memory utilization (% of limit)
- Network I/O
- Disk I/O (for stateful services)

### Kubernetes Metrics
- Pod restart count
- Container state
- Resource requests vs actual
- HPA status
```

#### 4. Distributed Traces

```markdown
Questions to answer from traces:
- Where is time being spent?
- Which span has highest latency?
- Are there error spans?
- What's the trace breakdown?
```

#### 5. Logs Analysis

```markdown
Questions to answer from logs:
- Any error messages?
- Any warning patterns?
- What happened just before the issue?
- Any correlation with metric spikes?
```

### Evidence Collection Checklist

- [ ] Captured current health score from OpsRamp
- [ ] Reviewed service topology for affected path
- [ ] Exported relevant metric graphs (with baseline)
- [ ] Pulled sample traces showing the issue
- [ ] Searched logs for error patterns
- [ ] Noted all timestamps

---

## PHASE 3: FORM HYPOTHESES

**Rule: Never have just ONE hypothesis. Always consider multiple possibilities.**

### Hypothesis Generation Questions

For every symptom, ask:
- "What else could cause this?"
- "If this hypothesis is wrong, what would I see instead?"
- "What evidence would prove this hypothesis?"
- "What evidence would disprove it?"

### Hypothesis Template

```markdown
## Hypothesis 1: [Short description]

**Theory**: [What you think is happening]

**Supporting evidence**:
- [Evidence point 1]
- [Evidence point 2]

**Evidence needed to confirm**:
- [What would prove this]

**Evidence that would disprove**:
- [What would rule this out]

## Hypothesis 2: [Alternative]

**Theory**: [Different explanation]
...
```

### Example: Multiple Hypotheses

```markdown
Symptom: Checkout latency increased after deployment

## Hypothesis 1: Code regression in payment-service
- Theory: New code has performance bug
- Supporting: Timing correlates with deployment
- To confirm: Check if rollback fixes it
- Disproves: If other services also slow

## Hypothesis 2: Database connection pool exhaustion  
- Theory: New code uses more DB connections
- Supporting: Payment-service uses DB
- To confirm: Check connection pool metrics
- Disproves: If pool shows normal usage

## Hypothesis 3: Downstream service degradation
- Theory: External payment provider is slow
- Supporting: Payment calls external API
- To confirm: Check external API latency in traces
- Disproves: If external calls are fast
```

---

## PHASE 4: TEST HYPOTHESES

### Testing Methodology

```markdown
For each hypothesis:
1. Identify the specific metric/data that proves/disproves
2. Query OpsRamp for that data
3. Compare against baseline
4. Document finding
5. Update hypothesis status
```

### OpsRamp Queries for Testing

#### Testing Resource Hypothesis

```markdown
Q: "Is the service resource-constrained?"

OpsRamp checks:
- Container CPU: Is it near limit? Throttling?
- Container Memory: Is it near limit? OOM risk?
- Compare current vs 24h average
- Check HPA events
```

#### Testing Network Hypothesis

```markdown
Q: "Is there network latency or packet loss?"

OpsRamp checks:
- Inter-service latency in topology
- TCP retransmits
- DNS resolution time
- Connection errors
```

#### Testing Dependency Hypothesis

```markdown
Q: "Is a dependency causing the slowdown?"

OpsRamp checks:
- Distributed trace breakdown
- Dependency latency in service map
- Downstream service health scores
- Database query latency
```

### Hypothesis Testing Checklist

- [ ] Each hypothesis has clear pass/fail criteria
- [ ] Queried OpsRamp for relevant data
- [ ] Compared against baseline (not just current)
- [ ] Documented which hypotheses ruled out
- [ ] Identified winning hypothesis with evidence

---

## PHASE 5: REMEDIATE WITH CONFIDENCE

### Pre-Remediation Questions (Socratic)

Before ANY action, ask:
- "What specific root cause am I fixing?"
- "What evidence supports this is the cause?"
- "What will success look like?"
- "How will I verify it worked?"
- "What's the rollback plan?"

### Remediation Types by Root Cause

| Root Cause | Remediation | OpsRamp Verification |
|------------|-------------|---------------------|
| Resource exhaustion | Increase limits/replicas | Watch CPU/Memory return to normal |
| Code regression | Rollback deployment | Watch latency/error rate recover |
| Dependency failure | Failover/circuit breaker | Watch dependency health improve |
| Configuration error | Fix config, restart | Watch application metrics stabilize |
| Traffic spike | Scale out | Watch request queue clear |

### Post-Remediation Verification (OpsRamp)

```markdown
## Verification Checklist

Monitor in OpsRamp for 10+ minutes:

- [ ] Service health score returning to green
- [ ] Latency P99 back to baseline
- [ ] Error rate back to baseline
- [ ] No new alerts firing
- [ ] Dependent services stable
- [ ] No repeat of original symptom
```

---

## OPSRAMP-SPECIFIC INVESTIGATION PATTERNS

### Using OpsRamp Alerts

```markdown
When alert fires:

1. DON'T immediately look at the alerting metric
2. DO check the alert context:
   - What other alerts fired around the same time?
   - What's the alert history for this service?
   - What's the correlation in OpsRamp?
   
3. Ask: "Is this alert the cause or a symptom?"
```

### Using OpsRamp Service Maps

```markdown
Service map investigation:

1. Find the affected service
2. Check health of all connected services
3. Follow the RED indicators:
   - Rate: Is traffic unusual?
   - Errors: Which direction has errors?
   - Duration: Where is latency high?
   
4. Ask: "Which edge in this graph is degraded?"
```

### Using OpsRamp AI Insights

```markdown
When OpsRamp provides AI-suggested root cause:

1. DON'T blindly accept it
2. DO use it as a hypothesis
3. Ask: "What evidence supports this suggestion?"
4. Validate with the same rigor as your own hypothesis
```

---

## INVESTIGATION CHECKLIST

- [ ] Defined the problem precisely (not vaguely)
- [ ] Established timeline and baseline metrics
- [ ] Formed multiple hypotheses (never just one)
- [ ] Tested each with OpsRamp data
- [ ] Root cause confirmed with evidence
- [ ] Rollback plan ready before remediation
- [ ] Verified fix in OpsRamp for 10+ minutes
- [ ] Documented findings and follow-ups

---

## REMEMBER: THE SOCRATIC PRINCIPLE

**"I know that I know nothing"** - Socrates

Approach every investigation with intellectual humility:
- Your first guess is probably wrong
- The obvious answer is often incomplete
- Ask one more question before acting
- Let the data guide you, not your assumptions

**The best SREs ask the best questions.**

