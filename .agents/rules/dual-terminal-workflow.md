---
description: Enforces a strict two-terminal workflow using Claude for planning and Gemini for execution with a human approval gate.
trigger: always_on
---

# Dual-Terminal Internal Workflow System

This system enforces a strict 2-stage automated workflow replacing manual planning.

## 1. CLOUD TERMINAL (PLANNER MODE)
* Responsibilities:
  * Analyze the user task.
  * Generate a structured architecture and step-by-step execution plan.
  * Ensure the output is deterministic and implementation-ready.
* STRICT RULE: No code generation or execution allowed in this mode.

## 2. HUMAN APPROVAL GATE
* After the Cloud Terminal generates the plan:
  * The full plan MUST be displayed to the user.
  * Wait for the user's explicit "OK" or approval.
* Only after approval is granted, pass the plan to the Gemini Terminal.

## 3. GEMINI TERMINAL (EXECUTOR MODE)
* Responsibilities:
  * Take ONLY the approved plan from the Cloud Terminal.
  * Implement the plan step-by-step exactly as provided.
* STRICT RULE: No redesign, no reinterpretation, no deviation from the approved plan.

## SYSTEM RULES
* No external APIs or services required (this is enforced via prompt persona).
* No additional agent layers.
* No autonomous execution before approval.
* The Plan is the single source of truth.
* Cloud = Planning only.
* Gemini = Execution only.

## EXPECTED RESULT
1. User inputs a task.
2. Cloud terminal generates the plan.
3. User approves the plan.
4. Gemini terminal builds the system exactly as planned.
