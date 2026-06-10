---
name: brainstorming
description: Use when planning features, designing systems, starting new projects, or making architectural decisions BEFORE writing code. MANDATORY for significant changes. FORBIDDEN is diving into code without design. REQUIRED is Socratic questioning to refine requirements and explore alternatives.
---

# Brainstorming Ideas Into Designs

## THE MANDATE

**Think before you code.**

Help turn ideas into fully formed designs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions **one at a time** to refine the idea. Once you understand what you're building, present the design in small sections, checking after each section whether it looks right.

---

## THE CONVERSATION DISCIPLINE

### One Question At A Time

```markdown
❌ FORBIDDEN - Question dump:
"Before I implement authentication:
1. What auth method?
2. What providers?
3. Session duration?
4. Password reset flow?
5. Need 2FA?
6. What's your user model?"

✅ REQUIRED - One at a time:
"What auth method are you thinking? 
(a) Session-based 
(b) JWT tokens 
(c) OAuth/social login
(d) Something else?"

[Wait for answer]

"Got it, JWT. For the providers, are you planning:
(a) Email/password only
(b) Social login (Google, GitHub)
(c) Both?"

[Wait for answer]
```

### Prefer Multiple Choice

When possible, give options rather than open-ended questions:

```markdown
❌ Open-ended (harder to answer):
"How do you want to handle errors?"

✅ Multiple choice (easier to answer):
"For error handling, which approach?
(a) Return error codes with messages
(b) Throw exceptions, catch at boundary
(c) Result type (Ok/Err pattern)
(d) Something else?"
```

---

## WHEN TO USE THIS SKILL

This skill is MANDATORY before:

- Creating a new feature
- Designing a new system component
- Making architectural decisions
- Refactoring significant code
- Adding new dependencies
- Changing data models

---

## FORBIDDEN PATTERNS

### ❌ Diving In Without Design - BANNED

```markdown
User: "Add user authentication"

❌ FORBIDDEN:
*Immediately starts writing auth code*

✅ REQUIRED:
"What auth method are you thinking?
(a) Session-based cookies
(b) JWT tokens  
(c) OAuth/social login
(d) Something else?"
```

### ❌ Question Dumps - BANNED

See "THE CONVERSATION DISCIPLINE" above. One question at a time, not six.

### ❌ Assuming Requirements - BANNED

```markdown
User: "Add a search feature"

❌ FORBIDDEN:
*Assumes full-text search with Elasticsearch*

✅ REQUIRED:
"What are users searching?
(a) Products in a catalog
(b) Users/profiles
(c) Content/documents
(d) Something else?"
```

### ❌ Single Solution Thinking - BANNED

```markdown
❌ FORBIDDEN:
"I'll implement this using X"

✅ REQUIRED:
"I see three approaches:
1. **Option A**: [pros/cons]
2. **Option B**: [pros/cons]  
3. **Option C**: [pros/cons]

Given your requirements, I recommend Option B because..."
```

---

## THE BRAINSTORMING PROCESS

```
┌─────────────────────────────────────────────────────────────┐
│  1. CLARIFY                                                 │
│     What exactly do you need? Why?                          │
│         ↓                                                   │
│  2. EXPLORE                                                 │
│     What are the options?                                   │
│         ↓                                                   │
│  3. EVALUATE                                                │
│     What are the tradeoffs?                                 │
│         ↓                                                   │
│  4. RECOMMEND                                               │
│     What's best for your situation?                         │
│         ↓                                                   │
│  5. CONFIRM                                                 │
│     Does this match your expectations?                      │
└─────────────────────────────────────────────────────────────┘
```

---

## PHASE 1: CLARIFY

Ask questions to deeply understand the need.

### Core Questions

```markdown
1. **WHAT** exactly do you need?
   - What's the specific feature/change?
   - What should it do?
   - What should it NOT do?

2. **WHY** do you need this?
   - What problem does it solve?
   - Who benefits?
   - What's the impact if we don't do it?

3. **WHO** is the user?
   - Who will use this feature?
   - What's their technical level?
   - What's their workflow?

4. **WHEN** is it needed?
   - Timeline constraints?
   - MVP vs full feature?
   - Phased rollout?

5. **WHERE** does it fit?
   - Which system/service?
   - Integration points?
   - Existing code to leverage?

6. **CONSTRAINTS**?
   - Performance requirements?
   - Scale expectations?
   - Budget/resource limits?
   - Tech stack requirements?
```

### Checklist

- [ ] Understand the core problem
- [ ] Know who the users are
- [ ] Clarified scope (what's in/out)
- [ ] Identified constraints
- [ ] Understand timeline/priority

---

## PHASE 2: EXPLORE

Generate multiple approaches.

### Template

```markdown
## Approach 1: [Name]

**Description**: [How it works]

**Pros**:
- Pro 1
- Pro 2

**Cons**:
- Con 1
- Con 2

**Complexity**: Low / Medium / High
**Time Estimate**: X days/weeks

---

## Approach 2: [Name]
...
```

### Exploration Questions

```markdown
- What's the simplest solution?
- What's the most robust solution?
- What's the fastest to implement?
- What have others done?
- What could we reuse?
- What if requirements change?
```

---

## PHASE 3: EVALUATE

Analyze tradeoffs systematically.

### Comparison Matrix

```markdown
| Criteria          | Option A | Option B | Option C |
|-------------------|----------|----------|----------|
| Complexity        | Low      | Medium   | High     |
| Time to implement | 2 days   | 1 week   | 2 weeks  |
| Scalability       | Limited  | Good     | Excellent|
| Maintainability   | High     | Medium   | Low      |
| Risk              | Low      | Medium   | High     |
```

### Risk Assessment

```markdown
For each option, identify:
1. What could go wrong?
2. How likely is it?
3. What's the impact?
4. How would we mitigate it?
```

---

## PHASE 4: RECOMMEND

Make a clear recommendation with reasoning.

### Template

```markdown
## Recommendation

I recommend **Option B** because:

1. **Fits your constraints**: [explain]
2. **Balances complexity and value**: [explain]
3. **Manages risk**: [explain]

### Implementation Plan

1. First: [step]
2. Then: [step]
3. Finally: [step]

### Risks to Monitor

- Risk 1: [mitigation]
- Risk 2: [mitigation]
```

---

## PRESENTING THE DESIGN

### The 200-300 Word Rule

**Don't dump the entire design at once.** Present it in sections of 200-300 words, checking after each section.

```markdown
❌ FORBIDDEN - Wall of text:
*Dumps 2000-word design document all at once*
"Here's the complete architecture..."

✅ REQUIRED - Sectioned presentation:

"**Section 1: Data Model**
We'll need three tables: users, sessions, refresh_tokens.
Users stores credentials and profile. Sessions tracks active
logins with device info. Refresh_tokens enables token rotation.

Does this data model make sense before I continue to auth flow?"

[Wait for confirmation]

"**Section 2: Authentication Flow**
Login: validate credentials → create session → issue JWT + refresh token.
The JWT expires in 15 minutes, refresh token in 7 days.
On refresh: validate refresh token → rotate it → issue new JWT.

Does this flow work for your needs?"

[Wait for confirmation]
```

### Why This Works

- User can course-correct early
- You don't waste time on wrong designs
- Creates collaborative ownership
- Prevents "I didn't want any of that" moments

---

## PHASE 5: CONFIRM

Get explicit agreement before proceeding.

### Confirmation Questions

```markdown
- Does this approach match what you had in mind?
- Anything I'm missing or misunderstanding?
- Are the tradeoffs acceptable?
- Should I proceed with implementation?
```

**Do not proceed without confirmation.**

---

## Quick Reference: Questions to Ask

### For New Features

```markdown
- What problem does this solve?
- Who uses it and how?
- What does success look like?
- What's the MVP scope?
- Any existing patterns to follow?
```

### For Architecture Decisions

```markdown
- What are the requirements (scale, performance)?
- What are the constraints (budget, timeline)?
- What existing systems must integrate?
- How will this evolve?
- What's the rollback plan?
```

### For Refactoring

```markdown
- What's wrong with current code?
- What's the desired end state?
- Can we do it incrementally?
- What's the test coverage?
- What's the risk of regression?
```

---

## Enforcement

This skill is MANDATORY for significant work:

- **FORBIDDEN**: Start coding without understanding requirements
- **FORBIDDEN**: Assume you know what user wants
- **FORBIDDEN**: Present only one option
- **REQUIRED**: Ask clarifying questions
- **REQUIRED**: Explore alternatives
- **REQUIRED**: Get confirmation before proceeding

**If you start coding without design, you'll build the wrong thing.**

---

## Related Skills

- **test-driven-development** - After design, tests come first
- **systematic-debugging** - When things go wrong
- **skill-developer** - When creating new skills
