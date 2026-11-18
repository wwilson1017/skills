# Skills

Skills for Claude Code and other agents that read `SKILL.md` folders. Two skills: page-based interviews and browser slide decks.

## grill-me-page

A grill is the interview an agent runs before it builds anything: map the decisions, recommend an answer for each, settle them with you. `grill-me-page` runs a round of that grill as one web page you answer in a single sitting, on a laptop or a phone, instead of one question at a time in chat. Every question has a ★ recommendation and a plain-English why, pre-set options where they help and a box for your own words where they do not, a notes box, and a mockup or diagram when a picture explains it; press Go and the answers land back in the session by themselves, and the next round rebuilds the same page with your answers locked and only the questions they opened. The example in `skills/grill-me-page/example/` is a six-question grill about a break-room lunch board, with its round 2.

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

## Licence

MIT. See `LICENSE`.
