---
name: technical-documentation
description: Use when creating, editing, or reviewing ANY documentation - docs, guides, API references, architecture docs, READMEs, or inline comments. MANDATORY for all documentation work in website/docs/ and docs/ directories. FORBIDDEN patterns include passive voice, jargon without definitions, undocumented assumptions. REQUIRED patterns are progressive disclosure, code-verified examples, Docusaurus frontmatter.
---

# Technical Documentation Skill

## THE MANDATE

Documentation is **product**. When you write documentation, you're building a user interface for knowledge. Every doc MUST answer: **"What does this let me do?"** before explaining how.

NexusDB uses **Docusaurus** for the website (`website/docs/`) and maintains internal docs (`docs/`). This skill governs both.

---

## FORBIDDEN PATTERNS

### ❌ **BANNED** - Passive Voice That Obscures Agency

```markdown
<!-- WRONG -->
Data is ingested and stored in the hot tier.
Queries are executed by the engine.
The configuration file should be created.

<!-- RIGHT -->
NexusDB ingests data into the hot tier.
The DataFusion query engine executes queries.
Create the configuration file at `config/nexus.yaml`.
```

### ❌ **BANNED** - Jargon Without Immediate Definition

```markdown
<!-- WRONG -->
The Brain uses Welford's algorithm for seasonal bucketing.

<!-- RIGHT -->
The Brain uses **Welford's algorithm**—a numerically stable method for computing running mean and variance—to track seasonal patterns.
```

### ❌ **BANNED** - Missing Frontmatter

```markdown
<!-- WRONG - No frontmatter -->
# My Document

<!-- RIGHT - Docusaurus frontmatter -->
---
sidebar_position: 3
title: My Document
description: One-sentence summary for SEO and sidebar
---

# My Document
```

### ❌ **BANNED** - Untested Code Examples

Never include code snippets that haven't been verified. If you can't run it, don't document it.

### ❌ **BANNED** - "Simple", "Easy", "Just", "Obviously"

```markdown
<!-- WRONG -->
Simply run the command to start the server.
It's easy to configure alerts.
Just add the label to your metrics.

<!-- RIGHT -->
Run the command to start the server.
Configure alerts by editing `alerts.yaml`.
Add the label to your metrics.
```

### ❌ **BANNED** - Wall of Text Without Structure

Every section needs:
- Headers for navigation
- Bullet points for lists of 3+ items
- Code blocks for anything executable
- Diagrams for architecture and data flow

### ❌ **BANNED** - Reference-Only Docs Without Context

```markdown
<!-- WRONG - Starts with reference -->
## Configuration Options
- `storage.hot.shards`: Number of shards...

<!-- RIGHT - Context first, reference after -->
## Storage Configuration

NexusDB's three-tier storage is configured in `config/nexus.yaml`. 
The hot tier handles recent writes; tune it based on your write volume.

### Hot Tier Options

| Option | Default | Description |
|--------|---------|-------------|
| `storage.hot.shards` | 64 | Number of parallel write shards |
```

---

## REQUIRED PATTERNS

### ✅ **MUST** - Progressive Disclosure Structure

Every document follows this hierarchy:

```
1. WHAT (1-2 sentences) - What is this? What does it let me do?
2. WHY (1 paragraph) - Why would I use this? What problem does it solve?
3. HOW (Quick Start) - Show me the fastest path to success
4. DETAILS (Reference) - Complete options, edge cases, configuration
5. TROUBLESHOOTING - Common errors and solutions
```

**Example:**

```markdown
# Intelligence Engine

<!-- WHAT -->
The Intelligence Engine automatically detects anomalies in your metrics without manual threshold configuration.

<!-- WHY -->
Traditional alerting requires you to set static thresholds that are wrong during traffic spikes and quiet periods. The Intelligence Engine learns what's "normal" for each metric at each hour of the week, then alerts when values deviate significantly.

<!-- HOW - Quick Start -->
## Quick Start

Enable anomaly detection in `config/nexus.yaml`:

\```yaml
intelligence:
  enabled: true
  sensitivity: 3.0  # Standard deviations
\```

<!-- DETAILS -->
## Configuration Reference
...

<!-- TROUBLESHOOTING -->
## Troubleshooting
...
```

### ✅ **MUST** - Use Docusaurus Frontmatter

```yaml
---
sidebar_position: 1        # Order in sidebar
title: Display Title       # Shows in sidebar and tab
description: SEO summary   # One sentence, appears in search
slug: /custom-url          # Optional: custom URL path
---
```

### ✅ **MUST** - Code Examples Are Verified

Before including any code:
1. Run the code yourself
2. Copy the exact output
3. Include version numbers where relevant

```markdown
\```bash
# Tested on NexusDB v0.4.0
curl http://localhost:9095/api/v1/query \
  -d 'query=up{job="nexusdb"}' | jq

# Expected output:
{
  "status": "success",
  "data": {
    "resultType": "vector",
    "result": [...]
  }
}
\```
```

### ✅ **MUST** - Use Mermaid for Architecture Diagrams

NexusDB docs use Mermaid for diagrams (enabled in docusaurus.config.ts):

```markdown
\```mermaid
graph TB
    A[Prometheus] --> B[Remote Write Handler]
    B --> C[Gatekeeper]
    C --> D[Hot Store]
\```
```

### ✅ **MUST** - Tables for Configuration Reference

```markdown
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `storage.hot.shards` | int | 64 | Number of write shards |
| `storage.hot.flush_interval` | duration | 15m | Time before warm tier transition |
```

### ✅ **MUST** - Admonitions for Warnings/Notes

```markdown
:::tip Quick Win
Enable bloom filters for 10x faster label lookups.
:::

:::warning Performance Impact
Setting `shards` > 128 increases memory pressure.
:::

:::danger Data Loss Risk
Never delete WAL files while NexusDB is running.
:::
```

### ✅ **MUST** - Include Performance Characteristics

For any feature doc, include concrete numbers:

```markdown
## Performance

| Metric | Value | Conditions |
|--------|-------|------------|
| Write latency (P50) | <100μs | Existing series |
| Write latency (P99) | <500μs | New series |
| Query latency (P99) | <10ms | 1M series, 1h range |
```

### ✅ **MUST** - Link to Related Docs

Never leave readers at a dead end:

```markdown
## Next Steps

- [Configure alerting](/docs/features/alerting) to act on anomalies
- [Tune storage](/docs/guides/tuning) for your workload
- [API Reference](/docs/api/overview) for programmatic access
```

---

## DOCUMENT TYPES & TEMPLATES

### Type 1: Concept Doc (Architecture, Features)

```markdown
---
sidebar_position: N
title: Feature Name
description: What this feature does in one sentence
---

# Feature Name

[One paragraph: what is this, why does it exist]

## Overview

[Diagram showing where this fits in the system]

## How It Works

[Technical explanation with examples]

## Configuration

[YAML/code snippets]

## Performance

[Table with latency/throughput numbers]

## Limitations

[Honest about what this doesn't do]

## Related

[Links to related docs]
```

### Type 2: How-To Guide (Operations, Tutorials)

```markdown
---
sidebar_position: N
title: How to Do X
description: Step-by-step guide to accomplish X
---

# How to Do X

[One sentence: what you'll accomplish]

## Prerequisites

- [ ] Requirement 1
- [ ] Requirement 2

## Steps

### Step 1: First Action

[Explanation + code]

### Step 2: Second Action

[Explanation + code]

## Verification

[How to confirm it worked]

## Troubleshooting

### Error: Common Error Message

[Cause and solution]
```

### Type 3: API Reference

```markdown
---
sidebar_position: N
title: Endpoint Name
description: Brief description of what this endpoint does
---

# Endpoint Name

`POST /api/v1/endpoint`

[One sentence description]

## Request

### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type` | Yes | Must be `application/json` |

### Body

\```json
{
  "field": "value"
}
\```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `field` | string | Yes | Description |

## Response

### Success (200)

\```json
{
  "status": "success"
}
\```

### Error Codes

| Code | Description |
|------|-------------|
| 400 | Invalid request body |
| 500 | Internal error |

## Example

\```bash
curl -X POST http://localhost:9095/api/v1/endpoint \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}'
\```
```

---

## FILE ORGANIZATION

See [templates.md](templates.md) for complete directory structure reference.

---

## WRITING PROCESS

### Before Writing

- [ ] Identify the audience (Developer? Operator? Evaluator?)
- [ ] Determine document type (Concept? How-To? Reference?)
- [ ] Find related existing docs to link/update
- [ ] Verify you have access to test the feature

### While Writing

- [ ] Start with WHAT/WHY before HOW
- [ ] Test every code example
- [ ] Add frontmatter with position, title, description
- [ ] Use Mermaid for any architecture/flow diagrams
- [ ] Include performance numbers where applicable
- [ ] Add troubleshooting for known issues

### Before Committing

- [ ] Run `npm run build` in website/ to catch broken links
- [ ] Verify sidebar position makes sense in navigation
- [ ] Check all internal links resolve
- [ ] Review for passive voice, jargon, "just"/"simple"
- [ ] Ensure every code block has a language tag

---

## STYLE GUIDE

### Voice & Tone

- **Direct**: "Configure X" not "X can be configured"
- **Confident**: "NexusDB stores" not "NexusDB attempts to store"
- **Inclusive**: "You can" not "Users can" (talk TO the reader)
- **Technical but clear**: Explain jargon, but don't dumb down

### Formatting

- **Headers**: Use sentence case ("How it works" not "How It Works")
- **Code inline**: Use backticks for `config_keys`, `commands`, `file.names`
- **Code blocks**: Always include language for syntax highlighting
- **Lists**: Use bullets for unordered, numbers only for sequences
- **Emphasis**: **Bold** for UI elements and key terms, *italic* sparingly

### Naming Consistency

| Correct | Incorrect |
|---------|-----------|
| NexusDB | Nexus DB, nexusDB, NEXUSDB |
| PromQL | Promql, promQL |
| DataFusion | Datafusion, Data Fusion |
| Gatekeeper | Gate Keeper, gatekeeper (in prose) |
| three-tier storage | 3-tier storage, Three Tier Storage |

---

## CHECKLIST

### New Document

- [ ] Created in correct directory (website/docs/ or docs/)
- [ ] Has complete Docusaurus frontmatter
- [ ] Follows progressive disclosure (WHAT → WHY → HOW → DETAILS)
- [ ] All code examples tested and verified
- [ ] Includes related links / next steps
- [ ] Added to sidebars.ts if needed
- [ ] Build passes: `cd website && npm run build`

### Editing Existing Document

- [ ] Preserved existing frontmatter
- [ ] Updated any outdated code examples
- [ ] Verified internal links still work
- [ ] Maintained consistent terminology
- [ ] Build passes after changes

### Review Checklist

- [ ] No passive voice
- [ ] No "just", "simple", "easy", "obviously"
- [ ] No undefined jargon
- [ ] All code blocks have language tags
- [ ] Diagrams use Mermaid
- [ ] Performance claims have numbers
- [ ] Links work
