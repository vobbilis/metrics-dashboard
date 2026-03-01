# K8s SRE Quick Reference

## QUICK REFERENCE: COMMON SCENARIOS

### Scenario: Pods Crashing Immediately

```bash
# Check exit code and logs
kubectl describe pod <pod> | grep -A 5 "State:"
kubectl logs <pod> --previous

# Common causes:
# - Exit code 1: Application error
# - Exit code 137: OOMKilled
# - Exit code 143: SIGTERM (graceful shutdown)
```

### Scenario: Pods Stuck in Pending

```bash
# Check why it can't schedule
kubectl describe pod <pod> | grep -A 10 "Events:"

# Common causes:
# - Insufficient CPU/memory on nodes
# - Node selector/affinity mismatch
# - PVC can't bind
# - Taint without toleration
```

### Scenario: Service Returns 503

```bash
# Check endpoints exist
kubectl get endpoints <service>

# Check pods are ready
kubectl get pods -l app=<app> | grep -v "Running\|1/1"

# Check readiness probe
kubectl describe pod <pod> | grep -A 5 "Readiness:"
```

### Scenario: High Latency

```bash
# Check resource pressure
kubectl top pods -n <namespace>

# Check for throttling
kubectl logs <pod> | grep -i "timeout\|slow"

# Check dependency latency
kubectl exec -it <pod> -- curl -w "@curl-format.txt" http://dependency
```

---

## OBSERVABILITY CHEAT SHEET

### Metrics to Always Check

| Metric | What It Shows | Prometheus Query |
|--------|---------------|------------------|
| Container Restarts | Stability | `kube_pod_container_status_restarts_total` |
| Memory Usage | Resource pressure | `container_memory_usage_bytes` |
| CPU Throttling | Performance | `container_cpu_cfs_throttled_seconds_total` |
| Request Latency | User experience | `histogram_quantile(0.99, http_request_duration_seconds_bucket)` |
| Error Rate | Reliability | `sum(rate(http_requests_total{status=~"5.."}[5m]))` |

### Grafana Dashboard Essentials

- Pod resource usage vs limits
- Container restart counts
- Request latency percentiles (p50, p90, p99)
- Error rates by endpoint
- Pod ready vs desired count

### Alert Queries That Matter

```promql
# Pods not running
kube_deployment_status_replicas_available < kube_deployment_spec_replicas

# High restart count
increase(kube_pod_container_status_restarts_total[1h]) > 5

# Memory near limit (>90%)
container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9

# High error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.01
```

---

## CONTAINER STATES REFERENCE

| State | Meaning | First Action |
|-------|---------|--------------|
| `Pending` | Can't schedule | Check events, node resources |
| `ContainerCreating` | Image pull or volume mount | Check events, image name |
| `CrashLoopBackOff` | Repeated crashes | Check logs --previous |
| `OOMKilled` | Out of memory | Increase memory limit |
| `Error` | Container exited non-zero | Check logs, exit code |
| `ImagePullBackOff` | Can't pull image | Check image name, registry auth |
| `Evicted` | Node pressure | Check node conditions |

---

## KUBECTL ALIASES FOR SRES

Add these to your `.bashrc` or `.zshrc`:

```bash
# Quick pod status
alias kgp='kubectl get pods'
alias kgpa='kubectl get pods -A'
alias kgpw='kubectl get pods -o wide'

# Quick logs
alias kl='kubectl logs'
alias klf='kubectl logs -f'
alias klp='kubectl logs --previous'

# Quick describe
alias kdp='kubectl describe pod'
alias kds='kubectl describe service'
alias kdd='kubectl describe deployment'

# Events sorted by time
alias kge='kubectl get events --sort-by=".lastTimestamp"'

# Resource usage
alias ktop='kubectl top pods'
alias ktopn='kubectl top nodes'

# Common namespace shortcuts
alias kn='kubectl -n'
alias kns='kubectl config set-context --current --namespace'
```

---

## EMERGENCY COMMANDS

```bash
# Emergency scale to zero (stop all traffic)
kubectl scale deployment/<app> --replicas=0 -n <namespace>

# Emergency rollback
kubectl rollout undo deployment/<app> -n <namespace>

# Emergency traffic shift (if using service mesh)
kubectl patch virtualservice <vs> --type merge -p '{"spec":{"http":[{"route":[{"destination":{"host":"backup-service"}}]}]}}'

# Cordon all nodes in a zone (multi-zone cluster)
kubectl get nodes -l topology.kubernetes.io/zone=us-east-1a -o name | xargs -I {} kubectl cordon {}

# Force delete stuck pod
kubectl delete pod <pod> --force --grace-period=0 -n <namespace>
```

---

## POSTMORTEM TEMPLATE

```markdown
# Incident Postmortem: [Brief Title]

## Summary
- **Date**: YYYY-MM-DD
- **Duration**: HH:MM
- **Severity**: SEV1/2/3/4
- **Impact**: X users affected, Y% error rate

## Timeline
| Time (UTC) | Event |
|------------|-------|
| 14:00 | First alert fired |
| 14:05 | Incident acknowledged |
| 14:15 | Root cause identified |
| 14:30 | Fix deployed |
| 14:35 | Service recovered |

## Root Cause
[What actually broke and why]

## Resolution
[What was done to fix it]

## Action Items
- [ ] Item 1 - Owner - Due date
- [ ] Item 2 - Owner - Due date

## Lessons Learned
- What went well
- What went poorly
- Where we got lucky
```
