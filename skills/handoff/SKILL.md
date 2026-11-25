---
name: handoff
description: Write a handoff document summarising the current conversation (or a referenced part of it) so a fresh agent can continue the work — saved to the OS temp directory, never the workspace. Returns the file link plus a starter paragraph for the next session. Use when the user says "handoff", "write a handoff", or "hand this off".
argument-hint: "What will the next session focus on? (optional)"
disable-model-invocation: true
---

# Handoff — Compact the conversation for a fresh agent

Write a **handoff document** that lets a brand-new agent — one with **none** of this conversation's
context — pick up the work and continue it smoothly. It summarises the current conversation, or the
**referenced part** of this session when the user names one (e.g. "a handoff for the SDS migration"
in a session that did many things). Save it to the **OS temporary directory**, never the workspace.

`$ARGUMENTS`, if present, describes what the **next** session will focus on. Treat it as the lens: foreground
the state relevant to that goal and background the rest. If it's empty, write a general-purpose handoff of
wherever the work currently stands.

The handoff is **connective tissue between artifacts**, not a copy of them. A fresh agent should be able to
resume from this document plus the artifacts it references — without ever reading this transcript.

## Where to save

Save to the **OS temporary directory** of the user's machine — NOT the repo / current workspace, and not
a folder inside it:

- macOS / Linux: `${TMPDIR:-/tmp}/handoff-<short-slug>-<YYYYMMDD-HHMMSS>.md` (on macOS `$TMPDIR` is the
  per-user `/var/folders/…/T/` directory — use it as-is)
- Windows: `%TEMP%\handoff-<short-slug>-<YYYYMMDD-HHMMSS>.md`

Pick a short, descriptive `<short-slug>` (derive it from `$ARGUMENTS` or the referenced topic). Generate the
timestamp with `date +%Y%m%d-%H%M%S`.

## What to deliver back to the user

Two things, in this order, and nothing else of substance:

1. **The link** — the full absolute path of the saved file (so it can be copied or opened).
2. **A starter paragraph** — one paragraph of plain text the user can paste as the first message of the
   next session to get it going: what to read first (the handoff path), the focus, and the first concrete
   action. Write it addressed to the next agent, not to the user.

Refresh anything you are about to assert (PR/issue state, CI, whether something was merged while you
were not looking) with cheap read-only commands before writing — a handoff built from stale memory sends
the next agent down a closed path.

## What to include

Write for an agent with zero prior context — concrete and self-contained, but **do not duplicate** anything
that already lives in another artifact (reference it instead — see Rules).

1. **Objective** — what we're ultimately trying to achieve (1–3 sentences). If `$ARGUMENTS` was given, open
   with what the next session should focus on.
2. **Current status** — where things stand right now: what's done, what's in progress, what's blocked, and
   the single most useful **next action**.
3. **Key decisions & rationale** — the non-obvious choices made and *why*, so the next agent doesn't
   relitigate them. Summarize; link to any plan/ADR that holds the full detail.
4. **Context the transcript won't make obvious** — gotchas, constraints, dead ends already ruled out,
   surprises, assumptions in force.
5. **Artifacts (reference, don't repeat)** — plans, PRDs, ADRs, issues, PRs, branches, commits, diffs, and
   key files, each by **path or URL**. Do not paste their contents.
6. **Environment** — working directory, git branch, relevant services/ports, and the setup steps needed to
   resume (where config/secrets live — by path, not value).
7. **Open questions / risks** — what's unresolved or needs the user's input.
8. **Suggested skills** — see below.

## Suggested skills section

Always include a **"Suggested skills"** section listing the skills the next agent should invoke, and *when*.
Choose only from skills actually available in the target environment (check the running agent's skill list,
`~/.claude/skills/`, and the project's `.claude/skills/` — do not invent skill names). For each: the skill
name and a one-line "use this to …", ordered by likely sequence. If none clearly apply, say so explicitly.

## Rules

- **Reference, don't duplicate.** If content already exists in a PRD, plan, ADR, issue, commit message, or
  diff, link it by path/URL — never paste it. Duplication rots; pointers stay fresh.
- **Redact secrets.** Never write API keys, tokens, passwords, connection strings, or PII into the document.
  Replace with `‹redacted›` and note where the real value lives (e.g. "in `~/path/to/.env`"), so the next
  agent knows the source without exposing the value.
- **Lean and self-contained.** Enough to resume from the doc + referenced artifacts alone; no transcript
  archaeology required.
- **Tailor to `$ARGUMENTS`.** Weight the whole document toward the next session's stated focus.

## Steps

1. Resolve the OS temp directory (`${TMPDIR:-/tmp}` / `%TEMP%`) and build the filename (slug + timestamp).
2. Refresh live state (PRs, issues, CI, background work) with read-only commands; decide whether the
   handoff covers the whole conversation or the part the user referenced.
3. Scan the conversation for: objective, status, decisions, artifacts (paths/URLs), environment, open
   questions — filtered through the `$ARGUMENTS` lens.
4. Identify the relevant available skills for the "Suggested skills" section.
5. Draft the document per the structure above: reference artifacts instead of duplicating them, and redact
   every secret/PII.
6. Write the file, then reply with the full path and the starter paragraph (see "What to deliver").
