# Design Study Document Template

Copy this template when creating design study documents at:
`docs/design/{component}/YYYY-MM-DD-{study-topic}.md`

---

```markdown
# [Component]: [Study Topic]

**Date:** YYYY-MM-DD
**Status:** Draft | Review | Final
**Component:** {component path}
**Author:** Design Study Expert (AI-assisted)

## Executive Summary

[2-3 sentences: What was studied, key findings, critical actions needed]

## Scope

### Files Analyzed
- `path/to/file.rs` (lines X-Y) - [purpose]
- `path/to/other.rs` (lines X-Y) - [purpose]

### Dependencies
- Upstream: [what this component depends on]
- Downstream: [what depends on this component]

### Data Flow
[Diagram or description of inputs → processing → outputs]

---

## Security Analysis

### Findings

| Severity | Location | Issue | Recommendation |
|----------|----------|-------|----------------|
| CRITICAL | file:line | Description | Fix approach |
| HIGH | file:line | Description | Fix approach |
| MEDIUM | file:line | Description | Fix approach |

### Details
[Detailed explanation of each security finding with code evidence]

---

## Correctness Analysis

### Findings

| Severity | Location | Issue | Recommendation |
|----------|----------|-------|----------------|
| ... | ... | ... | ... |

### Race Conditions
[Analysis of concurrent access patterns]

### Edge Cases
[Identified edge cases and how they're handled]

### Data Integrity
[How data consistency is maintained]

---

## Performance Analysis

### Hot Paths
[Identified hot paths with evidence]

### Allocation Patterns
[Memory allocation analysis]

### Algorithmic Complexity
| Operation | Current | Optimal | Gap |
|-----------|---------|---------|-----|
| ... | O(n²) | O(n log n) | Fix needed |

### Benchmark Results
[If available, or recommendations for benchmarks needed]

---

## Scalability Analysis

### Current Limits
| Resource | Current Capacity | Evidence |
|----------|-----------------|----------|
| Memory | X GB before OOM | [how determined] |
| Throughput | X ops/sec | [how determined] |
| Data size | X records | [how determined] |

### Scaling Behavior
- **10x load:** [what happens]
- **100x load:** [what happens]
- **1000x load:** [what happens]

### Bottlenecks
[Identified bottlenecks with evidence]

---

## Maintainability Analysis

### Code Quality
- Clarity: [assessment]
- Abstractions: [assessment]
- Documentation: [assessment]

### Technical Debt
[Identified technical debt items]

### Extensibility
[How easy to extend for future requirements]

---

## Observability Analysis

### Metrics Coverage
| Aspect | Covered | Missing |
|--------|---------|---------|
| Latency | ✅/❌ | [what's missing] |
| Throughput | ✅/❌ | [what's missing] |
| Errors | ✅/❌ | [what's missing] |
| Saturation | ✅/❌ | [what's missing] |

### Logging Quality
- Structured logging: [yes/no]
- Log levels appropriate: [assessment]
- Context included: [assessment]
- Sensitive data exposure: [assessment]

### Tracing Integration
- Spans defined: [assessment]
- Context propagation: [assessment]
- Async boundaries: [assessment]

### Profiling Hooks
- CPU profiling: [available/missing]
- Memory profiling: [available/missing]
- Async profiling: [available/missing]

---

## Testing Analysis

### Coverage Correlation

| File | Lines | Covered | Gap |
|------|-------|---------|-----|
| file.rs | 100-200 | 67% | Lines 145-160 untested |

### Critical Untested Paths
1. [Path 1 - why critical]
2. [Path 2 - why critical]

### Test Quality Assessment
- Unit tests: [count, quality]
- Integration tests: [count, quality]
- E2E tests: [count, quality]
- Benchmark tests: [count, quality]

### Missing Test Cases
1. [Edge case 1]
2. [Error condition 1]
3. [Concurrent scenario 1]

---

## Industry Comparison

### Best-of-Breed Analysis

| Aspect | Our Approach | Industry Leader | Their Approach | Gap |
|--------|--------------|-----------------|----------------|-----|
| [Aspect 1] | [Ours] | RocksDB | [Theirs] | [Gap] |
| [Aspect 2] | [Ours] | ScyllaDB | [Theirs] | [Gap] |
| [Aspect 3] | [Ours] | ClickHouse | [Theirs] | [Gap] |

### Patterns We Should Adopt
1. [Pattern from X] - [why, expected benefit]
2. [Pattern from Y] - [why, expected benefit]

---

## 10x Improvement Opportunities

### Opportunity 1: [Name]
- **Current state:** [description]
- **Proposed change:** [description]
- **Expected improvement:** [quantified]
- **Evidence:** [from industry comparison or analysis]
- **Effort:** [Low/Medium/High]

### Opportunity 2: [Name]
[Same structure]

---

## Potential Bugs

| ID | Severity | Location | Description | Reproduction | Fix |
|----|----------|----------|-------------|--------------|-----|
| B1 | CRITICAL | file:line | [desc] | [steps] | [fix] |
| B2 | HIGH | file:line | [desc] | [steps] | [fix] |

---

## Recommended Actions

### Critical (Do Immediately)
1. [ ] [Action with file:line reference]
2. [ ] [Action with file:line reference]

### High (This Sprint)
1. [ ] [Action]
2. [ ] [Action]

### Medium (This Quarter)
1. [ ] [Action]
2. [ ] [Action]

### Low (Backlog)
1. [ ] [Action]

---

## Evidence Appendix

### Code Snippets
[Relevant code with annotations]

### Flame Graphs / Profiles
[If available]

### Benchmark Data
[If available]

### References
- [Link to relevant RocksDB code/doc]
- [Link to relevant paper]
- [Link to relevant discussion]
```
