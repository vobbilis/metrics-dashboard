---
name: receiving-code-review
description: Use when you receive code review feedback on your PR. MANDATORY when responding to reviews. FORBIDDEN is dismissing feedback or arguing. REQUIRED is addressing every comment constructively.
---

# Receiving Code Review

## THE MANDATE

**Every review comment deserves a response.**

When you receive code review feedback:
1. Thank the reviewer
2. Address every comment
3. Don't take it personally
4. Learn from feedback

---

## THE MINDSET

### Reviews Are Gifts

```markdown
A reviewer spent their time to:
- Read your code carefully
- Think about edge cases
- Share their experience
- Help you improve

Respond with gratitude, not defensiveness.
```

### It's About The Code, Not You

```markdown
❌ WRONG MINDSET:
"They think I'm a bad developer"

✅ RIGHT MINDSET:
"They found ways to improve the code"
```

---

## FORBIDDEN PATTERNS

### ❌ Dismissing Feedback - BANNED

```markdown
❌ FORBIDDEN:
"That's just style preference"
"It works fine as is"
"We can fix that later"
"That's out of scope"

✅ REQUIRED:
Consider the feedback genuinely.
If you disagree, explain why respectfully.
```

### ❌ Arguing - BANNED

```markdown
❌ FORBIDDEN:
"No, you're wrong because..."
"That doesn't make sense"
"I've been doing it this way for years"

✅ REQUIRED:
"I see your point. My reasoning was X, but I understand
your concern about Y. Would Z be a good compromise?"
```

### ❌ Ignoring Comments - BANNED

```markdown
❌ FORBIDDEN:
*Reviewer leaves 5 comments*
*Developer addresses 2, ignores 3*

✅ REQUIRED:
Address ALL comments, even if just to say:
"Acknowledged" or "Fixed" or "Let's discuss"
```

### ❌ Silent Changes - BANNED

```markdown
❌ FORBIDDEN:
*Makes changes without responding to comments*

✅ REQUIRED:
Respond to each comment, then make changes:
"Good catch! Fixed in commit abc123"
```

---

## HOW TO RESPOND

### For Valid Feedback

```markdown
Reviewer: "This could cause a null pointer if user is undefined"

✅ RESPONSE:
"Good catch! I added a null check. Fixed in abc123."
```

### For Suggestions You'll Implement

```markdown
Reviewer: "Consider using a Map here for O(1) lookup"

✅ RESPONSE:
"Great suggestion! Changed to Map in abc123. 
Performance improved from O(n) to O(1)."
```

### For Suggestions You Disagree With

```markdown
Reviewer: "Should use class instead of function"

✅ RESPONSE:
"I considered that, but went with function because:
1. No state needed
2. Easier to test
3. Follows our codebase pattern

Would you like to discuss further?"
```

### For Questions

```markdown
Reviewer: "Why did you use approach X instead of Y?"

✅ RESPONSE:
"X handles edge case Z better than Y because [reason].
I documented this in the comment on line 45."
```

### For Style Preferences

```markdown
Reviewer: "I prefer early returns here"

✅ RESPONSE:
"Makes sense for readability. Refactored to early returns."

OR

"I find the current structure clearer for this case because
of the multiple conditions. WDYT?"
```

---

## THE RESPONSE TEMPLATE

For each comment:

```markdown
**Comment:** [Quote the reviewer's comment]
**Response:** [Your response]
**Action:** Fixed in [commit] | Will discuss | No change (with reason)
```

---

## RESPONSE MATRIX

| Feedback Type | Response | Action |
|---------------|----------|--------|
| Bug found | "Good catch!" | Fix it |
| Better approach | "Great idea!" | Implement |
| Valid concern | "You're right" | Address it |
| Disagree | "My reasoning is..." | Discuss |
| Unclear | "Can you clarify?" | Ask |
| Style preference | "Makes sense" | Usually adopt |
| Nitpick | "Fixed" | Fix it |

---

## WHEN YOU DISAGREE

It's okay to disagree, but do it constructively:

### The Formula

```markdown
1. Acknowledge their point
2. Explain your reasoning
3. Propose resolution
4. Stay open

"I see why you'd suggest that. My reasoning for the current
approach was [X]. However, I'm open to changing it if you
think [Y] is important. What do you think?"
```

### Don't Die On Every Hill

```markdown
Ask yourself:
- Is this worth the discussion time?
- Will the codebase suffer if I change it?
- Am I just being defensive?

Sometimes it's better to just change it and move on.
```

---

## HANDLING MULTIPLE REVIEWERS

When reviewers disagree with each other:

```markdown
Reviewer A: "Use approach X"
Reviewer B: "Use approach Y"

✅ RESPONSE:
"I see different perspectives here:
- A suggests X for [reason]
- B suggests Y for [reason]

My take: [Your analysis]

Can we align on which approach to use?"
```

---

## AFTER ADDRESSING FEEDBACK

```markdown
## Review Response Summary

**Reviewer:** @username
**Comments:** 8 total

### Addressed
- ✓ Comment 1: Fixed null check (abc123)
- ✓ Comment 2: Added error handling (def456)
- ✓ Comment 3: Renamed variable (def456)
- ✓ Comment 4: Added test case (ghi789)
- ✓ Comment 5: Updated documentation (jkl012)

### Discussed
- Comment 6: Agreed to keep current approach (see thread)
- Comment 7: Will address in follow-up PR (linked to ticket)

### Questions
- Comment 8: Asked for clarification (awaiting response)

**Ready for re-review.**
```

---

## LEARNING FROM REVIEWS

After the PR is merged:

```markdown
## What I Learned

- Always check for null before accessing properties
- Use early returns for cleaner code
- Consider performance for loops over large collections
- Update docs when changing public APIs

Add to personal checklist for next time.
```

---

## ENFORCEMENT

This skill is MANDATORY when receiving reviews:

- **FORBIDDEN**: Dismiss feedback
- **FORBIDDEN**: Argue defensively
- **FORBIDDEN**: Ignore comments
- **FORBIDDEN**: Make silent changes
- **REQUIRED**: Respond to every comment
- **REQUIRED**: Thank reviewers
- **REQUIRED**: Address feedback constructively
- **REQUIRED**: Learn from feedback

**Reviews make you better. Embrace them.**

---

## Related Skills

- **requesting-code-review** - Before you receive feedback
- **finishing-a-development-branch** - After review approval
