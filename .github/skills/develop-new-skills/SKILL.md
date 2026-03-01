---
name: skill-developer
description: Use when creating new skills, editing existing skills, or helping teammates add skills. MANDATORY for anyone modifying the .github/skills directory. Covers YAML frontmatter format, description best practices, the 500-line rule, and team extensibility patterns.
---

# Creating and Managing Skills

## THE MANDATE

Skills are **mandatory workflows, not suggestions**. When you create a skill, you're creating a rule that the AI MUST follow.

---

## Skill Structure

Every skill lives in `.github/skills/{skill-name}/SKILL.md`

### Required Format

```markdown
---
name: skill-name
description: Use when [specific triggers]. MANDATORY for [situations]. FORBIDDEN patterns include [anti-patterns]. REQUIRED patterns are [correct approaches].
---

# Skill Title

## THE MANDATE

What MUST happen when this skill applies.

## FORBIDDEN PATTERNS

What to NEVER generate.

## REQUIRED PATTERNS  

What to ALWAYS use.

## Checklists

Step-by-step requirements.
```

---

## Description Best Practices

The description is **THE trigger mechanism**. The AI reads descriptions to decide which skill applies.

### REQUIRED Format

```yaml
description: Use when [triggers]. MANDATORY for [scope]. FORBIDDEN patterns include [anti-patterns]. REQUIRED patterns are [correct approaches].
```

### Examples

**❌ BAD - Vague, no triggers:**
```yaml
description: Frontend development guidelines for React applications.
```

**✅ GOOD - Specific triggers:**
```yaml
description: Use when creating ANY React component, UI element, button, form, or styled element. MANDATORY for all frontend code. FORBIDDEN patterns include inline styles. REQUIRED patterns are MUI sx prop.
```

**❌ BAD - Describes what skill does:**
```yaml
description: Helps with error handling by showing Sentry patterns.
```

**✅ GOOD - Describes when to use:**
```yaml
description: Use when writing ANY catch block, try/catch, or error handling. MANDATORY for all code that can fail. FORBIDDEN is console.error without Sentry.
```

### Key Principles

1. **Start with "Use when"** - Focus on triggers
2. **Include "MANDATORY for"** - State scope
3. **Include "FORBIDDEN"** - What to never do
4. **Include "REQUIRED"** - What to always do
5. **Max 1024 characters** - Keep it scannable

---

## The 500-Line Rule

**Keep SKILL.md under 500 lines.**

If you need more:
- Create reference files in the same directory
- Link to them: `See [details.md](details.md)`
- Keep SKILL.md as the overview

```
skills/
  my-skill/
    SKILL.md           # < 500 lines - overview
    patterns.md        # Detailed patterns
    examples.md        # More examples
    reference.md       # API reference
```

---

## Authoritative Language

Use MANDATORY language - skills are not suggestions:

| Word | Meaning |
|------|---------|
| **MUST** | Required, no exceptions |
| **FORBIDDEN** | Never generate this |
| **REQUIRED** | Always do this |
| **BANNED** | Absolute prohibition |
| **NEVER** | Under no circumstances |

**Examples:**
```markdown
## FORBIDDEN PATTERNS

❌ **BANNED** - Never generate inline styles
❌ **FORBIDDEN** - console.error without Sentry

## REQUIRED PATTERNS

✅ **MUST** use sx prop for styling
✅ **REQUIRED** Sentry.captureException in catch blocks
```

---

## Skill Checklist Template

Every skill should have checklists:

```markdown
## Checklist

### Before Starting

- [ ] Item one
- [ ] Item two

### Required Steps

- [ ] Step one
- [ ] Step two
- [ ] Step three

### Verification

- [ ] Verify item one
- [ ] Verify item two
```

---

## Adding a New Skill (For Your Team)

### Step 1: Create Directory

```bash
mkdir -p .github/skills/my-new-skill
```

### Step 2: Create SKILL.md

```bash
cat > .github/skills/my-new-skill/SKILL.md << 'EOF'
---
name: my-new-skill
description: Use when [specific triggers]. MANDATORY for [scope]. FORBIDDEN patterns include [anti-patterns]. REQUIRED patterns are [correct approaches].
---

# My New Skill

## THE MANDATE

[What MUST happen]

## FORBIDDEN PATTERNS

[What to NEVER do]

## REQUIRED PATTERNS

[What to ALWAYS do]

## Checklist

- [ ] Required step 1
- [ ] Required step 2
EOF
```

### Step 3: Test the Skill

Ask: "I need to [task that should trigger skill]"

Verify the AI:
1. Reads the skill
2. Announces using it
3. Follows the patterns

### Step 4: Iterate

If the AI doesn't trigger on expected prompts:
- Add more trigger words to description
- Make triggers more specific
- Add FORBIDDEN/REQUIRED keywords

---

## Common Skill Types

### Domain Skill (Guidelines)

```yaml
description: Use when working on [domain]. MANDATORY for all [domain] code. FORBIDDEN patterns include [anti-patterns].
```

### Process Skill (Workflow)

```yaml
description: Use when [starting activity]. MANDATORY before [action]. Follow this process exactly.
```

### Debugging Skill (Investigation)

```yaml
description: Use when encountering [symptoms]. MANDATORY for systematic investigation. Do not guess - follow this process.
```

---

## File Organization

```
.github/
  skills/
    using-skills/              # Master skill - read first
      SKILL.md
    frontend-dev-guidelines/   # Domain skills
      SKILL.md
    backend-dev-guidelines/
      SKILL.md
    error-tracking/
      SKILL.md
    test-driven-development/   # Process skills
      SKILL.md
    systematic-debugging/
      SKILL.md
    brainstorming/
      SKILL.md
    skill-developer/           # Meta skill (this one)
      SKILL.md
    README.md                  # Team documentation
```

---

## Enforcement

When creating skills:

- **MUST** use authoritative language
- **MUST** include FORBIDDEN and REQUIRED sections
- **MUST** keep under 500 lines
- **MUST** start description with "Use when"
- **MUST** include checklists

Skills without these elements will be ineffective.
