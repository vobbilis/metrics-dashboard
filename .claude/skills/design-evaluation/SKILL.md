# Design Evaluation

Use when choosing between multiple design options, architectural alternatives, or implementation approaches. MANDATORY before committing to a design. FORBIDDEN is picking an option without evidence. REQUIRED is prototype-driven evaluation with quantified comparison.

## THE MANDATE

**Never commit to a design choice based on theory alone. Build lightweight POCs, measure, compare, then decide.**

---

## When This Skill Activates

- After brainstorming produces multiple options
- Before writing implementation plans
- When asked "which approach should we use?"
- When comparing technologies, libraries, or architectures
- When evaluating build vs. buy decisions

---

## The Evaluation Framework

### Phase 1: Define Evaluation Criteria

Before building anything, establish what matters:

```markdown
## Evaluation Criteria

| Criterion | Weight | How to Measure |
|-----------|--------|----------------|
| Latency (p99) | High | Benchmark under load |
| Implementation complexity | Medium | Lines of code, dependencies |
| Operational overhead | Medium | Deployment requirements |
| Cost at scale | Low | Estimate at 10x current |
| Team familiarity | Medium | Experience survey |
```

**Ask the user**: "What criteria matter most for this decision?"

### Phase 2: Design POC Scope

Each POC should be:
- **Minimal**: 1-2 hours max per option
- **Focused**: Test ONE critical aspect
- **Measurable**: Produce comparable numbers
- **Disposable**: Expect to throw away the code

```markdown
## POC Scope

### Option A: Redis + Pub/Sub
- [ ] Basic get/set operations
- [ ] Pub/sub message latency
- [ ] Connection pool behavior
- **Skip**: Full error handling, production config

### Option B: Local Cache + Gossip
- [ ] In-memory cache operations
- [ ] Gossip protocol message propagation
- [ ] Memory footprint per entry
- **Skip**: Persistence, complex eviction
```

### Phase 3: Build POCs

Create separate directories for each:

```
evaluation/
├── README.md           # Criteria, results, decision
├── option-a-redis/
│   ├── Cargo.toml
│   ├── src/main.rs
│   └── bench.sh
├── option-b-local/
│   ├── Cargo.toml
│   ├── src/main.rs
│   └── bench.sh
└── comparison/
    └── results.md
```

### Phase 4: Measure and Compare

Run equivalent benchmarks on each POC:

```markdown
## Results

| Metric | Option A (Redis) | Option B (Local) | Winner |
|--------|------------------|------------------|--------|
| p50 latency | 1.2ms | 0.05ms | B |
| p99 latency | 4.5ms | 0.2ms | B |
| Memory/instance | 50MB | 200MB | A |
| Cross-instance sync | <10ms | ~500ms | A |
| Lines of code | 150 | 400 | A |
| New dependencies | 2 | 5 | A |
```

### Phase 5: Make Decision with Evidence

```markdown
## Decision

**Chosen: Option A (Redis + Pub/Sub)**

### Rationale
- Cross-instance sync latency is critical for our real-time requirement
- 1.2ms p50 is acceptable given our 50ms latency budget
- Lower operational complexity outweighs local cache speed advantage

### Tradeoffs Accepted
- Higher latency than local cache (1.2ms vs 0.05ms)
- Network dependency (Redis must be available)

### Risks Mitigated
- Redis failure: Graceful degradation to no-cache mode
- Network latency: Connection pooling, local Redis in each AZ
```

---

## FORBIDDEN Patterns

### ❌ Choosing Based on Theory Alone

```markdown
// ❌ FORBIDDEN - No evidence
"Redis is industry standard, let's use that."

// ❌ FORBIDDEN - Opinion without data
"Local cache will be faster, obviously."

// ❌ FORBIDDEN - Premature commitment
"I've used X before, let's go with that."
```

### ❌ Skipping POC Because "We Know"

```markdown
// ❌ FORBIDDEN
"We don't need to prototype, the choice is obvious."

// ✅ REQUIRED
"Even though we're leaning toward X, let's spend 2 hours 
validating our assumptions with a quick POC."
```

### ❌ Comprehensive POCs

```markdown
// ❌ FORBIDDEN - Too much investment
- Full error handling
- Production-ready configuration
- Complete feature set
- Documentation

// ✅ REQUIRED - Minimal validation
- Happy path only
- Hardcoded config
- One critical feature
- Benchmark results
```

---

## REQUIRED Patterns

### ✅ Criteria Before Coding

```markdown
// ✅ REQUIRED - Define success first
"Before we build POCs, let's agree on:
1. What metrics matter?
2. What are the thresholds?
3. How will we measure?"
```

### ✅ Time-Boxed POCs

```markdown
// ✅ REQUIRED - Strict time limits
"Each POC gets 1-2 hours max. If we can't validate 
the critical path in that time, that's a signal."
```

### ✅ Quantified Comparison

```markdown
// ✅ REQUIRED - Numbers, not feelings
| Metric | Option A | Option B | Winner |
|--------|----------|----------|--------|
| Latency p99 | 4.5ms | 0.2ms | B |
| Memory | 50MB | 200MB | A |
```

### ✅ Document the Decision

```markdown
// ✅ REQUIRED - Future-proof the choice
## Decision Record

**Date**: 2026-01-15
**Decision**: Option A (Redis)
**Deciders**: @alice, @bob

**Context**: [Why we needed to choose]
**Options Considered**: [What we evaluated]
**POC Results**: [What we measured]
**Decision**: [What we chose and why]
**Tradeoffs**: [What we're accepting]
```

---

## Evaluation Templates

### Quick Comparison (< 1 hour)

For simple choices (library A vs B):

```markdown
## Quick Evaluation: [Topic]

### Options
1. **Option A**: [One-line description]
2. **Option B**: [One-line description]

### Key Criterion
[The ONE thing that matters most]

### 15-Minute Test Each
- Option A: [Result]
- Option B: [Result]

### Decision
[Choice] because [evidence-based reason]
```

### Standard Evaluation (2-4 hours)

For architectural choices:

```markdown
## Evaluation: [Topic]

### Context
[Why this decision matters]

### Options
1. **Option A**: [Description, pros, cons]
2. **Option B**: [Description, pros, cons]
3. **Option C**: [Description, pros, cons]

### Evaluation Criteria
| Criterion | Weight | Measurement |
|-----------|--------|-------------|
| ... | ... | ... |

### POC Results
[Benchmark data, comparison table]

### Decision
**Chosen**: [Option]
**Rationale**: [Evidence-based reasoning]
**Tradeoffs**: [What we're accepting]
```

### Deep Evaluation (1-2 days)

For major architectural decisions:

```markdown
## Architecture Decision Record: [Topic]

### Status
[Proposed | Accepted | Deprecated | Superseded]

### Context
[Detailed background, constraints, requirements]

### Options Considered
[Full analysis of each option]

### POC Implementation
[Links to POC code, benchmark methodology]

### Results
[Comprehensive comparison data]

### Decision
[Detailed rationale with evidence]

### Consequences
[Positive and negative impacts]

### Review Date
[When to revisit this decision]
```

---

## Workflow Integration

This skill sits between brainstorming and planning:

```
┌─────────────────┐
│  Brainstorming  │  ← Explore options
└────────┬────────┘
         ▼
┌─────────────────┐
│ Design Eval POC │  ← THIS SKILL: Build, measure, compare
└────────┬────────┘
         ▼
┌─────────────────┐
│  Writing Plans  │  ← Plan the chosen option
└────────┬────────┘
         ▼
┌─────────────────┐
│ Executing Plans │  ← Implement
└─────────────────┘
```

---

## Checklist

Before committing to a design:

- [ ] Criteria defined and weighted
- [ ] POC scope is minimal (1-2 hours each)
- [ ] Each option has comparable benchmark
- [ ] Results documented in comparison table
- [ ] Decision includes rationale AND tradeoffs
- [ ] Decision record created for future reference

---

## Enforcement

This skill is MANDATORY:

- **FORBIDDEN**: Choosing an option without building POCs
- **FORBIDDEN**: POCs that take more than 2 hours each
- **FORBIDDEN**: Decisions without quantified comparison
- **REQUIRED**: Evaluation criteria before coding
- **REQUIRED**: Comparison table with measurements
- **REQUIRED**: Decision record documenting the choice
