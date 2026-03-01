---
name: using-skills
description: Use BEFORE any task. MANDATORY skill that establishes how all other skills work. Invoke this skill if unsure whether skills apply. Skills are NOT optional - if a skill exists for your task, you MUST use it or you have failed.
---

# Using Skills

## THE MANDATE

**You MUST invoke relevant skills BEFORE any response or action.**

This is not a suggestion. This is not optional. If a skill applies to your task and you don't use it, **you have failed**.

---

## MANDATORY WORKFLOW ORDER

For ANY significant feature or implementation, skills MUST be used in this order:

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: BRAINSTORMING                                      │
│  "Let's explore options for X"                              │
│  → Explore alternatives, ask questions ONE at a time        │
│  → Output: Multiple options with tradeoffs                  │
│                         ↓                                   │
│  STEP 2: DESIGN EVALUATION (if multiple options)            │
│  "Let's evaluate these options with POCs"                   │
│  → Build minimal POCs (1-2 hours each)                      │
│  → Output: Comparison table with measurements               │
│                         ↓                                   │
│  STEP 3: WRITING PLANS                                      │
│  "Create an implementation plan"                            │
│  → Write detailed plan with bite-sized tasks                │
│  → Output: Plan file in docs/plans/                         │
│                         ↓                                   │
│  STEP 4: EXECUTING PLANS                                    │
│  "Let's execute the plan"                                   │
│  → Execute in batches with checkpoints                      │
│  → Output: Working implementation                           │
└─────────────────────────────────────────────────────────────┘
```

### FORBIDDEN: Skipping Steps

| If User Says... | FORBIDDEN Response | REQUIRED Response |
|-----------------|-------------------|-------------------|
| "Build me X" | Start coding immediately | "Let's first explore options for X" (→ brainstorming) |
| "Use Redis for caching" | Start implementing Redis | "Before we commit, let's evaluate alternatives" (→ design-evaluation) |
| "Implement Option A" | Start coding Option A | "Let me create an implementation plan first" (→ writing-plans) |
| "Just do it" | Skip to execution | "I understand the urgency, but let's at least create a quick plan" |

### When Steps Can Be Skipped

| Situation | Can Skip |
|-----------|----------|
| Trivial change (< 15 min, single file) | Brainstorming, Design Eval, Planning |
| Only ONE obvious option exists | Design Evaluation only |
| Plan already exists | Brainstorming, Design Eval |
| User explicitly says "skip planning" | Planning (but document they chose this) |

---

## SKILL DISCOVERY FLOW

```
┌─────────────────────────────────────────────────────────────┐
│  USER MESSAGE RECEIVED                                      │
│                    ↓                                        │
│  Could ANY skill apply? (even 1% chance)                    │
│         ↓                    ↓                              │
│        YES                   NO                             │
│         ↓                    ↓                              │
│  READ the skill         Respond normally                    │
│         ↓                                                   │
│  ANNOUNCE: "Using [skill] for [purpose]"                    │
│         ↓                                                   │
│  FOLLOW the skill EXACTLY                                   │
│         ↓                                                   │
│  Has checklist? → Create todos for EACH item                │
│         ↓                                                   │
│  Respond following the skill                                │
└─────────────────────────────────────────────────────────────┘
```

## Available Skills

| Skill | Use When | Workflow Step |
|-------|----------|---------------|
| **brainstorming** | New features, architecture decisions | Step 1 |
| **design-evaluation** | Multiple options need comparison | Step 2 |
| **writing-plans** | Creating implementation plans | Step 3 |
| **executing-plans** | Executing a plan | Step 4 |
| **test-driven-development** | Implementing ANY feature or bugfix | During Step 4 |
| **systematic-debugging** | ANY bug, unexpected behavior | Any time |
| **frontend-dev-guidelines** | ANY React/TypeScript code, components, styling, MUI, UI | During Step 4 |
| **backend-dev-guidelines** | ANY Node.js/Express code, routes, controllers, services | During Step 4 |
| **error-tracking** | ANY error handling, catch blocks, Sentry integration | During Step 4 |
| **route-tester** | Testing API endpoints, debugging auth issues | During Step 4 |
| **skill-developer** | Creating or modifying skills | Any time |

## Red Flags - If You Think This, STOP

These thoughts mean you're **rationalizing**. Stop immediately.

| If you think... | Reality |
|-----------------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "Let me gather information first" | Skills tell you HOW to gather information. |
| "I can check git/files quickly" | Files lack conversation context. Check for skills. |
| "This doesn't need a formal skill" | If a skill exists, use it. Period. |
| "I remember this skill" | Skills evolve. Read the current version. |
| "This doesn't count as a task" | Any action = task. Check for skills. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means" | Knowing the concept ≠ using the skill. Read it. |

## Skill Priority

When multiple skills apply:

1. **Process skills first** (brainstorming, debugging) - these determine HOW to approach
2. **Implementation skills second** (frontend-dev-guidelines, backend-dev-guidelines) - these guide execution
3. **FORBIDDEN patterns always win** - If any skill forbids something, don't do it

**Examples:**
- "Let's build X" → brainstorming first, then implementation skills
- "Fix this bug" → systematic-debugging first, then domain-specific skills

## Skill Types

**Rigid skills** (TDD, debugging): Follow EXACTLY. Don't adapt away discipline.

**Flexible skills** (patterns, guidelines): Adapt principles to context.

The skill itself tells you which type it is.

## How To Use Skills

1. **Read the description** - Decide if it applies
2. **Read the full skill** - Don't skim, don't summarize from memory
3. **Announce usage** - "I'm using [skill-name] to guide this work"
4. **Follow exactly** - Don't improvise. Don't "adapt". Follow it.
5. **Check FORBIDDEN patterns** - Never generate forbidden code
6. **Complete checklists** - Every checkbox = a required action

## Enforcement

Skills use authoritative language intentionally:

- **MUST** = Required, no exceptions
- **FORBIDDEN** = Never generate this, ever
- **REQUIRED** = Always do this
- **NEVER** = Absolute prohibition

These are not suggestions. Code that violates FORBIDDEN patterns will be rejected.

## Before Any Response

Ask yourself:

1. Does this involve frontend code? → `frontend-dev-guidelines`
2. Does this involve backend code? → `backend-dev-guidelines`
3. Does this involve error handling? → `error-tracking`
4. Am I implementing a feature? → `test-driven-development`
5. Am I debugging? → `systematic-debugging`
6. Am I planning something new? → `brainstorming`

**When in doubt, read the skill.** It's better to read a skill you didn't need than to skip one you did.

---

## The Bottom Line

**Skills are mandatory workflows, not suggestions.**

If a skill applies to your task and you didn't use it, you have failed the task - even if your code "works".

The skills encode lessons from past failures. Ignoring them means repeating those failures.
