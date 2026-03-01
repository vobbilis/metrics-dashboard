---
name: data-contract-validation
description: Use when building multi-component systems where one component produces data another consumes. MANDATORY for producer-consumer architectures, cross-language data exchange, schema/protocol boundaries. FORBIDDEN is deploying without contract validation. REQUIRED is explicit enumeration of producer outputs and consumer expectations with automated diff verification.
---

# Data Contract Validation

## THE MANDATE

**Never deploy a producer without validating its contract against all consumers.**

When system A produces data and system B consumes it, there is an implicit contract. This contract MUST be:
1. Explicitly documented
2. Automatically validated
3. Enforced at build time

---

## WHEN TO USE THIS SKILL

**Always use when:**
- Building data producers (simulators, generators, scrapers, APIs)
- Building data consumers (dashboards, validators, processors, UIs)
- Cross-language boundaries (Rust → Python, Go → TypeScript)
- Protocol boundaries (Protobuf, JSON Schema, OpenAPI)
- Database schema changes
- Metric/telemetry systems (Prometheus, OpenTelemetry)
- Event-driven architectures (Kafka, RabbitMQ)

**Trigger phrases:**
- "simulator", "generator", "producer"
- "dashboard", "consumer", "validator"
- "metrics", "labels", "schema"
- "cross-language", "Rust and Python"
- "protocol", "contract", "interface"

---

## THE CONTRACT VALIDATION PROCESS

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: ENUMERATE PRODUCER OUTPUTS                        │
│  List EVERY field, metric, label, column the producer emits │
│         ↓                                                   │
│  PHASE 2: ENUMERATE CONSUMER EXPECTATIONS                   │
│  List EVERY field, metric, label the consumer requires      │
│         ↓                                                   │
│  PHASE 3: DIFF AND VALIDATE                                 │
│  Compare producer vs consumer - FAIL on mismatch            │
│         ↓                                                   │
│  PHASE 4: INTEGRATION TEST                                  │
│  Run real data through full pipeline - verify end-to-end    │
└─────────────────────────────────────────────────────────────┘
```

---

## PHASE 1: ENUMERATE PRODUCER OUTPUTS

**Extract EVERY piece of data the producer generates:**

```markdown
## Producer Contract: [Component Name]

### Metrics/Fields Produced:
| Name | Type | Labels/Columns | Example Value |
|------|------|----------------|---------------|
| http_requests_total | counter | method, status, route | 1523 |
| container_cpu_usage | gauge | pod, namespace, node | 0.45 |

### Labels/Attributes Produced:
| Label Name | Possible Values | Required |
|------------|-----------------|----------|
| cluster | prod-east, prod-west | yes |
| namespace | default, kube-system, ... | yes |
| resource | cpu, memory | yes (for resource metrics) |

### Data Format:
- Protocol: Prometheus Remote Write / JSON / Protobuf
- Encoding: Snappy compressed
- Timestamp: Unix milliseconds
```

**For code extraction:**
```bash
# Rust: Find all metric names
grep -oE '"[a-z_]+_[a-z_]+"' src/producer.rs | sort -u

# Python: Find all metric references
grep -oE '(container|node|kube|http)[a-z_]+' scripts/consumer.py | sort -u
```

---

## PHASE 2: ENUMERATE CONSUMER EXPECTATIONS

**Extract EVERY piece of data the consumer expects:**

```markdown
## Consumer Contract: [Component Name]

### Metrics/Fields Required:
| Name | Used In | Query/Usage |
|------|---------|-------------|
| http_requests_total | Traffic Dashboard | rate(http_requests_total{...}[5m]) |
| container_cpu_usage | CPU Panel | sum by (pod) |

### Labels Required:
| Label Name | Used In | Filter Expression |
|------------|---------|-------------------|
| cluster | All dashboards | cluster=~"$cluster" |
| resource | CPU/Memory | resource="cpu" or resource="memory" |

### Special Requirements:
- Histograms need _bucket, _count, _sum suffixes
- Resource metrics need resource label for filtering
- Phase metrics need phase label (Running, Pending, etc.)
```

---

## PHASE 3: DIFF AND VALIDATE

**Automated contract validation:**

```python
#!/usr/bin/env python3
"""Contract validation script - run before deployment."""

def validate_contract(producer_metrics: set, consumer_metrics: set,
                      producer_labels: dict, consumer_labels: dict) -> bool:
    """
    Validate producer outputs match consumer expectations.
    Returns False if contract is violated.
    """
    errors = []
    
    # Check metrics
    missing_metrics = consumer_metrics - producer_metrics
    if missing_metrics:
        errors.append(f"MISSING METRICS: {missing_metrics}")
    
    # Check labels for each metric
    for metric, required_labels in consumer_labels.items():
        if metric in producer_labels:
            missing_labels = required_labels - producer_labels[metric]
            if missing_labels:
                errors.append(f"MISSING LABELS on {metric}: {missing_labels}")
        else:
            errors.append(f"METRIC {metric} not in producer")
    
    if errors:
        print("❌ CONTRACT VALIDATION FAILED:")
        for e in errors:
            print(f"   - {e}")
        return False
    
    print("✅ Contract validation passed")
    return True
```

**CLI command pattern:**
```bash
# Generate and compare contracts
./scripts/extract_producer_contract.sh > producer_contract.json
./scripts/extract_consumer_contract.sh > consumer_contract.json
./scripts/validate_contract.py producer_contract.json consumer_contract.json
```

---

## PHASE 4: INTEGRATION TEST

**Real data through full pipeline:**

```markdown
## Integration Test Checklist

- [ ] Start producer (simulator/generator)
- [ ] Inject data into system
- [ ] Run consumer queries
- [ ] Verify queries return expected data shape
- [ ] Verify NO empty results (unless expected)
- [ ] Verify label values match expected patterns
```

**Example integration test:**
```python
def test_end_to_end_contract():
    """E2E test: producer data matches consumer expectations."""
    # 1. Producer injects data
    simulator.run(duration="5m", metrics=ALL_METRICS)
    
    # 2. Consumer queries data
    for query in DASHBOARD_QUERIES:
        result = prometheus.query(query)
        
        # 3. Validate result
        assert result.status == "success", f"Query failed: {query}"
        assert len(result.data) > 0, f"Empty result for: {query}"
```

---

## FORBIDDEN PATTERNS

### ❌ Assuming Contract Matches - BANNED

```markdown
❌ FORBIDDEN:
"The simulator generates metrics, the dashboard queries them, it should work."

✅ REQUIRED:
"I enumerated 50 metrics from the simulator and 47 from dashboards.
 3 dashboard metrics are missing from simulator: [list].
 Here's the fix..."
```

### ❌ Testing Only Happy Path - BANNED

```markdown
❌ FORBIDDEN:
"The query works with test data."

✅ REQUIRED:
"I verified ALL dashboard queries return data:
 - 72 queries tested
 - 72 returned results
 - 0 empty results
 - Contract validated"
```

### ❌ Manual Inspection Only - BANNED

```markdown
❌ FORBIDDEN:
"I looked at the code and the metrics match."

✅ REQUIRED:
"I ran automated contract extraction:
 $ ./scripts/validate_contract.py
 ✅ 50/50 metrics validated
 ✅ 127/127 labels validated"
```

### ❌ Different Sources of Truth - BANNED

```markdown
❌ FORBIDDEN:
- Rust: const METRICS = ["cpu_usage", "mem_usage"]
- Python: METRICS = ["cpu_usage", "memory_usage"]  # Different name!

✅ REQUIRED:
- Single source of truth (config.py or schema.json)
- Auto-generate constants for all languages
- Or: Shared protobuf/schema definition
```

---

## CHECKLIST BEFORE DECLARING COMPLETE

```markdown
## Contract Validation Checklist

### Enumeration
- [ ] Listed ALL producer outputs (metrics, fields, columns)
- [ ] Listed ALL producer labels/attributes with possible values
- [ ] Listed ALL consumer requirements (queries, filters)
- [ ] Listed ALL consumer label expectations

### Validation
- [ ] Ran automated contract diff
- [ ] Zero missing metrics
- [ ] Zero missing labels
- [ ] All label values are valid

### Integration
- [ ] Ran real data through pipeline
- [ ] ALL consumer queries return data
- [ ] No unexpected empty results
- [ ] Timestamp alignment verified

### Documentation
- [ ] Contract documented in shared location
- [ ] Breaking changes require version bump
- [ ] Consumer updated before producer changes
```

---

## METRICS/TELEMETRY SPECIFIC PATTERNS

For Prometheus/OpenTelemetry metrics specifically:

### Label Completeness Matrix

```markdown
| Metric | cluster | namespace | node | pod | resource | phase | condition |
|--------|---------|-----------|------|-----|----------|-------|-----------|
| container_cpu_usage | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| kube_pod_status_phase | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ |
| kube_node_status_condition | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
```

### Common Missing Labels

| Metric Type | Often Missing | Fix |
|-------------|---------------|-----|
| Resource requests/limits | `resource` (cpu/memory) | Split into 2 series per resource type |
| Pod status | `phase` (Running/Pending) | Add phase label with valid values |
| Node conditions | `condition`, `status` | Add both labels |
| Container termination | `reason` (OOMKilled/Error) | Add reason label |

---

## SINGLE SOURCE OF TRUTH PATTERN

**Best practice: One config file generates all constants**

```
┌─────────────────────────────────────────┐
│  config/metrics_contract.yaml           │
│  (Single source of truth)               │
└──────────────────┬──────────────────────┘
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Rust     │ │ Python   │ │ TypeScript│
│ constants│ │ constants│ │ constants │
└──────────┘ └──────────┘ └──────────┘
```

**Example contract YAML:**
```yaml
# config/metrics_contract.yaml
metrics:
  - name: kube_pod_container_resource_requests
    type: gauge
    labels:
      required: [cluster, namespace, pod, resource]
      resource_values: [cpu, memory]
    
  - name: kube_pod_status_phase
    type: gauge
    labels:
      required: [cluster, namespace, pod, phase]
      phase_values: [Running, Pending, Succeeded, Failed, Unknown]
```

---

## QUICK REFERENCE

```bash
# Extract metrics from Rust
grep -hoE '(container|node|kube|http|machine)[a-zA-Z_]+' src/*.rs | sort -u

# Extract metrics from Python dashboards
grep -hoE '(container|node|kube|http|machine)[a-z_]+' scripts/**/*.py | sort -u

# Find metrics in consumer but not producer
comm -23 <(sort consumer_metrics.txt) <(sort producer_metrics.txt)

# Validate contract
./scripts/validate_contract.py --producer rust --consumer python
```

---

## REMEMBER

> "A contract violation discovered in production costs 100x more than one caught at build time."

Every producer-consumer boundary is a potential failure point. Validate explicitly. Test with real data. Never assume.
