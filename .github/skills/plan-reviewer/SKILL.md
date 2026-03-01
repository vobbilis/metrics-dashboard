---
name: plan-reviewer
description: Use when reviewing a development plan BEFORE implementation. MANDATORY for high-risk plans (migrations, auth changes, integrations). FORBIDDEN is approving without research. REQUIRED is systematic analysis of risks, dependencies, and alternatives.
---

# Plan Review

## THE MANDATE

**Catch the "gotchas" before they become roadblocks.**

Review plans thoroughly before implementation to identify:
- Critical flaws
- Missing considerations
- Incompatible technologies
- Better alternatives

---

## WHEN TO USE THIS SKILL

This skill is MANDATORY for plans involving:

- Database migrations
- Authentication/authorization changes
- Third-party integrations
- Architecture changes
- Breaking changes to APIs
- Data transformations

---

## THE REVIEW PROCESS

```
┌─────────────────────────────────────────────────────────────┐
│  1. UNDERSTAND                                              │
│     What is this plan trying to achieve?                    │
│         ↓                                                   │
│  2. RESEARCH                                                │
│     Verify compatibility, limitations, requirements         │
│         ↓                                                   │
│  3. ANALYZE                                                 │
│     Find gaps, risks, and dependencies                      │
│         ↓                                                   │
│  4. REPORT                                                  │
│     Critical issues, missing items, recommendations         │
└─────────────────────────────────────────────────────────────┘
```

---

## CRITICAL AREAS TO EXAMINE

### Authentication/Authorization

```markdown
- [ ] Compatible with existing auth system?
- [ ] Token handling correct?
- [ ] Session management addressed?
- [ ] SSO/OAuth requirements met?
- [ ] Security implications considered?
```

### Database Operations

```markdown
- [ ] Migration strategy safe?
- [ ] Rollback plan exists?
- [ ] Index strategy defined?
- [ ] Data validation covered?
- [ ] Transaction handling correct?
- [ ] Performance at scale considered?
```

### API Integrations

```markdown
- [ ] Endpoints actually available?
- [ ] Rate limits accounted for?
- [ ] Authentication documented?
- [ ] Error handling planned?
- [ ] Retry logic defined?
```

### Dependencies

```markdown
- [ ] Version conflicts checked?
- [ ] Deprecated features avoided?
- [ ] Compatibility verified?
- [ ] License acceptable?
```

---

## GAP ANALYSIS

### What's Often Missing

| Area | Common Gaps |
|------|-------------|
| Error Handling | What if API returns 500? What if DB is down? |
| Rollback | How do we undo this if it breaks? |
| Testing | How will we verify this works? |
| Monitoring | How will we know if it fails in production? |
| Edge Cases | What about empty data? Null values? Timeouts? |
| Performance | What happens with 10x current load? |
| Security | Input validation? SQL injection? XSS? |

### Questions to Ask

```markdown
For each plan step, ask:
1. What could go wrong here?
2. How would we detect failure?
3. How would we recover from failure?
4. What assumptions are we making?
5. What dependencies does this have?
```

---

## RESEARCH CHECKLIST

Before approving a plan:

```markdown
- [ ] Verified API endpoints exist and work as expected
- [ ] Checked library documentation for limitations
- [ ] Looked for known issues/bugs in dependencies
- [ ] Confirmed compatibility with existing stack
- [ ] Validated that approach has worked for others (GitHub issues, SO)
```

---

## OUTPUT FORMAT

```markdown
# Plan Review: [Plan Name]

## Executive Summary
[1-2 sentences: Is this plan viable? Major concerns?]

## Critical Issues (Must Address)
1. [Issue]: [Why it matters] [Recommendation]
2. ...

## Missing Considerations
- [Item not covered in plan]
- ...

## Alternative Approaches
[If a simpler/better solution exists]

## Dependencies & Risks
| Dependency | Risk | Mitigation |
|------------|------|------------|
| ... | ... | ... |

## Recommendation
[ ] Approved - Ready to implement
[ ] Approved with changes - Address [specific items] first
[ ] Needs revision - [Major concerns that block implementation]
```

---

## EXAMPLE: Catching A Gotcha

```markdown
## Plan: Use HTTPie for API Testing

### Plan Says:
"We'll use HTTPie instead of curl for easier API testing with 
our Keycloak authentication."

### Review Finding:
❌ CRITICAL ISSUE: HTTPie doesn't support the specific cookie-based
JWT authentication pattern used by our Keycloak integration. 

HTTPie can't:
- Sign cookies with JWT secrets
- Handle the refresh token flow
- Work with our SSO middleware pattern

### Recommendation:
Keep using the existing test-auth-route.js script which handles 
all authentication complexity correctly.

### Result:
Saved hours of implementation time on a doomed approach.
```

---

## ENFORCEMENT

This skill is MANDATORY for plan review:

- **FORBIDDEN**: Approve without research
- **FORBIDDEN**: Skip compatibility checks
- **FORBIDDEN**: Ignore rollback planning
- **REQUIRED**: Verify all technologies work together
- **REQUIRED**: Identify missing error handling
- **REQUIRED**: Check for better alternatives

**A thorough plan review prevents costly implementation failures.**

---

## Related Skills

- **writing-plans** - Create plans to be reviewed
- **executing-plans** - Execute after review
- **brainstorming** - Design before planning
