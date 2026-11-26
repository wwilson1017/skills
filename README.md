# Skills

Skills for Claude Code and other agents that read `SKILL.md` folders. Eight skills: page-based interviews, browser slide decks, recaps, handoffs, competing plans, two-stage code review, unlisted share pages, and small-business site redos.

## grill-me-page

A grill is the interview an agent runs before it builds anything: map the decisions, recommend an answer for each, settle them with you. `grill-me-page` runs a round of that grill as one web page you answer in a single sitting, on a laptop or a phone, instead of one question at a time in chat. Every question has a ★ recommendation and a plain-English why, pre-set options where they help and a box for your own words where they do not, a notes box, and a mockup or diagram when a picture explains it; press Go and the answers land back in the session by themselves, and the next round rebuilds the same page with your answers locked and only the questions they opened. A round can also settle the project's words and flag the few decisions worth an ADR: the session writes the words you accept to `GLOSSARY.md` as soon as you press Go. The example in `skills/grill-me-page/example/` is a short grill about a break-room lunch board (two words and six questions), with its round 2.

### Install

With the `skills` CLI (any agent that reads `SKILL.md` folders):

```
npx skills@latest add wwilson1017/skills
```

As a Claude Code plugin:

```
/plugin marketplace add wwilson1017/skills
/plugin install grill-me-page@wwilson1017-skills
```

Or copy `skills/grill-me-page/` into your agent's skills folder. Then type `/grill-me-page` in a session. The skill needs Python 3 and nothing else; the collector is standard library only.

### How it differs from grill-me

Matt Pocock's `grill-me` (github.com/mattpocock/skills) is where this comes from, and his `grilling` skill defines the method: work the design tree in rounds, ask the whole frontier at once with a recommended answer, wait. `grill-me-page` keeps that method and changes the medium. A round becomes a page, so thirty questions stay readable and you can answer from a phone or hand the page to someone else. Pictures go next to the questions they explain. The answers come back to the session on their own through a small local collector, or as text to paste when there is none.

Matt's repo does not take skills from outside, and he closed a proposal for a page-based grill as not planned (grilling stays plain-text rounds you answer in your own words), so this is published separately. He also objected to pre-baked multiple choice, which is why every card has a box for an answer in your own words beside the options, and why a page holds one round rather than a guess at the whole tree.

### Hosting the page for someone else

`skills/grill-me-page/hosted/` has a PHP adapter with the same API as the local collector, for putting a page on a shared host where a staff member or a client answers it. `HOSTED.md` there explains it.

## deck

Build a presentation as one HTML page with keyboard/clicker navigation, incremental reveals, notes, media and printable slides. Start from the neutral system-font template, edit an existing deck, or import slides from a PPTX. Open the folder from disk, use any static host, or publish to [Simple Sites](https://simplesites.app).

### Install

With the `skills` CLI:

```bash
npx skills@latest add wwilson1017/skills
```

As a Claude Code plugin:

```text
/plugin marketplace add wwilson1017/skills
/plugin install deck@wwilson1017-skills
```

Then ask for `/deck`. The skill and its tools live in `skills/deck/` in this repo; use the corresponding installed folder if installed through a plugin.

### Publish to Simple Sites

Put `index.html` and its media in `my-deck/`. Connect once, publish, then update using the returned id (replace `123`):

```bash
python3 skills/deck/tools/sitesync.py connect
python3 skills/deck/tools/sitesync.py publish my-deck my-talk
python3 skills/deck/tools/sitesync.py update 123 my-deck
```

The connection command prints a browser approval URL and code; the browser can create a free account. Credentials stay in `~/.config/simplesites/link` with mode 600. Publishing prints the public address and id. Only missing file contents are uploaded, and retries from the same folder reuse the same site.

If SITE_SYNC refuses the size, run `python3 skills/deck/tools/shrink.py my-deck`, review its before/after report and the smaller copy, and retry once with `my-deck-small` (use the existing id for updates). Stop if it is still over the server limit. Keep backups and private notes outside the upload folder; slide notes in HTML are public too.

### Requirements

Python 3.9+ for the helpers; no Python packages are needed. ffmpeg (including ffprobe) is needed only for the shrink helper. Node is needed only for the timeline tool, which also needs the Playwright npm package and its Chromium browser (setup in `skills/deck/iterate.md`). `playwright-cli` is optional for visual checks. The deck itself needs only a browser; local media works offline, while external embeds need a connection.

## recap

Refresh stale state (PRs, CI, background jobs), then report exactly four things: the goal in the requester's words, where things actually stand with evidence, what is blocked (on a person vs technically), and next steps tagged with an owner. The recap is read-only: it starts no new work.

### Install

```
npx skills@latest add wwilson1017/skills
```

```text
/plugin marketplace add wwilson1017/skills
/plugin install recap@wwilson1017-skills
```

Then ask for a recap, or type `/recap`.

## handoff

Write a handoff document that lets a fresh agent continue the work, saved to the OS temporary directory rather than the workspace. The skill returns the file path plus a starter paragraph to paste into the next session. Secrets are redacted; existing artifacts are referenced, not copied.

### Install

```
npx skills@latest add wwilson1017/skills
```

```text
/plugin marketplace add wwilson1017/skills
/plugin install handoff@wwilson1017-skills
```

Then type `/handoff`, optionally with what the next session should focus on.

## plan-fresh-eyes

Spawn an independent agent that sees the session's research, constraints, and decisions — but not the existing plan — and writes a competing plan. Ask which model to use first. The two plans are then compared so you can combine them.

### Install

```
npx skills@latest add wwilson1017/skills
```

```text
/plugin marketplace add wwilson1017/skills
/plugin install plan-fresh-eyes@wwilson1017-skills
```

Then type `/plan-fresh-eyes`.

## webpage

Publish an unlisted Markdown or HTML page on [Simple Sites](https://simplesites.app), which is free, and update, take down, or restore it later. Pages are unlisted, not secret. Markdown is converted with `md2page.py` (markdown-to-page), a small script in the skill folder that wraps the file in a simple, printable HTML page; `simplesite.py` is what puts that HTML on the web. The account link stays in `~/.config/simplesites/link` (mode 600), the same file the `deck` skill uses.

### Install

```
npx skills@latest add wwilson1017/skills
```

```text
/plugin marketplace add wwilson1017/skills
/plugin install webpage@wwilson1017-skills
```

Then ask for `/webpage`. Python 3 is required; `md2page.py` creates a private venv beside itself on first run to install the `markdown` package.

## site-redo

Take a small business from their current website to a clickable beta: an intake form the client fills in on their own time, a brief, several homepage options, then a build, review, and published beta. Client details stay in a local folder that is not a git repo. Hosting (Simple Sites, or a grill-me-page collector) is configured locally, not hard-coded to one domain.

### Install

```
npx skills@latest add wwilson1017/skills
```

```text
/plugin marketplace add wwilson1017/skills
/plugin install site-redo@wwilson1017-skills
```

Then type `/site-redo <client>`.


## review-super

A code review that fixes what it finds. Stage 1 is one fresh reviewer that knows nothing about how the change was built. Stage 2 is a second reader from another vendor (the Codex CLI), reading the whole repository, because two models from one family tend to miss the same things. Every finding has to quote the line that makes it true, and a quick `sed` check drops any that don't. Every finding that survives goes to a fix agent, which fixes it or refutes it with a reason. The skill never pushes, opens a PR or merges.

**Install a second-vendor reviewer.** Stage 2 does most of the catching. Over about 400 PRs in one team's November 2026 runs, the second-vendor stage raised a P0/P1 on 26% of diffs, against 9% for the same-vendor first stage. Without the Codex CLI, review-super runs Stage 1 only and says so.

Other numbers from the same runs:
- Fewer than 10% of findings went unacted on.
- An extra always-on checklist ("check sibling code paths") caught none of its target bugs in replay and added noise, so it was cut.
- The two checks that stayed run only when they apply: an authority check when auth, permissions or agent tools change, and a deploy-overlap check when a migration changes.

### Install

```
npx skills@latest add wwilson1017/skills
```

```text
/plugin marketplace add wwilson1017/skills
/plugin install review-super@wwilson1017-skills
```

For Stage 2: `npm i -g @openai/codex`, then sign in. Then type `/review-super` on a branch (`report-only` for findings without fixes, `full` to force Stage 2).

## Licence

MIT. See `LICENSE`.
