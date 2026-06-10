---
name: rust-db-architect
description: Use when designing database internals, storage engines, query execution, indexing strategies, or high-performance systems in Rust. MANDATORY for architecture decisions involving data structures, memory layout, concurrency, or performance optimization. FORBIDDEN is designing without benchmarks or evidence. REQUIRED is phased implementation with quantified tradeoffs.
---

# Rust Database Architect

## THE MANDATE

**Every architectural decision must be backed by evidence, benchmarks, and quantified tradeoffs.**

You are designing systems that handle millions of operations per second. Intuition is not enough. Measure everything.

---

## WHEN TO USE THIS SKILL

This skill is MANDATORY for:

- Storage engine design (MemTables, WAL, Parquet, LSM trees)
- Query engine architecture (DataFusion, execution plans)
- Indexing strategies (Sparse, Bloom, Inverted, FST)
- Memory layout decisions (Arrow, column stores)
- Concurrency patterns (sharding, lock-free, actors)
- Performance optimization (write path, read path)
- Multi-tenancy and isolation
- Compression and encoding strategies

---

## THE ARCHITECTURE DECISION FRAMEWORK

Every significant decision follows this structure:

```
┌─────────────────────────────────────────────────────────────┐
│  1. PROBLEM STATEMENT                                       │
│     What are we solving? What's the current bottleneck?     │
│         ↓                                                   │
│  2. QUANTIFIED ANALYSIS                                     │
│     Measure the problem. Show the numbers.                  │
│         ↓                                                   │
│  3. ALTERNATIVES EVALUATION                                 │
│     Compare options with concrete tradeoffs                 │
│         ↓                                                   │
│  4. IMPLEMENTATION BLUEPRINT                                │
│     Phased plan with verification at each step              │
│         ↓                                                   │
│  5. EVIDENCE OF SUCCESS                                     │
│     Benchmarks proving the solution works                   │
└─────────────────────────────────────────────────────────────┘
```

---

## DOCUMENTATION STANDARDS

### Comparison Tables Are Mandatory

Every design decision needs a comparison table:

```markdown
| Metric | Option A | Option B | Option C |
|--------|----------|----------|----------|
| Memory | 4 GB | 16 GB | 20+ GB |
| Lookup | O(1) | O(log n) | O(n) |
| Write throughput | 1M/s | 500K/s | 100K/s |
| Complexity | Low | Medium | High |
```

### Quantified Tradeoffs

```markdown
| Approach | Columns | Row Size | 10M rows |
|----------|---------|----------|----------|
| **Wide Schema** (Prometheus) | 200+ | ~2KB | ~20 GB |
| **Three-Column** (NexusDB) | 4 | 28 bytes | ~280 MB |

**~70x storage reduction** for high-cardinality label sets.
```

### Architecture Diagrams (ASCII)

```
┌─────────────────────────────────────────────────────────────┐
│  SERIES INDEX (Two-Tier Lookup)                             │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────┐                             │
│  │   ACTIVE TIER (Mutable)    │                             │
│  │   Arc<RwLock<HashMap>>     │                             │
│  │   - Recent series (< 100k) │                             │
│  └────────────────────────────┘                             │
│              │ overflow                                     │
│              ▼                                              │
│  ┌────────────────────────────┐                             │
│  │   FROZEN TIER (Immutable)  │                             │
│  │   FST (memory-mapped)      │                             │
│  │   - Historical (millions)  │                             │
│  └────────────────────────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

---

## FORBIDDEN PATTERNS

### ❌ Design Without Measurement - BANNED

```markdown
❌ FORBIDDEN:
"I think using a HashMap will be fast enough"
"This should handle our load"
"Memory usage won't be a problem"

✅ REQUIRED:
"HashMap: 4 bytes/entry × 1B entries = 4 GB RAM"
"Measured: 178,556 writes/sec baseline"
"Target: 1,000,000 writes/sec (5.6x improvement needed)"
```

### ❌ Single-Option Design - BANNED

```markdown
❌ FORBIDDEN:
"We'll use RocksDB for storage"

✅ REQUIRED:
"Three options analyzed:

| Option | Throughput | Memory | Complexity |
|--------|------------|--------|------------|
| RocksDB | 500K/s | 8 GB | Low (existing) |
| Custom LSM | 1M/s | 4 GB | High |
| Arrow MemTable | 2M/s | 6 GB | Medium |

Recommendation: Arrow MemTable because [quantified reasoning]"
```

### ❌ Vague Performance Claims - BANNED

```markdown
❌ FORBIDDEN:
"This is faster"
"Significant improvement"
"Better performance"

✅ REQUIRED:
"6.0x improvement: 178,556/s → 1,069,268/s"
"P99 latency: 140µs (down from 2.3ms)"
"Memory: 280 MB vs 20 GB (70x reduction)"
```

---

## REQUIRED PATTERNS

### Evidence-Based Architecture

```markdown
## Implementation Evidence Summary

| Component | Module | Status | Key Files |
|-----------|--------|--------|-----------|
| **Storage Engine** | `storage/` | ✅ | `memtable.rs`, `wal.rs` |
| **Query Engine** | `query/` | ✅ | `engine.rs`, `planner.rs` |
| **Sparse Index** | `storage/` | ✅ | `sparse_index.rs` |

### Performance Verification

| Metric | Baseline | After | Improvement |
|--------|----------|-------|-------------|
| Write Throughput | 178K/s | 1.07M/s | **6.0x** ✅ |
| Query Latency | 50ms | 7.6ms | **6.6x** ✅ |
```

### Phased Implementation Plans

```markdown
## Phase 19: Write Path Optimization

**Status:** ✅ COMPLETE  
**Goal:** Restore 1,000,000 writes/sec  
**Result:** 1,069,268 samples/sec achieved

### Optimizations Implemented

| ID | Optimization | Impact |
|----|--------------|--------|
| H1 | Async HLL Background Worker | -82% hot path time |
| H2 | Schema Memoization Cache | O(52) → O(1) checks |
| H3 | O(1) Batch-Level Sharding | Eliminates O(n) scan |
```

### Before/After Architecture Diagrams

```markdown
### Before (Synchronous - Blocking)

┌─────────────────────────────────────────────────────────┐
│  Ingest Thread                                          │
│  ┌─────────┐   ┌────────────────┐   ┌────────────────┐ │
│  │ Decode  │ → │ Normalize SYNC │ → │ WAL + MemTable │ │
│  │         │   │ (82% of time!) │   │                │ │
│  └─────────┘   └────────────────┘   └────────────────┘ │
└─────────────────────────────────────────────────────────┘

### After (Asynchronous - Zero-Copy)

┌─────────────────────────────────────────────────────────┐
│  Ingest Thread (Fast Path)                              │
│  ┌─────────┐   ┌────────────────┐   ┌────────────────┐ │
│  │ Decode  │ → │ Schema Cache   │ → │ O(1) Teleport  │ │
│  │         │   │ O(1) lookup    │   │ to shard       │ │
│  └─────────┘   └────────┬───────┘   └────────────────┘ │
│                         │ async (1/64 sampled)         │
└─────────────────────────┼──────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Background Worker (Dedicated Thread)                   │
│  crossbeam_channel → HLL observe (non-blocking)         │
└─────────────────────────────────────────────────────────┘
```

---

## TIERED STORAGE ARCHITECTURE TEMPLATE

For databases with hot/warm/cold tiers:

```markdown
## Storage Tiers

| Tier | Storage | Latency | Data Age | Memory Efficiency |
|------|---------|---------|----------|-------------------|
| **Hot** | MemTable (Arrow) | µs | 0-15 min | ~29 bytes/row |
| **Warm** | MemTable (Parquet) | µs | 15m-4h | ~3 bytes/row |
| **Cold** | Parquet (SSD) | ms | 4h+ | ~3 bytes/row |

### Key Innovation
The **Warm Tier** keeps data in memory but compresses it into 
Parquet format. This reduces memory usage by **~10x**, allowing 
significantly longer in-memory retention.
```

---

## INDEXING STRATEGY TEMPLATE

```markdown
## Index Hierarchy

| Level | Index Type | Purpose | Complexity |
|-------|------------|---------|------------|
| L0 | Sparse Primary | Granule pruning | O(1) lookup |
| L1 | Time B+ Tree | Time range queries | O(log n) |
| L2 | Inverted (Roaring) | Label→SeriesID | O(1) + bitmap AND |
| L3 | Bloom Filter | Existence check | O(1), false positives |

### Query Execution Flow

1. **L2**: Inverted index → Get candidate SeriesIDs
2. **L3**: Bloom filter → Skip files that don't contain series
3. **L1**: Time index → Prune to relevant time range
4. **L0**: Sparse index → Jump to exact granules
5. **Scan**: Read only required row groups
```

---

## RUST-SPECIFIC PATTERNS

### Memory Layout Decisions

```rust
// BEFORE: Wide schema (200+ columns)
Schema::new(vec![
    Field::new("timestamp", Int64, false),
    Field::new("value", Float64, false),
    Field::new("label_1", Utf8, true),     // String!
    Field::new("label_2", Utf8, true),     // String!
    // ... 198 more label columns
])
// Problem: 2KB per row, 20 GB for 10M rows

// AFTER: Three-column model
Schema::new(vec![
    Field::new("timestamp", Int64, false),   // 8 bytes
    Field::new("series_id", UInt64, false),  // 8 bytes (hash)
    Field::new("value", Float64, false),     // 8 bytes
])
// Result: 28 bytes per row, 280 MB for 10M rows (70x reduction)
```

### Concurrency Patterns

```rust
// ❌ FORBIDDEN: Single lock contention point
pub struct Index {
    data: RwLock<HashMap<String, u64>>,  // All threads fight for this
}

// ✅ REQUIRED: Sharded for concurrency
pub struct ShardedIndex {
    shards: [RwLock<HashMap<String, u64>>; 64],  // 64x less contention
}

impl ShardedIndex {
    fn get_shard(&self, key: &str) -> usize {
        // Consistent hashing to distribute load
        let hash = fxhash::hash64(key);
        (hash % 64) as usize
    }
}
```

### Zero-Copy Patterns

```rust
// ❌ FORBIDDEN: Copying data on hot path
fn process_batch(batch: RecordBatch) -> Result<RecordBatch> {
    let mut new_cols = vec![];
    for col in batch.columns() {
        new_cols.push(col.clone());  // COPY!
    }
    RecordBatch::try_new(batch.schema(), new_cols)
}

// ✅ REQUIRED: Zero-copy with Arc
fn process_batch(batch: RecordBatch) -> Result<RecordBatch> {
    // Schema cache lookup - Arc pointer comparison
    let schema_ptr = Arc::as_ptr(&batch.schema()) as usize;
    if let Some(cached) = self.cache.get(&schema_ptr) {
        return Ok(batch.clone());  // Arc::clone = pointer copy only
    }
    // ... only normalize if not cached
}
```

---

## DECISION RECORD TEMPLATE

```markdown
# Architecture Decision Record: [Title]

## 1. Context
[What problem are we solving? Current state?]

## 2. Alternatives

### Option A: [Name]
- **Pros**: [List]
- **Cons**: [List]
- **Performance**: [Benchmarks if available]

### Option B: [Name]
...

### Option C: [Name] (SELECTED)
...

## 3. Decision

**Selected**: Option C

**Rationale**:
1. [Quantified reason 1]
2. [Quantified reason 2]
3. [Quantified reason 3]

## 4. Consequences

- [Positive consequence]
- [Negative consequence / tradeoff]
- [Migration path if needed]

## 5. Verification Plan

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Throughput | >1M/s | Benchmark suite |
| Memory | <4 GB | `htop` under load |
| Latency P99 | <10ms | Histogram metrics |
```

---

## PHASE PLANNING TEMPLATE

```markdown
# Phase N: [Name]

**Status:** Planning | In Progress | ✅ COMPLETE  
**Risk Level:** LOW | MEDIUM | HIGH  
**Estimated LOC:** ~X,XXX across Y files

## Executive Summary

[2-3 sentences: What are we building and why?]

## Performance Targets

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| Write throughput | 178K/s | 1M/s | Async HLL |
| Read latency | 50ms | <10ms | Index pruning |

## Implementation Tasks

### Task 1: [Name]
- **Files**: `src/storage/xxx.rs`
- **Changes**: [Specific description]
- **Verification**: [How to test]

### Task 2: [Name]
...

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk 1] | HIGH | [Mitigation strategy] |

## Rollback Plan

1. [Step to undo if needed]
2. [Step to undo if needed]
```

---

## ENFORCEMENT

This skill is MANDATORY for architecture work:

- **FORBIDDEN**: Design without benchmarks
- **FORBIDDEN**: Single-option proposals
- **FORBIDDEN**: Vague performance claims
- **REQUIRED**: Comparison tables for decisions
- **REQUIRED**: Quantified tradeoffs (bytes, ops/sec, latency)
- **REQUIRED**: Before/After architecture diagrams
- **REQUIRED**: Phased implementation with verification
- **REQUIRED**: Evidence of success (benchmark results)

**Architecture is not art. It's engineering. Show the numbers.**

---

## Related Skills

- **writing-plans** - For implementation plans
- **systematic-debugging** - When performance doesn't meet targets
- **test-driven-development** - Benchmarks are tests
