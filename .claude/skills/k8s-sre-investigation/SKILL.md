---
name: k8s-sre-investigation
description: Use when investigating ANY cloud-native application issue in Kubernetes - performance degradation, availability problems, pod crashes, network issues, resource exhaustion, or service latency. MANDATORY for SRE troubleshooting. FORBIDDEN is guessing, restarting pods without diagnosis, or ignoring metrics. REQUIRED is the 5-phase process - triage, observe, correlate, diagnose, remediate.
---

# Kubernetes SRE Investigation

## THE MANDATE

**Do not guess. Do not restart pods hoping it helps. Do not blame "the cloud."**

When an application has issues in Kubernetes:
1. Triage severity and scope
2. Observe current state with kubectl and metrics
3. Correlate events, logs, and metrics
4. Diagnose root cause with evidence
5. Remediate with targeted fix

**Restarting without understanding WHY will only delay the next incident.**

---

## THE SRE MINDSET

You are the last line of defense. Your job is:
- **Reduce MTTR** (Mean Time To Recovery)
- **Prevent recurrence** (fix root cause, not symptoms)
- **Preserve evidence** (capture before restart)
- **Communicate status** (keep stakeholders informed)

```markdown
❌ PANICKED SRE:
"Pods are crashing!" → kubectl delete pod → "Fixed!"
→ 10 min later: Same crash → Delete again → "It's flaky"
→ Rinse repeat for hours

✅ SYSTEMATIC SRE:
"Pods are crashing!" → Check events → Check logs → OOMKilled!
→ Check memory requests → Under-provisioned → Fix limits
→ Deploy → Verified stable → Write postmortem
```

---

## FORBIDDEN PATTERNS

### ❌ Restart Without Diagnosis - BANNED

```bash
# ❌ FORBIDDEN - Deleting pods without investigation
kubectl delete pod my-app-xyz --force

# ❌ FORBIDDEN - Rolling restart as "fix"
kubectl rollout restart deployment/my-app

# ✅ REQUIRED - Investigate FIRST
kubectl describe pod my-app-xyz
kubectl logs my-app-xyz --previous
kubectl get events --field-selector involvedObject.name=my-app-xyz
```

### ❌ Ignoring Resource Metrics - BANNED

```markdown
❌ "App is slow" → Check code → Blame developers
✅ "App is slow" → Check CPU/memory metrics → Pod throttled at 95% CPU → Scale up
```

### ❌ Guessing Network Issues - BANNED

```bash
# ❌ FORBIDDEN - Assuming network is broken
"The service can't reach the database" → Change network policies

# ✅ REQUIRED - Verify connectivity first
kubectl exec -it my-pod -- curl -v http://database:5432
kubectl get endpoints my-service
kubectl get networkpolicy -A
```

### ❌ Ignoring Previous Container Logs - BANNED

```bash
# ❌ FORBIDDEN - Only checking current logs
kubectl logs my-pod

# ✅ REQUIRED - Check previous crash
kubectl logs my-pod --previous
kubectl logs my-pod -c init-container  # Check init containers too
```

### ❌ Changing Multiple Things At Once - BANNED

```markdown
❌ FORBIDDEN:
- Increase memory limit
- Add readiness probe
- Change image version
- All in one commit

✅ REQUIRED:
- One change at a time
- Verify each change's impact
- Roll back if no improvement
```

---

## THE 5-PHASE INVESTIGATION PROCESS

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: TRIAGE                                                │
│  What's broken? Who's affected? How urgent?                     │
│         ↓                                                       │
│  PHASE 2: OBSERVE                                               │
│  Current state: pods, events, logs, metrics                     │
│         ↓                                                       │
│  PHASE 3: CORRELATE                                             │
│  Timeline: What changed? When did it start?                     │
│         ↓                                                       │
│  PHASE 4: DIAGNOSE                                              │
│  Root cause: WHY is it failing? (Not just WHAT)                 │
│         ↓                                                       │
│  PHASE 5: REMEDIATE                                             │
│  Fix root cause. Verify. Prevent recurrence.                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## PHASE 1: TRIAGE

### Severity Assessment

| Severity | Criteria | Response |
|----------|----------|----------|
| **SEV1** | Complete outage, data loss risk | All hands, incident commander |
| **SEV2** | Major degradation, 50%+ users affected | Immediate investigation |
| **SEV3** | Partial impact, workaround exists | Investigate during business hours |
| **SEV4** | Minor issue, cosmetic | Backlog |

### Scope Assessment

```bash
# How many pods affected?
kubectl get pods -l app=my-app | grep -v Running

# How many namespaces?
kubectl get pods -A | grep -v Running | head -20

# Is it cluster-wide or localized?
kubectl get nodes
kubectl top nodes
```

### First Questions

- [ ] What service/app is affected?
- [ ] When did it start?
- [ ] What's the blast radius?
- [ ] Is there a recent deployment?
- [ ] Are other teams affected?

---

## PHASE 2: OBSERVE

### The Observation Order (USE THIS EVERY TIME)

```bash
# 1. Pod Status
kubectl get pods -n <namespace> -l app=<app> -o wide

# 2. Pod Details (for any non-Running pod)
kubectl describe pod <pod-name> -n <namespace>

# 3. Events (cluster-wide view of recent issues)
kubectl get events -n <namespace> --sort-by='.lastTimestamp' | tail -30

# 4. Logs (current container)
kubectl logs <pod-name> -n <namespace> --tail=100

# 5. Logs (previous crash)
kubectl logs <pod-name> -n <namespace> --previous --tail=100

# 6. Resource Usage
kubectl top pods -n <namespace>
kubectl top nodes
```

### Container States Cheat Sheet

| State | Meaning | First Action |
|-------|---------|--------------|
| `Pending` | Can't schedule | Check events, node resources |
| `ContainerCreating` | Image pull or volume mount | Check events, image name |
| `CrashLoopBackOff` | Repeated crashes | Check logs --previous |
| `OOMKilled` | Out of memory | Increase memory limit |
| `Error` | Container exited non-zero | Check logs, exit code |
| `ImagePullBackOff` | Can't pull image | Check image name, registry auth |
| `Evicted` | Node pressure | Check node conditions |

### Resource Observation Commands

```bash
# Memory/CPU pressure on nodes
kubectl describe nodes | grep -A 5 "Conditions:"

# Actual vs requested resources
kubectl top pods -n <namespace>
kubectl get pods -n <namespace> -o json | jq '.items[].spec.containers[].resources'

# PVC status
kubectl get pvc -n <namespace>

# Service endpoints
kubectl get endpoints <service-name> -n <namespace>
```

---

## PHASE 3: CORRELATE

### Build the Timeline

```markdown
## Timeline Template

| Time | Event | Source |
|------|-------|--------|
| 14:00 | Deployment rolled out | GitOps/ArgoCD |
| 14:02 | First pod crash | kubectl events |
| 14:05 | Memory spike observed | Prometheus |
| 14:07 | Alerts fired | PagerDuty |
```

### Correlation Commands

```bash
# Recent deployments
kubectl rollout history deployment/<app> -n <namespace>

# Deployment events
kubectl describe deployment <app> -n <namespace> | grep -A 20 "Events:"

# Check if recent config change
kubectl get configmap <config> -n <namespace> -o yaml | head -20

# Check for recent secret rotation
kubectl get secret <secret> -n <namespace> -o yaml | grep -i "last"

# Git commits in timeframe (if GitOps)
git log --since="2 hours ago" --oneline
```

### What Changed? (THE KEY QUESTION)

- [ ] New deployment/image version?
- [ ] Config change (ConfigMap, Secret)?
- [ ] Infrastructure change (node pool, network)?
- [ ] Traffic pattern change (load spike)?
- [ ] Dependency outage (database, external API)?
- [ ] Kubernetes upgrade?
- [ ] Certificate expiration?

---

## PHASE 4: DIAGNOSE

### Common Root Causes

#### 1. Resource Exhaustion

```bash
# Symptoms: OOMKilled, throttling, slow response
# Diagnosis:
kubectl top pods -n <namespace>
kubectl describe pod <pod> | grep -A 10 "Limits:"

# Evidence pattern:
# - Memory usage near limit
# - CPU throttling (check container_cpu_cfs_throttled_seconds_total)
# - Pods evicted
```

#### 2. Networking Issues

```bash
# Symptoms: Connection refused, timeouts, DNS failures
# Diagnosis:
kubectl exec -it <pod> -- nslookup <service>
kubectl exec -it <pod> -- curl -v <endpoint>
kubectl get endpoints <service>
kubectl get networkpolicy -n <namespace>

# Evidence pattern:
# - Empty endpoints (no ready pods)
# - NetworkPolicy blocking traffic
# - DNS resolution failing
```

#### 3. Image/Registry Issues

```bash
# Symptoms: ImagePullBackOff, ErrImagePull
# Diagnosis:
kubectl describe pod <pod> | grep -A 5 "Events:"
kubectl get secret <image-pull-secret> -o yaml

# Evidence pattern:
# - 401/403 from registry
# - Image not found
# - Secret expired or missing
```

#### 4. Storage Issues

```bash
# Symptoms: Pod stuck in Pending, volume mount failures
# Diagnosis:
kubectl get pvc -n <namespace>
kubectl describe pvc <pvc-name>
kubectl get pv

# Evidence pattern:
# - PVC stuck in Pending
# - StorageClass not found
# - Volume already attached to another node
```

#### 5. Application Bugs

```bash
# Symptoms: Crash after startup, specific error in logs
# Diagnosis:
kubectl logs <pod> --previous | grep -i "error\|exception\|panic"
kubectl exec -it <pod> -- env  # Check environment variables

# Evidence pattern:
# - Stack trace in logs
# - Missing config/secrets
# - Incompatible dependency version
```

### Root Cause Verification

**Before declaring root cause, verify:**

- [ ] Can you reproduce the issue?
- [ ] Does fixing this specific thing resolve it?
- [ ] Is there supporting evidence in logs/metrics?
- [ ] Does the timeline match?

---

## PHASE 5: REMEDIATE

### Remediation Hierarchy

1. **Immediate** - Stop the bleeding (scale, traffic shift)
2. **Short-term** - Fix the symptom (increase limits, restart)
3. **Long-term** - Fix root cause (code fix, architecture change)

### Safe Remediation Commands

```bash
# Scale up (more replicas, same config)
kubectl scale deployment <app> --replicas=5 -n <namespace>

# Rollback to previous version
kubectl rollout undo deployment/<app> -n <namespace>

# Rolling restart (when all else fails)
kubectl rollout restart deployment/<app> -n <namespace>

# Cordon a bad node (stop new pods)
kubectl cordon <node-name>

# Drain a node (move all pods off)
kubectl drain <node-name> --ignore-daemonsets
```

### Before ANY Remediation

```markdown
## Pre-Remediation Checklist

- [ ] Captured logs from affected pods
- [ ] Captured describe output
- [ ] Captured events
- [ ] Noted current replica count
- [ ] Noted current image version
- [ ] Informed stakeholders of planned action
```

### Post-Remediation Verification

```bash
# Verify pods running
kubectl get pods -n <namespace> -l app=<app> -w

# Verify endpoints healthy
kubectl get endpoints <service> -n <namespace>

# Verify metrics recovering
# (Check your observability platform)

# Verify no new errors in logs
kubectl logs -f deployment/<app> -n <namespace> --tail=10
```

---

## OBSERVABILITY INTEGRATION

### Key Metrics

| Metric | Prometheus Query |
|--------|------------------|
| Container Restarts | `kube_pod_container_status_restarts_total` |
| Memory Usage | `container_memory_usage_bytes` |
| CPU Throttling | `container_cpu_cfs_throttled_seconds_total` |
| Request Latency | `histogram_quantile(0.99, http_request_duration_seconds_bucket)` |
| Error Rate | `sum(rate(http_requests_total{status=~"5.."}[5m]))` |

See [quick-reference.md](quick-reference.md) for Grafana dashboards, alert queries, and more.

---

## INCIDENT CHECKLIST

### When Pager Goes Off

- [ ] Acknowledge alert
- [ ] Open incident channel/ticket
- [ ] Assess severity and scope
- [ ] Communicate initial status
- [ ] Begin Phase 2: Observe

### During Investigation

- [ ] Keep stakeholders updated (every 15 min for SEV1/2)
- [ ] Document findings in incident ticket
- [ ] Capture evidence before any fix
- [ ] Get approval for risky remediations

### After Resolution

- [ ] Verify service recovered
- [ ] Update incident with resolution
- [ ] Schedule postmortem (for SEV1/2)
- [ ] Create follow-up tickets for long-term fixes

---

## QUICK REFERENCE

For common scenarios (crashing pods, pending pods, 503 errors, high latency), observability cheat sheets, kubectl aliases, emergency commands, and postmortem templates, see [quick-reference.md](quick-reference.md).

---

## VERIFICATION CHECKLIST

Before declaring "fixed":

- [ ] All pods in Running state with correct ready count
- [ ] No new errors in logs for 5+ minutes
- [ ] Metrics show normal values
- [ ] Latency returned to baseline
- [ ] Error rate at normal levels
- [ ] No pending alerts
- [ ] Stakeholders notified of resolution

---

## REMEMBER

1. **Evidence first, changes second** - Never remediate without diagnosis
2. **Preserve before restart** - Logs and events disappear on restart
3. **One change at a time** - Otherwise you won't know what fixed it
4. **Communicate constantly** - Stakeholders need updates
5. **Document everything** - Future you will thank present you
