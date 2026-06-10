---
name: terminal-discipline
description: Use when running ANY terminal command. MANDATORY for all terminal interactions. FORBIDDEN is running a new command while another is in progress. FORBIDDEN is interrupting long-running tests or builds. REQUIRED is using isBackground=true for commands >30 seconds, then get_terminal_output to check status.
---

# Terminal Discipline

## THE MANDATE

**NEVER run a new terminal command while one is in progress.**

Running a new command interrupts the previous one. This destroys:
- E2E test runs (2-5 minutes)
- Build processes (30-120 seconds)
- Server startups
- Any long-running operation

---

## WHY THIS SKILL EXISTS

### The Incident Pattern (Repeated Multiple Times)

```
1. Run E2E test (takes 3 minutes)
2. Get "impatient" after 30 seconds
3. Run another command to "check status"
4. Previous command INTERRUPTED
5. Test results lost
6. Have to start over
7. Repeat mistake
```

This has happened multiple times in this session alone.

---

## FORBIDDEN PATTERNS

### ❌ Running Commands While Another Is In Progress - ABSOLUTELY BANNED

```markdown
❌ FORBIDDEN:
*Runs E2E test*
*Waits 30 seconds*
"Let me check the status..."
*Runs new command*
*E2E test interrupted*

✅ REQUIRED:
*Runs E2E test with isBackground=true*
*Uses get_terminal_output to check*
OR
*Waits for user to confirm completion*
```

### ❌ "Checking Status" With New Commands - BANNED

```markdown
❌ FORBIDDEN:
"Let me see if the server is ready"
*Runs curl command*
*Interrupts server startup*

✅ REQUIRED:
Use get_terminal_output tool
OR
Ask user: "Is the server ready?"
```

### ❌ Impatient Command Chaining - BANNED

```markdown
❌ FORBIDDEN:
*Command takes longer than expected*
"That's taking a while, let me try..."
*Runs another command*

✅ REQUIRED:
WAIT.
If truly stuck, ask user: "The command seems to be taking long. Should I check on it?"
```

---

## REQUIRED PATTERNS

### ✅ Long-Running Commands (>30 seconds)

For tests, builds, or any command expected to take >30 seconds:

```markdown
REQUIRED approach:

1. Use isBackground=true:
   run_in_terminal(
     command: "cargo test --release",
     isBackground: true,
     explanation: "Running tests in background"
   )

2. Inform user:
   "Running tests in background. This will take ~2 minutes."

3. To check status, use get_terminal_output:
   get_terminal_output(id: "<terminal_id>")

4. NEVER run a new command to "check"
```

### ✅ Server Processes

```markdown
REQUIRED approach:

1. Start server with isBackground=true:
   run_in_terminal(
     command: "./start_server.sh",
     isBackground: true,
     explanation: "Starting server in background"
   )

2. Wait for user confirmation:
   "Server starting. Please let me know when it's ready, or I can check with get_terminal_output."

3. NEVER run curl/wget to "test" while server is starting
```

### ✅ Sequential Commands

When you need to run multiple commands:

```markdown
REQUIRED approach:

1. Run first command (isBackground=false for short commands)
2. WAIT for it to complete
3. Observe output
4. THEN run next command

NEVER run parallel commands in separate terminals
unless explicitly confirmed by user
```

### ✅ When You Don't Know If Command Is Done

```markdown
REQUIRED approach:

ASK THE USER:
"Is the previous command still running?"
"Should I wait longer?"
"Can I proceed with the next step?"

DO NOT assume and run another command
```

---

## COMMAND DURATION GUIDE

| Command Type | Expected Duration | Approach |
|--------------|-------------------|----------|
| `cargo build` | 30-120s | isBackground=true |
| `cargo build --release` | 60-180s | isBackground=true |
| `cargo test` | 30-300s | isBackground=true |
| E2E tests | 120-600s | isBackground=true |
| Server startup | 5-30s | isBackground=true |
| `git` commands | <5s | isBackground=false |
| `grep/find` | <10s | isBackground=false |
| `curl` health check | <5s | isBackground=false |

---

## DECISION TREE

```
Need to run a terminal command?
            │
            ▼
┌─────────────────────────┐
│ Is another command      │
│ currently running?      │
└───────────┬─────────────┘
            │
     ┌──────┴──────┐
     │             │
    YES            NO
     │             │
     ▼             ▼
┌─────────┐  ┌──────────────┐
│ STOP!   │  │ Estimate     │
│ DO NOT  │  │ duration     │
│ PROCEED │  └──────┬───────┘
└─────────┘         │
                    ▼
            ┌───────────────┐
            │ >30 seconds?  │
            └───────┬───────┘
                    │
             ┌──────┴──────┐
             │             │
            YES            NO
             │             │
             ▼             ▼
      isBackground    isBackground
      = true          = false
             │             │
             ▼             ▼
      Use get_terminal   Wait for
      _output to check   completion
```

---

## CHECKLIST

### Before Running ANY Command

- [ ] Is another command currently running? → If YES, STOP
- [ ] Will this take >30 seconds? → If YES, use isBackground=true
- [ ] Am I running this to "check on" something? → Use get_terminal_output instead

### During Long-Running Commands

- [ ] DO NOT run new commands
- [ ] Use get_terminal_output if you need status
- [ ] Or ask user for status update

### When Tempted to "Check Status"

- [ ] STOP
- [ ] Use get_terminal_output tool
- [ ] Or ask user: "Is it done?"
- [ ] NEVER run a new command

---

## ABSOLUTE RULES

1. **ONE command at a time** - No exceptions
2. **isBackground=true for >30s commands** - No exceptions  
3. **get_terminal_output for status** - Never run new commands to check
4. **When in doubt, ASK** - Don't assume and interrupt

---

## SELF-CHECK QUESTIONS

Before every terminal command, ask yourself:

1. "Is something already running?" → CHECK FIRST
2. "Will this interrupt something?" → IF YES, DON'T DO IT
3. "Can I use get_terminal_output instead?" → PREFER IT
4. "Should I just wait?" → PROBABLY YES
