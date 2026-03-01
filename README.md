# Aigile

Multi-agent orchestration pipelines for GitHub Copilot — plan, build, review, and ship with specialized AI agents working in concert.

**[Live Documentation →](https://vobbilis.github.io/aigile/)**

---

## What Is This?

Aigile is a set of reusable Copilot-native pipelines that turn a single prompt into fully orchestrated, multi-agent software delivery. Describe a feature or a bug in plain English; the system plans the work, implements it with TDD, validates every step, runs adversarial code review, and opens a PR — all without leaving VS Code.

The pipelines are **project-agnostic**. Edit one config file (`.github/project.json`) to point them at any tech stack — Python, TypeScript, Java, Go, or anything else.

---

## Architecture Overview

**[Pipelines Technical Overview →](.github/PIPELINES.md)** — full architecture with Mermaid diagrams, agent registry, hook system, and data flow.

---

## Tests

Step-by-step tests to verify each pipeline end-to-end. See **[docs/TESTING.md](docs/TESTING.md)** for full details.

| Test | What It Validates | Link |
|------|-------------------|------|
| **Test 1** | VS Code Copilot — interactive local agent mode | [Test 1: VS Code Copilot](docs/TESTING.md#test-1-vs-code-copilot-interactive-local) |
| **Test 2** | GitHub Copilot Coding Agent — async cloud PR flow | [Test 2: Async Cloud Agent](docs/TESTING.md#test-2-github-copilot-coding-agent-async-cloud) |
| **Test 3** | Failure recovery — CI failures and cross-platform seams | [Test 3: Failure Recovery](docs/TESTING.md#test-3-failure-recovery-the-interesting-one) |
| **Test 4** | Bug-to-PR pipeline — 7 agents, 6 phases, full lifecycle | [Test 4: Bug-to-PR Pipeline](docs/TESTING.md#test-4-bug-to-pr-pipeline-the-star-of-the-show) |

---

## More Documentation

| Document | Description |
|----------|-------------|
| [Adapting to Your Project](docs/ADAPTING-TO-YOUR-PROJECT.md) | Detailed guide to configure the pipelines for any tech stack |
| [Quick Adapt](docs/QUICK-ADAPT.md) | 5 copy-paste Copilot prompts that generate all config for you |
| [Local vs. Cloud Comparison](docs/TESTING.md#local-vs-cloud-why-both-matter) | Why both agent architectures matter and when to use each |

---

## Quick Start

```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 — the frontend proxies API calls to port 8000.
