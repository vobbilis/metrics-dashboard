---
name: nexus-db-guardrails
description: NexusDB project-specific guardrails, patterns, and lessons learned. Use when working on NexusDB (Rust TSDB) to avoid known pitfalls. Covers API wiring, Lance/feature-flag requirements, schema conventions, test patterns, and hard-won debugging knowledge. Triggers include any work in the nexus-db repository.
---

# NexusDB Project Guardrails

## PURPOSE

Project-specific rules for NexusDB — a Rust time-series database with Arrow/DataFusion, WAL, sharded memtables, and Parquet storage. These rules encode hard-won lessons from real failures.

---

## ARCHITECTURE QUICK REFERENCE

| Concept | Detail |
|---------|--------|
| Schema | `canonical_schema()`: timestamp(i64), value(f64), series_id(u64), tenant_id(u32), attributes(List<Struct<key,value>>) |
| Attributes | `DataType::List(Struct<key,value>)` NOT `DataType::Map` (DataFusion Map-panic workaround) |
| Storage constructor | `NexusStorage::new_for_test(wal, memtable, registry, data_dir)` — synchronous |
| Write path | `write_arrow_batch(&batch, tenant_override, shard_hint)` — reference, 3 params |
| Empty batch | Returns early from write_arrow_batch WITHOUT triggering stream_tap |
| Series IDs | `HybridSeriesIndex::get_or_create()` returns hash-based u64, NOT sequential |
| AppState | Requires `object_store: Option<Arc<dyn ObjectStore>>` field |
| Flush worker | `spawn_prw_flush_worker(shard_buffer, storage, registry, hybrid_buffer)` — 4 args |
| Two-layer catalog | `HybridSeriesIndex` (persistence) vs `CatalogCache` (query resolution) — both must be updated |

---

## LANCE (VECTOR SEARCH) RULES

Lance (LanceDB) is used for anomaly fingerprint similarity search in Brain v2. These rules prevent the most common Lance-related failures.

### Build Requirements

```bash
# macOS: MUST set toolchain for lance crate compatibility
RUSTUP_TOOLCHAIN=stable-aarch64-apple-darwin cargo build --features lance

# Demo/E2E scripts MUST include --features lance when Brain v2 is involved
```

### Initialization — Never Leave as None

```rust
// WRONG: lance_store: None  (feature is compiled but store is dead)
// RIGHT: Actually initialize the store at startup
#[cfg(feature = "lance")]
lance_store: {
    let path = data_dir.join("brain_fingerprints.lance");
    std::fs::create_dir_all(&path).ok();
    Some(Arc::new(BrainLanceStore::new(path.to_str().unwrap(), 16)))
},
```

### API Signatures

```rust
// search_similar takes 4 args, NOT 2:
lance.search_similar(&padded_signature, tenant_id, &suspect_services, limit).await

// Signatures must be padded to max_dim (16) before Lance operations:
let mut padded = signature.clone();
padded.resize(16, 0.0);

// Lance 0.10 API: Dataset::write/open, .scan().nearest().filter()
// FixedSizeListArrayExt for vector columns
```

### TenantMapper

```rust
// WRONG: state.tenant_mapper.resolve_or_create("default")
// RIGHT:
state.tenant_mapper.get_or_create("default")
```

---

## API HANDLER WIRING RULES

### Registry Metrics Are Direct AtomicU64

```rust
// WRONG: state.registry.brain_v2_rca_triggered_total.as_ref()  (not Option)
// RIGHT:
state.registry.brain_v2_rca_triggered.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
```

### PromQL Queries MUST Include Tenant Header

```rust
// Write path uses x-org header for tenant
// Query path MUST use the same tenant_id
// Mismatch = empty results (data exists but query can't find it)
engine.execute_promql(&promql_query, tenant_id, eval_time_ms).await
```

### Ruler Tenant Matching

```yaml
# config/alerts.yaml: group.tenant_id defaults to "1"
# PRW writes use X-Org header (defaults to "default")
# These MUST match or ruler evaluation finds no data
```

---

## TEST PATTERNS

| Pattern | Rule |
|---------|------|
| `stress_contention.rs` | Uses `compile_error!` in debug mode — always skip in debug tests |
| WAL truncate | May not reduce file to exactly 0 bytes (header retention possible) |
| SBBF bloom filters | Inherent false positives — use `>=` not `==` for candidate counts |
| `resolve_join_keys` | Empty schemas fall through to timestamp-only join (1 key, not 2) |
| `broadcast::Receiver` | Delivers `RecordBatch` directly, not `Arc<RecordBatch>` |
| Series ID determinism | Cross-format determinism no longer holds (string vs column-based hashing differ) |
| Empty batches | 0 rows → early return, no stream_tap, no side effects — tests hang if waiting on tap |

### rkyv Alignment

```rust
// redb returns 4-byte aligned data, rkyv needs 8-byte
// ALWAYS use AlignedVec + check_archived_root
// NEVER use bare from_bytes_unchecked — corruption risk
```

---

## CANONICAL SCHEMA RULES

### mint_derived_series_canonical

- The `__name__` key in attributes must be the string `"__name__"`, NOT the metric name itself
- Use the static fast-path (`mint_derived_series_canonical`) to skip slow `normalize_to_canonical`
- Bug found by `test_canonical_schema_fast_path` — always run this test after schema changes

### Columnar Hash for Labels

```rust
// Use BTreeMap to merge Arrow column labels + extra labels
// BTreeMap handles dedup and sorted iteration
// This ensures hash equivalence with the HashMap-based approach
```

---

## E2E / DEMO VERIFICATION RULES

### Verification Must Assert on Data

```markdown
WRONG: "Demo ran, all 4 use cases printed PASS"
RIGHT: "Demo ran, verified:
  - Signatures contain non-zero values: [3000.0, 3000.0, 3000.0, 0.0]
  - Counters incremented: rca_triggered 0 -> 3
  - Lance store contains 3 fingerprints
  - Similarity search found match at 100%"
```

### Server Operations Reference

| Operation | Command |
|-----------|---------|
| Logs | `outputs/nexus-db.log` (file), `outputs/server_console.log` (stderr) |
| Debug trace | `RUST_LOG=nexus_db::alert::ruler=trace ./scripts/run_e2e.sh ruler` |
| Ruler trigger | `POST /debug/ruler/trigger` |
| Ruler reload | `POST /debug/ruler/load?file=...` |
| Brain metrics | `curl localhost:9090/nexus-db-metrics \| grep brain_v2` |
| Fingerprints | `GET /api/v1/brain/fingerprints` |
| Root cause | `POST /api/v1/brain/root-cause -d '{"service":"..."}'` |

---

## HARD-WON DEBUGGING LESSONS

1. **When API returns errors but metrics show success** — check the serialization/deserialization path, not the business logic
2. **When tests hang** — check for early-return paths that skip side effects (empty batch -> no tap notification)
3. **Prometheus metric format** — values follow labels like `{node="node-1"} 500`. Parsers must handle `{...}` before extracting the value
4. **When multiple services share data** — check tenant_id matching. Writes and queries silently target different tenants if headers don't match
5. **Always check source API signatures before writing calls** — APIs evolve, parameter counts change, types change. `cargo check` is your friend, not your memory

---

## ENFORCEMENT

When working in the NexusDB codebase:

- **REQUIRED**: Check this skill for known pitfalls before writing new code
- **REQUIRED**: Any new API handler must be verified with actual data, not just HTTP 200
- **REQUIRED**: Lance features must be built with `--features lance` and `RUSTUP_TOOLCHAIN` on macOS
- **REQUIRED**: Tenant IDs must match between write and query paths
- **FORBIDDEN**: Initializing lance_store as None when Brain v2 features are active
- **FORBIDDEN**: Using `from_bytes_unchecked` for rkyv deserialization
- **FORBIDDEN**: Marking E2E tests as PASS when response data contains zeros or empty arrays
