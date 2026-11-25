---
name: recap
description: Refresh stale state (PRs, CI, background jobs/agents), then report exactly four things — the goal in the requester's words, actual state with evidence, person-blocked vs technically-blocked, and owner-tagged next steps. Read-only; starts no new work. Use when the user asks "status?", "where are we?", "recap", or returns to a long-running session.
---

Give me a recap of this session's work. A recap is a **read-only** operation: you must not start, resume, fix, retry, or push anything while producing it. If refreshing reveals something broken, that goes in the report as a finding — acting on it waits until I respond.

## Step 1 — Refresh (spend a minute or two, no more)

Anything you'd report on may have changed since you last looked. Re-check whatever applies before writing a word:

- **PRs**: current state via `gh pr view`/`gh pr checks` — CI results, mergeability, new review comments, whether someone merged or closed while you weren't looking.
- **Background jobs and sub-agents**: anything you started (builds, test runs, reviewers, workers) — completed? died? output waiting unread?
- **Branches/worktrees**: does local state still match what you last pushed? Any commits from concurrent sessions?
- **External processes**: deploys, scheduled runs, anything a human might have touched in the meantime.

Only re-check what's relevant to this session — don't audit the world. Cheap read-only commands only (`gh pr checks`, `git log`, reading task output files). If something can't be checked quickly, report it as unverified rather than stalling the recap.

## Step 2 — Report exactly four sections

**1. The goal — in the words of whoever asked.**
Quote or closely paraphrase the original request(s) from the person, not your restatement of them. If the goal shifted mid-session (new instructions, scope changes), show the progression in their words.

**2. Where things actually stand — with evidence.**
Current state as verified in Step 1, not as remembered. Every claim carries its evidence: a PR number with its check status, a test count from an actual run, a commit hash, an agent's reported result. Distinguish clearly between "verified just now" and "as of when X reported it". If evidence contradicts what was previously believed, lead with that.

**3. What's blocked, split by kind.**
- **Blocked on a person**: decisions, approvals, merges, credentials, answers — name the person and the exact thing needed.
- **Blocked technically**: failing jobs, running processes not yet finished, missing infrastructure, rate limits — name the blocker and what unblocks it.
- If nothing is blocked, say so explicitly.

**4. Next steps — each tagged with an owner.**
A short ordered list. Every item starts with **[Claude]** or **[You]** (or a named third party). No untagged items, no vague "continue the work" entries — each step is a concrete action. Do not begin any [Claude] item until I've seen the recap and responded, unless it was already running before the recap started.

## Rules

- **No new work.** No fixes, no retries, no pushes, no spawning agents, no resuming paused work — even "quick" ones, even obvious ones. The recap ends with the report.
- Keep the whole report scannable — this is a briefing, not a log. Prose over fragments, but selective: what changed, what matters, what's next.
- The usual session status footer still applies as the last line.
