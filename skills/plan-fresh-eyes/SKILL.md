---
name: plan-fresh-eyes
description: "Spawn an independent agent (Fable by default, Opus optional) to create a competing plan from session context alone — no existing plan shared. The agent asks questions, you answer or escalate to the user, then compare both plans for the user to combine."
argument-hint: "[optional: brief problem statement]"
---

Generate an independent "fresh eyes" plan by spawning a separate agent that only sees the raw context (research, constraints, decisions) from this session — never the existing plan. Ask which model to use before you spawn it. The agent creates its own plan, then the user compares both and cherry-picks the best ideas into a combined plan.

## Steps

### Step 1: Capture session context

Write everything you know about the current problem to `.claude/fresh-eyes/context.md`. This file is the ONLY thing the second agent will see — it must be self-contained.

Include ALL of the following (skip sections that don't apply):

```markdown
# Fresh Eyes Context

## Problem Statement
What is the problem? What production failures or user pain prompted this work?

## Root Cause Analysis
What did research reveal? Include specific findings — file paths, line numbers,
function signatures, current behavior vs expected behavior.

## Codebase Research
Key files examined, their current state, relevant code patterns.
Include actual code snippets and line numbers for anything the second agent
would need to understand the solution space.

## Constraints & Decisions
What has the user decided? What's locked vs open?
What technical constraints exist (e.g., upcoming migrations, deployment model)?

## Key Questions Discussed
What questions came up during the session? What were the answers?

## Failed Approaches or Rejected Ideas
What was considered and ruled out, and why?
```

Do NOT include:
- Any existing plan or proposed solution — the agent must form its own
- Opinions about the right approach — only facts and constraints
- Summaries of plans you've already written

The context file should be thorough — err on the side of too much detail. The second agent has no conversation history and cannot ask the user for basics.

### Step 2: Ask the user which model to use

Before spawning, ask the user which model they want the fresh-eyes agent to run on:

| Option | Model |
|--------|-------|
| A strong current Claude model | The default planning model in this environment (for example `model: "fable"` or the current Opus), deepest reasoning |
| A cheaper strong Claude model | A mid-tier model (`model: "opus"` or Sonnet) — strong reasoning at lower cost |
| A cross-vendor reviewer | A Codex (or similar) runner — a second opinion from a different vendor |

Use AskUserQuestion with header "Model" to let the user choose.

### Step 3: Spawn the fresh-eyes agent

Spawn a single Agent with the user's chosen model and this prompt structure:

```
You are an independent planning agent. You have been given the full research
context from a session that investigated a problem. Your job is to create
your own implementation plan — you have NOT seen any existing plan and should
not ask for one.

Read the context file at: .claude/fresh-eyes/context.md

Then explore the codebase as needed to verify claims, check current code state,
and understand the architecture. Do not trust the context file blindly — verify
key assertions against the actual code.

IMPORTANT: Before writing your plan, you MUST ask clarifying questions. Return
your questions as a numbered list under a "## Questions" header. For each
question, note whether it could be answered by codebase exploration (tag:
[CODE]) or requires a human decision (tag: [DECISION]).

Do NOT write a plan yet. Only return questions.
```

The agent will return a list of questions.

### Step 4: Answer questions (Q&A loop)

For each question the agent returned:

1. **[CODE] questions**: Search the codebase yourself and find the answer. Send the answer back to the agent via SendMessage.

2. **[DECISION] questions**: Present them to the user using AskUserQuestion (batch up to 4 at a time). Send the user's answers back to the agent via SendMessage.

3. **Questions you can answer from session context**: Answer directly and send back via SendMessage.

When sending answers back, use this format in the SendMessage prompt:

```
Here are the answers to your questions:

1. [answer]
2. [answer]
...

If you have follow-up questions, return them in the same format.
If all questions are resolved, write your full implementation plan now.
Follow the plan format below.
```

Include these plan format instructions:

```
## Plan Format

Start with a narrative overview (2-3 paragraphs) explaining the full scope —
what's being done, why, which parts of the codebase are affected, and how the
pieces fit together. A reader should understand the entire edit from the
narrative alone.

Then provide a detailed implementation section organized by commit or logical
unit. For each change, specify:
- The exact file path
- What changes (function signatures, new code, removed code)
- Why this change is needed (not just what it does)

End with a Verification section (how to confirm correctness) and a
Risks/Notes section (known limitations, future work).
```

Repeat the Q&A loop until the agent stops asking questions and produces a plan. Maximum 3 Q&A rounds — if still asking after 3, instruct it to proceed with best judgment.

### Step 5: Present both plans

Once the fresh-eyes agent returns a plan:

1. Display the fresh-eyes plan to the user under a `## Fresh Eyes Plan` header.

2. Display the original plan (from the current session) under a `## Original Plan` header.

3. Under a `## Comparison` header, present a **table** comparing the two plans line-item by line-item. Each row is a decision point, scope area, or deliverable. Columns: `Area`, `Original Plan`, `Fresh Eyes Plan`, `Stronger`. Example:

   | Area | Original Plan | Fresh Eyes Plan | Stronger |
   |------|---------------|-----------------|----------|
   | Scope of the change | One file, the existing helper | New module plus two call sites | Fresh Eyes |
   | Migration of old records | Covered in detail | Not addressed | Original |
   | ... | ... | ... | ... |

   After the table, add 2-3 sentences summarizing the overall takeaway — which plan is stronger where, and what the combined plan should look like.

### Step 6: Combine

Ask the user:

> "How would you like to combine these plans? You can:
> (a) Adopt one plan wholesale
> (b) Point out specific ideas from the fresh-eyes plan to merge into the original
> (c) Ask me to write a combined plan incorporating the best of both"

If the user picks (c), write the combined plan yourself — do not spawn another agent. You have both plans and the full session context; you are the best-positioned to merge them. Write the combined plan to `.claude/fresh-eyes/combined-plan.md` and also display it in the conversation.

## Cleanup

The `.claude/fresh-eyes/` directory is ephemeral. Files from prior runs may exist — overwrite them. Do not commit these files to git.
