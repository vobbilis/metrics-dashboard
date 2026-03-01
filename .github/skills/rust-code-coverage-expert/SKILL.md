# Rust Code Coverage Expert

Use when measuring, analyzing, or improving code coverage in Rust projects. MANDATORY for coverage-related tasks, writing coverage tests, setting up coverage infrastructure, or diagnosing coverage gaps.

## When This Skill Applies

- Setting up code coverage infrastructure (llvm-cov, cargo-llvm-cov)
- Writing tests specifically to increase coverage
- Analyzing coverage reports and identifying gaps
- Creating coverage CI/CD pipelines
- Understanding why certain lines aren't covered
- Establishing coverage thresholds and policies

## The Deep Intent Behind Code Coverage

**Coverage is NOT a metric to game. It's a tool for discovering untested behavior.**

The NexusDB coverage infrastructure embodies these principles:

1. **Targeted Coverage Tests**: Each module has a dedicated `*_coverage_test.rs` file
2. **Behavioral Focus**: Tests verify caller expectations, not implementation details
3. **Coverage Priorities**: P1 (≥95% core), P2 (≥90% support), P3 (≥85% utilities)
4. **Actionable Reports**: Scripts show "top 10 files needing improvement"

## Coverage Infrastructure Setup

### Required Tools

| Tool | Purpose | Install Command |
|------|---------|-----------------|
| llvm-tools-preview | LLVM instrumentation | `rustup component add llvm-tools-preview` |
| cargo-llvm-cov | Coverage command | `cargo install cargo-llvm-cov` |
| Python 3 | JSON report parsing | OS package manager |

### Standard Directory Structure

```
project/
├── code-coverage/
│   ├── scripts/
│   │   ├── coverage.sh          # Main runner
│   │   └── setup-coverage.sh    # Dependency installer
│   ├── output/                   # JSON data files
│   └── reports/html/             # HTML reports
└── tests/
    ├── module_coverage_test.rs   # Dedicated coverage tests
    └── module_integration_test.rs # Integration tests
```

## Writing Coverage Tests

### Naming Convention

```
tests/<module>_coverage_test.rs  →  src/<path>/<module>.rs
```

| Test File | Target Source |
|-----------|---------------|
| `wal_coverage_test.rs` | `src/storage/wal.rs` |
| `compaction_coverage_test.rs` | `src/storage/compaction.rs` |
| `registry_coverage_test.rs` | `src/monitor/registry.rs` |

### Coverage Test Structure

Every coverage test file should have clear sections:

```rust
//! Behavioral tests for <module>
//!
//! Verify <module> behavior:
//! 1. <Primary behavior>
//! 2. <Secondary behavior>
//! 3. <Error handling>
//!
//! Target: ≥95% coverage for <module>

// =============================================================================
// BASIC CONSTRUCTION TESTS
// =============================================================================

#[test]
fn test_new_creates_instance() {
    // Test default construction
}

#[test]
fn test_new_with_config() {
    // Test parameterized construction
}

// =============================================================================
// CORE FUNCTIONALITY TESTS
// =============================================================================

#[tokio::test]
async fn test_primary_operation() {
    // Happy path
}

#[tokio::test]
async fn test_primary_operation_edge_case() {
    // Boundary conditions
}

// =============================================================================
// ERROR HANDLING TESTS
// =============================================================================

#[tokio::test]
async fn test_handles_invalid_input() {
    // Verify error types
}

#[tokio::test]
async fn test_recovers_from_corruption() {
    // Test recovery paths
}
```

### The Behavioral Testing Pattern

**WRONG** - Testing internal implementation:
```rust
#[test]
fn test_internal_buffer_size() {
    let wal = WalManager::new(&path);
    assert_eq!(wal.buffer.capacity(), 4096);  // ❌ Testing internal detail
}
```

**RIGHT** - Testing caller expectations:
```rust
#[test]
fn test_flush_persists_all_entries() {
    let wal = WalManager::new(&path);
    wal.write_batch(&entries).await.unwrap();
    wal.flush().await.unwrap();
    
    let recovered = wal.replay().unwrap();
    assert_eq!(recovered.len(), entries.len());  // ✅ Testing observable behavior
}
```

## Coverage Report Analysis

### Understanding Coverage Numbers

```
Coverage shows INSTRUMENTED lines (executable code), NOT total lines:
- 1000-line file → ~350 instrumented lines (typical)
- Comments, imports, type definitions → NOT counted
- Percentage = branch coverage of actual code
```

### Coverage JSON Structure

```json
{
  "data": [{
    "totals": {
      "lines": { "count": 14928, "covered": 843, "percent": 5.64 },
      "functions": { "count": 1100, "covered": 83, "percent": 7.54 },
      "regions": { "count": 25088, "covered": 1043, "percent": 4.15 }
    },
    "files": [{
      "filename": "src/storage/wal.rs",
      "summary": { "lines": { "count": 858, "covered": 786, "percent": 91.61 } }
    }]
  }]
}
```

### Priority-Based Coverage Targets

| Priority | Target | Module Type | Rationale |
|----------|--------|-------------|-----------|
| P1 | ≥95% | Core (storage, catalog) | Data integrity critical |
| P2 | ≥90% | Support (monitor, index) | Operational reliability |
| P3 | ≥85% | Utilities (ingest, query) | Functional correctness |

## Coverage Test Patterns

### Pattern 1: State Transition Coverage

```rust
// Test all states of a stateful component
#[tokio::test]
async fn test_state_transitions() {
    let wal = WalManager::new(&path);
    
    // State: Empty
    assert!(!wal.has_pending_entries());
    assert_eq!(wal.write_lsn(), 0);
    
    // Transition: Write
    wal.write_batch(&entries).await.unwrap();
    
    // State: Has pending
    assert!(wal.has_pending_entries());
    assert_eq!(wal.write_lsn(), entries.len());
    
    // Transition: Checkpoint
    wal.checkpoint(wal.write_lsn() - 1);
    
    // State: All checkpointed
    assert!(!wal.has_pending_entries());
}
```

### Pattern 2: Error Path Coverage

```rust
// Cover every error return path
#[tokio::test]
async fn test_replay_truncated_header() {
    // Create file with incomplete header (2 bytes instead of 4)
    let mut file = File::create(&path).unwrap();
    file.write_all(&[0x1C, 0x00]).unwrap();  // Partial length
    
    let wal = WalManager::new(&path).unwrap();
    let result = wal.replay();
    
    // Should handle gracefully (UnexpectedEof = end of log)
    assert!(result.is_ok());
    assert!(result.unwrap().is_empty());
}

#[tokio::test]
async fn test_replay_truncated_payload() {
    // Create file with valid header but truncated payload
    let mut file = File::create(&path).unwrap();
    file.write_all(&28u32.to_le_bytes()).unwrap();  // Claims 28 bytes
    file.write_all(&[0x01, 0x02, 0x03]).unwrap();   // Only 3 bytes
    
    let wal = WalManager::new(&path).unwrap();
    let result = wal.replay();
    
    assert!(result.is_err());
    assert!(result.unwrap_err().to_string().contains("Truncated"));
}
```

### Pattern 3: Boundary Condition Coverage

```rust
// Test edge cases explicitly
#[tokio::test]
async fn test_empty_batch() {
    let wal = WalManager::new(&path).unwrap();
    let lsn = wal.write_batch(&[], &[], &[], &[]).await.unwrap();
    
    assert_eq!(lsn, 0);  // Current write LSN returned
    assert_eq!(wal.entries_written(), 0);
}

#[tokio::test]
async fn test_single_entry_batch() {
    let wal = WalManager::new(&path).unwrap();
    let lsn = wal.write_batch(&[1], &[100], &[1000], &[42.5]).await.unwrap();
    
    assert_eq!(lsn, 0);  // First entry gets LSN 0
    assert_eq!(wal.write_lsn(), 1);
}

#[tokio::test]
async fn test_large_batch() {
    let wal = WalManager::new(&path).unwrap();
    let count = 10_000;
    let tenant_ids: Vec<_> = (0..count).map(|_| 1).collect();
    let series_ids: Vec<_> = (0..count).map(|i| i as u64).collect();
    let timestamps: Vec<_> = (0..count).map(|i| i as i64).collect();
    let values: Vec<_> = (0..count).map(|i| i as f64).collect();
    
    let lsn = wal.write_batch(&tenant_ids, &series_ids, &timestamps, &values)
        .await.unwrap();
    
    assert_eq!(lsn, count - 1);  // End LSN
    assert_eq!(wal.entries_written(), count);
}
```

### Pattern 4: Deduplication/Policy Testing

```rust
// Test policy triggers at exact thresholds
#[test]
fn test_size_tiered_policy_threshold() {
    let config = CompactionConfig { l0_threshold: 4, ..Default::default() };
    let policy = SizeTieredPolicy::new(config);
    
    // 3 files: No compaction
    for i in 0..3 {
        catalog.register(mock_fragment(i, Level::L0));
    }
    assert!(policy.select_files(&catalog).is_none(),
        "Should NOT compact 3 files when threshold is 4");
    
    // 4 files: Triggers compaction
    catalog.register(mock_fragment(3, Level::L0));
    let selection = policy.select_files(&catalog);
    assert!(selection.is_some(), "Should compact at threshold");
    assert_eq!(selection.unwrap().len(), 4);
}
```

## Coverage Script Commands

### Basic Usage

```bash
# Run all tests with coverage
./code-coverage/scripts/coverage.sh

# Run specific test suite
./code-coverage/scripts/coverage.sh --test wal_coverage_test

# Get coverage for specific file
./code-coverage/scripts/coverage.sh --file src/storage/wal.rs

# Combined: specific test + specific file
./code-coverage/scripts/coverage.sh --test wal_coverage_test --file src/storage/wal.rs

# Summary view of all files
./code-coverage/scripts/coverage.sh --summary
```

### CI/CD Integration

```yaml
# GitHub Actions
coverage:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Setup Coverage
      run: ./code-coverage/scripts/setup-coverage.sh
    - name: Run Coverage
      run: ./code-coverage/scripts/coverage.sh --lib
    - name: Check Threshold
      run: |
        python3 -c "
        import json, sys
        data = json.load(open('code-coverage/output/coverage.json'))
        pct = data['data'][0]['totals']['lines']['percent']
        print(f'Coverage: {pct:.2f}%')
        if pct < 80: sys.exit(1)
        "
```

## Diagnosing Coverage Gaps

### Common Uncovered Code Patterns

| Pattern | Why Uncovered | How to Cover |
|---------|---------------|--------------|
| Error branches | Happy path only | Write tests that trigger errors |
| Edge cases | Standard inputs | Test empty, single, max values |
| Panic paths | Tests avoid panics | Use `#[should_panic]` tests |
| Dead code | Never called | Remove or verify needed |
| Platform-specific | Wrong OS | Use cfg-aware testing |

### Reading Coverage Reports

```bash
# Visual bars show coverage at a glance
File                                     Coverage
-------------------------------------------------------
wal.rs                                   ████████████████░░░░ 91.61% ✅
memtable.rs                              ███████████████████░ 95.31% ✅
compaction.rs                            ████████████████████ 98.42% ✅
prometheus.rs                            ██████████████████░░ 91.18% 🟡
```

### Identifying What to Test

```bash
# Show files needing improvement
./code-coverage/scripts/coverage.sh --summary

# Output: Top 10 files needing improvement
#   new_module.rs           65.00%  <- Start here
#   legacy_handler.rs       72.34%
#   ...
```

## FORBIDDEN Patterns

1. **Gaming coverage with meaningless tests**
   ```rust
   // ❌ WRONG: Just calls code without assertions
   #[test]
   fn test_covers_lines() {
       let _ = MyStruct::new();
       let _ = my_struct.do_something();
   }
   ```

2. **Testing implementation details**
   ```rust
   // ❌ WRONG: Tests internal state
   assert_eq!(wal.internal_buffer.len(), 42);
   ```

3. **Ignoring error paths**
   ```rust
   // ❌ WRONG: Only happy path
   let result = wal.replay().unwrap();  // What if replay fails?
   ```

4. **Copy-paste test bodies**
   ```rust
   // ❌ WRONG: Same test with different names
   fn test_case_1() { /* identical body */ }
   fn test_case_2() { /* identical body */ }
   ```

## REQUIRED Patterns

1. **Behavioral assertions on observable state**
   ```rust
   // ✅ RIGHT: Test observable behavior
   wal.write(&entry).await.unwrap();
   wal.flush().await.unwrap();
   let recovered = wal.replay().unwrap();
   assert_eq!(recovered[0].value, entry.value);
   ```

2. **Error path coverage**
   ```rust
   // ✅ RIGHT: Explicitly test error conditions
   let result = wal.replay();  // Corrupted file
   assert!(result.is_err());
   assert!(result.unwrap_err().to_string().contains("Truncated"));
   ```

3. **Boundary condition tests**
   ```rust
   // ✅ RIGHT: Empty, single, many
   test_empty_batch();
   test_single_entry();
   test_large_batch();
   ```

4. **State transition verification**
   ```rust
   // ✅ RIGHT: Verify state changes
   assert!(!wal.has_pending_entries());  // Before
   wal.write(&entry).await.unwrap();
   assert!(wal.has_pending_entries());   // After
   ```

## Coverage Improvement Workflow

1. **Identify**: Run coverage, find lowest-covered modules
2. **Analyze**: Read the source, identify untested paths
3. **Plan**: Create `<module>_coverage_test.rs` if not exists
4. **Implement**: Write behavioral tests for uncovered paths
5. **Verify**: Re-run coverage, confirm improvement
6. **Document**: Update coverage tables in README

```bash
# Workflow example
./code-coverage/scripts/coverage.sh --summary
# → sparse_index.rs: 78%

# Read source to find untested paths
# Write tests in tests/sparse_index_coverage_test.rs

# Verify improvement
./code-coverage/scripts/coverage.sh --test sparse_index_coverage_test \
    --file src/storage/sparse_index.rs
# → sparse_index.rs: 93.12%
```

## Test Helper Patterns

### Mock Data Factories

```rust
fn mock_fragment(id: u64, level: Level) -> FragmentMetadata {
    FragmentMetadata {
        id,
        path: PathBuf::from(format!("{}.parquet", id)),
        min_timestamp: 0,
        max_timestamp: 1000,
        row_count: 100,
        size_bytes: 1000,
        level,
        ..Default::default()
    }
}
```

### Parquet Test File Creation

```rust
fn create_parquet_file(
    path: &Path,
    data: Vec<(i64, i64, f64)>,  // (series_id, timestamp, value)
) -> anyhow::Result<()> {
    let schema = Arc::new(Schema::new(vec![
        Field::new("series_id", DataType::Int64, false),
        Field::new("timestamp", DataType::Int64, false),
        Field::new("value", DataType::Float64, false),
    ]));
    
    let batch = RecordBatch::try_new(schema.clone(), vec![
        Arc::new(Int64Array::from(data.iter().map(|d| d.0).collect::<Vec<_>>())),
        Arc::new(Int64Array::from(data.iter().map(|d| d.1).collect::<Vec<_>>())),
        Arc::new(Float64Array::from(data.iter().map(|d| d.2).collect::<Vec<_>>())),
    ])?;
    
    let file = File::create(path)?;
    let mut writer = ArrowWriter::try_new(file, schema, None)?;
    writer.write(&batch)?;
    writer.close()?;
    Ok(())
}
```

## Summary

Code coverage in Rust is about **discovering untested behavior**, not hitting a number. 

The key principles:
- **Dedicated coverage test files** per module
- **Behavioral tests** that verify caller expectations
- **Priority-based thresholds** (P1: 95%, P2: 90%, P3: 85%)
- **Error path coverage** is as important as happy path
- **Boundary conditions** (empty, single, large) must be tested
- **Actionable reports** that show what needs work

Use `cargo-llvm-cov` with targeted tests for efficient coverage measurement, and focus on the quality of tests, not just the percentage.
