# GitHub Copilot Skills

This directory contains **skills** that guide GitHub Copilot's behavior for this project.

## What Are Skills?

Skills are markdown files with YAML frontmatter that teach GitHub Copilot project-specific patterns, workflows, and guardrails. When you ask Copilot to help with a task, it reads relevant skills and follows their guidance.

## Available Skills

| Skill | Purpose |
|-------|---------|
| **using-skills** | Meta-skill that establishes how skills work |
| **brainstorming** | Design thinking before coding |
| **design-study-expert** | Deep code research, architecture analysis, industry comparisons |
| **design-evaluation** | Evaluate design options with POCs |
| **writing-plans** | Create implementation plans |
| **executing-plans** | Execute plans with checkpoints |
| **plan-reviewer** | Review plans before implementation |
| **test-driven-development** | RED-GREEN-REFACTOR cycle |
| **systematic-debugging** | 4-phase debugging process |
| **code-refactoring** | Safe file moves and restructuring |
| **data-contract-validation** | Producer-consumer contract verification |
| **pre-flight-readiness** | E2E/integration test risk assessment with "What If" analysis |
| **verification-before-completion** | Verify before declaring done |
| **requesting-code-review** | Prepare PRs for review |
| **receiving-code-review** | Handle review feedback |
| **finishing-a-development-branch** | Merge and cleanup |
| **using-git-worktrees** | Parallel development |
| **frontend-dev-guidelines** | React, MUI, TypeScript patterns |
| **backend-dev-guidelines** | Express, controllers, services |
| **error-tracking** | Sentry integration patterns |
| **route-tester** | API endpoint testing |
| **rust-db-architect** | Database architecture, storage engines |
| **rust-code-coverage-expert** | Code coverage with llvm-cov |
| **prd-writer** | Generate PRDs from user stories with TDD-first task + test plans |

## How Skills Work

1. Each skill lives in its own directory with a `SKILL.md` file
2. The YAML frontmatter contains `name` and `description`
3. The `description` field tells Copilot when to use the skill
4. When your request matches a skill's description, Copilot loads and follows it

## Skill Format

Every skill follows this structure:

```markdown
---
name: skill-name
description: Use when [triggers]. MANDATORY for [scope]. FORBIDDEN is [anti-patterns]. REQUIRED is [patterns].
---

# Skill Title

## THE MANDATE
[Core requirement]

## FORBIDDEN PATTERNS
[What NOT to do with examples]

## REQUIRED PATTERNS
[What TO do with examples]
```

## Creating a New Skill

1. Create a directory: `mkdir .github/skills/my-skill`
2. Create `SKILL.md` with the format above
3. Write a clear `description` with trigger keywords
4. Include code examples for FORBIDDEN and REQUIRED patterns
5. Test by asking Copilot to do something the skill covers

## Tips for Effective Skills

- **Description is key**: Use specific keywords that match user requests
- **Be authoritative**: Use MANDATORY, FORBIDDEN, REQUIRED, NEVER, ALWAYS
- **Show, don't tell**: Include code examples for every pattern
- **Keep it focused**: Under 500 lines per skill
- **Test your triggers**: Verify the skill activates when expected
