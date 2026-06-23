---
description: Investigate and fix bugs systematically. Trace root cause, verify assumptions, implement minimal fixes, test affected flows, and summarize changes without introducing unrelated modifications.
---

# Debug Issue Workflow

When debugging any issue in Investo, follow this exact process:

## Step 1: Understand the Problem
- Read the error completely.
- Identify:
  - Expected behavior
  - Actual behavior
  - Affected module
  - Reproduction steps

Never start coding before understanding the issue.

---

## Step 2: Investigate First
Search relevant files and trace the flow:

Frontend:
- Page
- Component
- Hook
- API client

Backend:
- URL
- View
- Service
- Repository
- Model

Find the actual root cause.

Do not guess.

---

## Step 3: Explain Root Cause
Before modifying code, provide:

- Root cause
- Files affected
- Proposed fix
- Why the fix works

Keep explanation concise.

---

## Step 4: Implement Minimal Fix
Rules:

- Fix only the affected area.
- Preserve existing architecture.
- Follow View → Service → Repository pattern.
- Do not introduce hacks.
- Do not create duplicate logic.
- Do not refactor unrelated code.

---

## Step 5: Verify
After implementing:

- Check imports.
- Check type errors.
- Check API contracts.
- Check frontend integration.
- Check affected user flows.

---

## Step 6: Report
Provide:

### Root Cause
...

### Files Modified
...

### Fix Applied
...

### Validation Performed
...

### Remaining Risks
...

---

Investo Context:

Current phase:
- Frontend integration
- UI/UX polish
- Bug fixing
- End-to-end testing
- Production readiness

Do NOT:
- Build new features
- Introduce paid services
- Perform large refactors
- Change deployment infrastructure
- Add placeholder code

Always prefer the smallest correct fix.