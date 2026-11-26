---
name: review-super
description: "Review the current branch's diff for bugs that will actually break something, then fix or refute each finding. Stage 1 is one fresh reviewer with no build context; Stage 2, when the Codex CLI is installed, is a second reader from another vendor over the whole repo. A finding must quote the line that makes it true or it is dropped. Use before opening or merging a PR, or when asked for a 'super review', 'deep review' or 'review and fix'."
argument-hint: "[base branch | staged | report-only | full]"
---

# review-super

Two readers, each followed by a fix pass. Stage 1 is a fresh reviewer that knows nothing about how the change was built. Stage 2 is a model from another vendor (Codex), because two models from one family tend to miss the same things. Every finding must quote the line that makes it true; anything else is dropped. Every finding that survives goes to a fix agent, which either fixes it or refutes it.

**Arguments:** a base branch (default `main`, else `master`) · `staged` reviews only staged changes · `report-only` stops after Stage 1 with findings and no edits · `full` runs Stage 2 even when the gate below would skip it.

This skill does not commit unless the user asked for that, and it never pushes, opens PRs or merges.

## Setup

1. Diff: `staged` → `git diff --cached`; otherwise `git diff <base>...HEAD`. An empty diff → say "Nothing to review" and stop.
2. Context for the reviewers: the root `CLAUDE.md` / `AGENTS.md` and the nested one in each touched directory, `git log <base>..HEAD --oneline`, and the issue or task description if the user gave one.
3. Pick one scratch directory for the run, e.g. `/tmp/review-super-<branch>`, and use its literal path in every command (shell variables do not persist between calls).
4. Note two flags from the changed file list:
   - **AUTHORITY**: the diff changes authentication, sessions, permissions, roles, or the tools an AI agent can call (test and doc files don't count).
   - **MIGRATION**: the diff adds or changes a database migration or schema file.

## The reviewer contract

Paste this into every reviewer prompt, followed by the schema.

> **Framing.** Confirm this diff is safe to merge. Report only what will actually break, misbehave, or violate a written rule. An empty report is a valid and common result. You are not rewarded for volume.
>
> **Confidence is one of five anchors.** `0` does not hold up · `25` could not verify from the code · `50` real but a nitpick, edge case, or taste · `75` you double-checked and can name a concrete consequence a user, caller or operator will hit · `100` provable from the code itself (type mismatch, swapped argument, quotable rule violation). Never emit 0 or 25.
>
> **Quote the line.** Every finding's first `evidence` item is the verbatim line(s) that make it true, with `file:line`. "Field X doesn't exist" → quote where X would be defined. "May be None" → quote the initialization. "Race between A and B" → quote both. A failed grep is not evidence. No quoted line, no finding.
>
> **Never report:** pre-existing issues the diff does not interact with (a dormant bug the diff newly exposes is a finding) · anything a linter, formatter or type-checker catches · code that is intentional per a comment, commit message or surrounding code · issues a caller, guard, middleware or framework default already handles · "consider adding" with no named failure · quality complaints with no written rule behind them · speculative future concerns with no signal in this diff.

When **AUTHORITY** is set, add:

> Authority check. This diff touches auth, permissions or agent tools. For each thing the change trusts, allows or restores, ask who controls it and what else it opens. Can a user or another agent supply something the code then treats as genuine? Does permission for one action also grant a stronger action through the same gate? Can a late or stale result undo a security decision that came after it? A request in the issue does not make the side effects of that request safe; report them.

When **MIGRATION** is set, add:

> Deploy overlap. A migration runs before the new code takes traffic, so the old code serves alone on the new schema until the rollout ends. Report any statement of the old code that then fails or writes a wrong value. A sequence that needs both versions running at once is not a finding.

Schema, one JSON array:
```json
[{"title":"…","severity":"P0|P1|P2|P3","confidence":50,"file":"path","line":42,"evidence":["path:42: <verbatim line>"],"consequence":"what a user or caller hits","suggested_fix":"specific change"}]
```
Severity: P0 crash, data loss or security · P1 wrong behavior · P2 edge case · P3 minor.

## The gate and the fix agent

After each reviewer: for every finding, check that its first evidence line really exists at that `file:line` (`sed -n '<line>p' <file>`). Drop it if not, and drop anchors 0 and 25. Count the drops.

Then one fix agent (a fresh subagent) takes each surviving finding: reads the code, then fixes it or refutes it with a one-line reason, by running a test or a repro where it can. A finding that needs a human decision it can neither fix nor refute is listed as `human: <title>: <the decision needed>`; stop after that stage and ask the user. No findings survive the gate → skip the fix agent. The fix agent follows the repo's own test rules, does not commit, and lists the files it changed.

## Stage 1: one fresh reviewer

Spawn one subagent with no context from this session. Give it the diff, the task description, the `CLAUDE.md` files and the contract, and tell it:

> You are reviewing a change you did not write. Read the task description, then the diff, then any file in the repository you need. Do not edit anything. Look for what will actually break, including callers of changed functions and input crossing a trust boundary, and for:
> - **The ask.** Anything the task asked for that is missing or narrowed, and anything changed that it did not ask for.
> - **Rules and tests.** Violations of a written rule in `CLAUDE.md` (quote the rule); changed behavior whose test is missing or would still pass against a broken implementation.
>
> Write your findings as one JSON array to `<scratch>/stage1.json` and reply with one line: `written: <path> (<count> findings)`.

Read the file, apply the gate, run the fix agent.

`report-only` stops here: list the gated findings by severity with `file:line`, confidence, the quoted evidence, consequence and suggested fix, then a verdict (Ready to merge / Needs attention).

## Stage 2: another vendor, whole repo

**Install a second-vendor reviewer.** This stage does most of the catching. In one team's November runs, it raised a P0/P1 on about a quarter of diffs that a same-vendor Stage 1 had already passed. Without the Codex CLI (`npm i -g @openai/codex`, then sign in), you get half the review.

Run when the Codex CLI is installed (`command -v codex`) and the diff changes backend, data, auth or infrastructure code, or Stage 1 raised a P0/P1, or `full` was passed. A frontend-only diff with a clean Stage 1 stops here. No Codex CLI → say "Stage 2 skipped: Codex not installed. Install it: a second-vendor reviewer catches what the first one misses" in the summary and stop.

```bash
git diff <base>...HEAD > <scratch>/diff.txt
codex exec --sandbox read-only -c model_reasoning_effort=high -C <repo-root> -o <scratch>/stage2.md \
  "Review the unified diff on stdin against its task. The current directory is the whole repository: read any file, because a bug often sits where a changed thing is used. <CONTRACT> Output one JSON array in the schema." \
  < <scratch>/diff.txt
```

Allow up to 10 minutes. If Codex fails, report the error and stop; do not substitute a Claude reviewer and call it Stage 2. Otherwise read `stage2.md`, apply the gate, run the fix agent. If a P0/P1 was fixed, run Codex once more on the new diff, adding: "I made edits based on your previous review. Are my fixes correct, did I introduce new issues, what remains?"

## Summary

```
## Review complete
| Stage | Reviewer | Findings | Fixed | Refuted | Dropped |
| 1 | <model> | N | N | N | N |
| 2 | Codex, or skipped: <reason> | N | N | N | N |
```
Then **Needs a human** (the `human:` lines) and a **Verdict**: Ready to merge / Ready with caveats / Needs attention. Delete the scratch directory.
