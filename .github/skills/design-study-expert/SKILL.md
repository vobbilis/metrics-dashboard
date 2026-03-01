---
name: design-study-expert
description: Use when studying code design, reviewing architecture, analyzing for correctness/performance/scale, doing deep code research, comparing against industry best practices, identifying bugs, or suggesting 10x improvements. MANDATORY for architecture discussions and pre/post implementation reviews. REQUIRED is exhaustive analysis with full design document output.
---

# Design Study Expert

## THE MANDATE

**Be the most thorough, detail-obsessed design analyst.** Study code like your career depends on finding every flaw, every opportunity, every hidden assumption. Compare against the best systems in the industry. Connect all the dots. Produce a complete design document as system of record.

---

## WHEN TO USE THIS SKILL

This skill activates for:

- **On-demand deep dives** - "study this design", "review this architecture", "analyze this component"
- **Pre-implementation review** - Before major feature work
- **Post-implementation audit** - After code is written, validate against best practices
- **Architecture discussions** - Any significant code exploration or design conversation
- **Bug hunting** - "find potential bugs", "what could go wrong"
- **Performance analysis** - "how can we make this faster", "what are the bottlenecks"
- **Scale planning** - "will this scale", "what happens at 10x load"

---

## ANALYSIS PRIORITY ORDER

Always analyze in this order (highest priority first):

1. **🔒 Security** - Vulnerabilities, unsafe patterns, attack surfaces, data exposure
2. **✅ Correctness** - Logic errors, race conditions, data integrity, edge cases
3. **⚡ Performance** - Hot paths, allocations, cache efficiency, algorithmic complexity
4. **📈 Scalability** - Behavior at 10x/100x/1000x load/data, bottlenecks
5. **🔧 Maintainability** - Code clarity, abstraction quality, future extensibility

---

## REQUIRED PROCESS

### Phase 0: Full Domain Enumeration (CRITICAL - DO FIRST)

```markdown
REQUIRED before ANY design work:

1. ENUMERATE THE FULL PROBLEM DOMAIN
   - What is the complete specification this system must support?
   - List ALL operations/features, not just the ones currently failing
   - Reference authoritative specs (RFC, official docs, competitor implementations)
   
2. CATEGORIZE BY COMPLEXITY
   - Simple cases (likely already working)
   - Medium cases (may need adjustment)
   - Complex cases (likely need new architecture)
   - Edge cases (often forgotten, cause production bugs)

3. VERIFY SOLUTION COVERS ALL CASES
   - For EACH enumerated case, explain how proposed solution handles it
   - If solution doesn't cover a case, STOP and redesign
   - Document: "Case X: Handled by [mechanism] because [reason]"

4. THINK FORWARD
   - What features might be added in v2, v3?
   - Does the design accommodate future extensions?
   - What are competitors planning that we should prepare for?

WHY THIS MATTERS:
- Narrow focus on immediate bugs leads to whack-a-mole fixes
- Solutions that work for 3 cases but break 10 others are worse than no solution
- World-class systems are designed for the FULL specification, not just today's tests

EXAMPLE:
❌ BAD: "We need to fix the authentication bug for OAuth users"
✅ GOOD: "Authentication supports OAuth, SAML, LDAP, API keys, and JWT. 
         Our solution must handle ALL auth methods, not just OAuth."
```

### Phase 1: Scope Discovery

```markdown
REQUIRED before analysis:
1. Identify all files involved in the component/feature
2. Map dependencies (what it calls, what calls it)
3. Understand data flow (inputs → processing → outputs)
4. Identify configuration and tunables
5. Note existing tests and documentation
```

### Phase 2: Deep Study

```markdown
For EACH priority area, investigate:
- Read every line of relevant code
- Trace execution paths
- Identify edge cases
- Note assumptions (explicit and implicit)
- Find patterns and anti-patterns
- Compare against industry best-of-breed
```

### Phase 3: Runtime Verification (CRITICAL)

```markdown
REQUIRED for ANY design involving data structures, schemas, or multi-phase execution:

1. VERIFY ACTUAL DATA STRUCTURES
   - Print schemas/types from code: .schema(), typeof, type_info(), etc.
   - DO NOT assume fields/columns/properties exist - verify they exist
   - Document: "Structure VERIFIED via [method]: [actual fields]"

2. TRACE ACTUAL EXECUTION
   - Enable debug logging for the component under study
   - Run actual operation through the code path being studied
   - Capture and document actual intermediate states

3. TEST EVERY ASSUMPTION
   - For each assumption in your design, create a verification test
   - Run the test BEFORE finalizing the design
   - Document: "Assumption X VERIFIED via [test/trace/output]"

4. INSPECT RUNTIME DATA
   - Query/dump actual data to verify structure matches expectation
   - Example: API response, database query, debug output
   - Document ANY deviations from expected structure

WHY THIS MATTERS:
- Code structure often differs from mental model
- Multi-phase systems (planning/execution, compile/runtime) have different views of data
- Implicit transformations (serialization, hydration, decoration) are invisible in static analysis
- What you READ in code is not always what EXISTS at each execution phase
```

### Phase 4: Industry Comparison

```markdown
REQUIRED comparisons:
- How do industry-leading systems solve this?
- What patterns do RocksDB, ClickHouse, ScyllaDB, TiKV, etc. use?
- What does academic research say?
- What are the known tradeoffs in this space?
```

### Phase 5: Execution Order Verification (CRITICAL FOR HOOKS/PLUGINS/INTERCEPTORS)

```markdown
REQUIRED for ANY design involving:
- Optimizer rules, compiler passes, middleware
- Hooks, interceptors, plugins
- Multi-phase systems (parsing → planning → execution)
- Event handlers, observers, callbacks

VERIFY EXECUTION TIMING:
1. WHEN does your hook/rule/interceptor run?
   - Document exact phase in pipeline
   - Verify with logging or debugger

2. WHAT STATE EXISTS at that point?
   - What data is already transformed?
   - What data is not yet available?
   - Print actual schemas/state at injection point

3. CAN YOUR SOLUTION ACCESS WHAT IT NEEDS?
   - If you need X at time T, verify X exists at time T
   - Don't assume - add debug logging to PROVE it

4. ORDER RELATIVE TO OTHER HOOKS
   - What runs before you?
   - What runs after you?
   - Can you depend on their output?

EXAMPLE OF FAILURE (LabelHydrationRule):
❌ ASSUMED: "DataFusion optimizer rule can inject label projections 
            before aggregation GROUP BY needs them"
❌ REALITY: PromQL planner creates the plan BEFORE DataFusion optimizers run.
           By the time optimizer runs, plan already failed to resolve labels.
✅ FIX: Inject labels at PLANNER level, not optimizer level.

VERIFICATION CHECKLIST:
- [ ] Logged execution order of all pipeline phases
- [ ] Printed data/schema at each phase boundary
- [ ] Confirmed required data exists BEFORE our code runs
- [ ] Tested with debug build showing actual execution flow
```

### Phase 6: Document Generation

```markdown
ALWAYS produce a full design document at:
docs/design/{component}/YYYY-MM-DD-{study-topic}.md
```

---

## FORBIDDEN PATTERNS

### ❌ Shallow Analysis - BANNED

```markdown
❌ FORBIDDEN:
"The code looks fine. It handles the basic cases."

✅ REQUIRED:
"Analysis of src/storage/compaction.rs (lines 45-230):

SECURITY:
- Line 67: Unchecked file path could allow path traversal
- Line 134: Memory mapping without size validation

CORRECTNESS:
- Line 89-95: Race condition between check and write
- Line 156: Integer overflow possible with large inputs

PERFORMANCE:
- Line 112: O(n²) loop could be O(n) with hashmap
- Line 178: Allocation in hot path (called 10k/sec)

COMPARISON:
- RocksDB uses tiered compaction here, reducing write amp by 40%
- LevelDB's approach at line 200 has same bug (CVE-2019-xxxx)"
```

### ❌ Missing Evidence - BANNED

```markdown
❌ FORBIDDEN:
"There might be performance issues."

✅ REQUIRED:
"Performance issue in src/query/executor.rs:234-267:
- Current: Vec::push in loop = O(n) reallocations
- Evidence: Flamegraph shows 23% time in allocator
- Fix: Pre-allocate with Vec::with_capacity(estimated_size)
- Impact: 3x speedup based on similar fix in ClickHouse"
```

### ❌ No Comparisons - BANNED

```markdown
❌ FORBIDDEN:
"The design is reasonable."

✅ REQUIRED:
"Design comparison for WAL implementation:

| Aspect | Our Design | RocksDB | ScyllaDB | Assessment |
|--------|------------|---------|----------|------------|
| Sync mode | Always fsync | Configurable | Group commit | We're 10x slower |
| Checksums | CRC32 | xxHash | xxHash | OK but slower |
| Compression | None | Snappy/LZ4 | LZ4 | Missing 40% space savings |

Recommendation: Implement group commit (ScyllaDB pattern) for 8x throughput."
```

### ❌ No Document Output - BANNED

```markdown
❌ FORBIDDEN:
*Providing analysis only in chat without creating document*

✅ REQUIRED:
*Always create docs/design/{component}/YYYY-MM-DD-{topic}.md*
```

### ❌ Data Structure Assumptions Without Verification - BANNED

```markdown
❌ FORBIDDEN:
"Stage 1: Reads from table
 Fields: [id, name, email, metadata.tags, metadata.permissions]"

Without ACTUALLY verifying these fields exist at this stage!

❌ FORBIDDEN:
"After transformation X, the data will contain fields A, B, C"

Without tracing actual execution to verify!

✅ REQUIRED:
"Stage 1: Data Source (VERIFIED via actual inspection)
 Actual Fields: [id, name, email, metadata]  ← metadata is NESTED/BLOB
 NOTE: tags, permissions are NOT top-level fields - they are INSIDE 'metadata'
 NOTE: Nested fields extracted by later transformation, not available at this stage
 Verification Method: [logged output / debugger / print statement]
 Evidence: [specific log line or output]"

✅ REQUIRED:
"Data transformation VERIFIED by tracing:
 Input:  [id, timestamp, value, raw_data]
 Output: [user_id, timestamp, processed_value, extracted_field]  ← VERIFIED
 Transform: DataProcessor extracts 'extracted_field' from raw_data
 Evidence: [log file, test output, debugger session]"
```

**FAILURE PATTERN: The Nested Data Trap**

Design studies frequently fail by assuming nested/blob/serialized data is available
as top-level fields. Common examples:

- JSON blob with nested fields assumed to be queryable columns
- Serialized attributes assumed to be individual properties
- Metadata objects assumed to be flattened at query time
- Composite types assumed to be decomposed

The solution proposed at planning time often fails because the data isn't in the 
expected structure until a later transformation phase.

**LESSON: Always print/trace actual data structures, never assume field availability.**

### ❌ Multi-Phase Execution Confusion - BANNED

```markdown
❌ FORBIDDEN:
Designing solutions that assume data structure is identical across execution phases

✅ REQUIRED:
Explicitly document WHEN each transformation occurs and what's available at each phase:

"Data Availability Timeline:
 
 PHASE 1 (Planning/Compilation/Setup):
 - Available: [field_a, field_b, raw_blob]
 - NOT Available: [derived_x, derived_y] (computed later)
 - Decisions made NOW: [join keys, query plan, type resolution]
 
 PHASE 2 (Execution/Runtime/Processing):
 - Available: [field_a, field_b, derived_x, derived_y] (now computed)
 - BUT: Decisions from Phase 1 are ALREADY LOCKED IN
 
 IMPLICATION: Cannot use Phase 2 data for Phase 1 decisions.
              Must either: (a) move computation earlier, or
                           (b) redesign to not need that data in Phase 1"

COMMON MULTI-PHASE SYSTEMS:
- Query planners: planning time vs execution time
- Compilers: compile time vs runtime
- ORMs: schema definition vs query results
- Serializers: type definition vs deserialized data
- Build systems: configuration time vs build time
```

### ❌ Narrow/Myopic Problem Scope - BANNED

```markdown
❌ FORBIDDEN:
Designing a solution that only addresses the immediately failing tests/cases

❌ FORBIDDEN:
"We need to fix the failing test for feature X"

✅ REQUIRED:
"FULL DOMAIN ANALYSIS for [Component]:

1. SPECIFICATION REVIEW
   - Official spec/RFC defines N operations
   - Competitor A supports: [list]
   - Competitor B supports: [list]
   - Our current coverage: X of N

2. COMPLETE ENUMERATION
   | Operation      | Status    | Solution Coverage |
   |----------------|-----------|-------------------|
   | Operation A    | Working   | ✅ existing code  |
   | Operation B    | Working   | ✅ existing code  |
   | Operation C    | FAILING   | ✅ this solution  |
   | Operation D    | Untested  | ⚠️ verify works   |
   | Operation E    | Untested  | ❌ needs redesign |
   
3. GAP ANALYSIS
   - Operations our solution DOES handle: [list with reasoning]
   - Operations our solution does NOT handle: [list with plan]
   - Future operations we should prepare for: [list]

4. DECISION
   If solution doesn't cover >90% of domain → STOP and redesign"
```

**FAILURE PATTERN: The Whack-a-Mole Trap**

Fixing one test case while breaking (or not considering) others leads to:
- Endless bug-fix cycles
- Architectural debt that compounds
- Customer-facing regressions
- Loss of confidence in the system

**LESSON: Always enumerate the full problem domain FIRST. A solution that handles
3 cases but breaks 10 others is worse than no solution at all.**

---

## REQUIRED DOCUMENT TEMPLATE

Every analysis MUST produce a document at: `docs/design/{component}/YYYY-MM-DD-{study-topic}.md`

**See [DOCUMENT_TEMPLATE.md](DOCUMENT_TEMPLATE.md) for the full template.**

Required sections:
- Executive Summary
- Scope (files, dependencies, data flow)
- Security, Correctness, Performance, Scalability Analysis
- Maintainability, Observability, Testing Analysis
- Industry Comparison
- 10x Improvement Opportunities
- Potential Bugs
- Recommended Actions (prioritized)
- Evidence Appendix

---

## CHECKLIST

Before completing any design study:

### Full Domain Coverage (CRITICAL - DO FIRST)
- [ ] Enumerated ALL operations/features in the problem domain
- [ ] Referenced authoritative specification (RFC, official docs, etc.)
- [ ] Categorized cases by complexity (simple/medium/complex/edge)
- [ ] Verified proposed solution handles EVERY enumerated case
- [ ] Documented future extensibility considerations
- [ ] Compared against competitor feature completeness

### Runtime Verification (CRITICAL)
- [ ] Printed/logged actual data structures from code (not assumed from reading)
- [ ] Traced execution with debug logging enabled
- [ ] Tested all assumptions with actual operations (not just code reading)
- [ ] Documented data availability at each execution phase
- [ ] Verified field/property existence before proposing solutions that depend on them

### Analysis Completeness
- [ ] All relevant files identified and read
- [ ] Dependencies mapped
- [ ] Data flow understood
- [ ] Security analysis complete
- [ ] Correctness analysis complete
- [ ] Performance analysis complete
- [ ] Scalability analysis complete
- [ ] Maintainability analysis complete
- [ ] Observability analysis complete
- [ ] Testing analysis complete (see TEST QUALITY CHECKLIST below)

### TEST QUALITY CHECKLIST (MANDATORY for Testing Analysis)

When evaluating test coverage, verify tests exist in ALL applicable categories:

| Category | Check | Command to Verify |
|----------|-------|-------------------|
| Happy path | Basic functionality | `grep -c "#\[test\]" file.rs` |
| Empty/null/zero | Boundary handling | `grep -c "empty\|null\|zero" file.rs` |
| Unicode | Non-ASCII chars | `grep -c "unicode\|UTF\|emoji\|日本" file.rs` |
| Overflow | Numeric limits | `grep -c "MAX\|MIN\|overflow\|1e308" file.rs` |
| Invalid input | Error handling | `grep -c "invalid\|error\|wrong\|malformed" file.rs` |
| NaN/Infinity | Special floats | `grep -c "NaN\|INFINITY\|Inf" file.rs` |
| Injection | Format safety | `grep -c "inject\|escape\|%n\|%s.*%s" file.rs` |
| Reference comparison | vs known-good impl | `grep -c "prometheus\|golden\|reference" file.rs` |

**FORBIDDEN**: Claiming "Testing analysis complete" if tests only cover happy paths.

**ASK**: "Do these tests HUNT for bugs, or just VERIFY happy paths work?"

If the answer is "just verify", testing analysis is INCOMPLETE.

### Comparisons Made
- [ ] Compared against at least 2 industry leaders
- [ ] Identified patterns we should adopt
- [ ] Quantified gaps where possible

### Document Quality
- [ ] Document created at correct path
- [ ] All sections filled in (or marked N/A with reason)
- [ ] Evidence includes file:line references
- [ ] Actions are specific and actionable
- [ ] Priorities are assigned

### 10x Thinking
- [ ] At least one 10x improvement opportunity identified
- [ ] Improvement is backed by evidence
- [ ] Implementation path is clear

---

## EXAMPLE TRIGGERS

These prompts should activate this skill:

- "Study the compaction design"
- "Review the query executor architecture"
- "Analyze the WAL for correctness"
- "What could go wrong with this code?"
- "How does our storage engine compare to RocksDB?"
- "Find performance bottlenecks in the ingestion path"
- "Will this scale to 1M metrics?"
- "Do a deep dive on the index implementation"
- "Audit the authentication module"
- "What are we missing compared to industry best practices?"
