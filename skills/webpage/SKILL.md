---
name: webpage
description: Publish an unlisted web page on Simple Sites (simplesites.app/<name>-<code>) for a report, list, or prototype meant for one person or a small group — Markdown or HTML, no PR. Can update a page in place, take it down, and bring it back. Use when the user says "post a website", "make a page I can send to X", "share page", or wants a report at a private link.
---

# Unlisted pages on Simple Sites

Simple Sites is free. Pages are unlisted, not secret: anyone with the link can read them. Keep passwords, keys, and private message text off the page.

The account link lives in `~/.config/simplesites/link` (mode 600) on this machine, not in this skill. If it is missing, ask the user to put it there (the same link `deck` uses). `$SKILL` below is this skill's folder.

## Publish

1. **Get an HTML file.** If you already have a self-contained HTML page (inline CSS, system fonts), use it. If you have Markdown, convert it with `md2page.py` (markdown-to-page), a small script beside this skill that wraps the Markdown in a simple, printable HTML page with a title, typography, responsive tables, a `noindex` tag, and an "unlisted" footer:

   `python3 $SKILL/md2page.py REPORT.md /tmp/<slug>.html --subtitle "prepared for <recipient> · <date>"`

   For a short note, that conversion is enough. For a longer report, design the page: lead with the answer, use a few tiles or a plain-English box, put deep detail in `<details>`, and only then convert or write the HTML.

2. **Publish:** `python3 $SKILL/simplesite.py publish <file.html> <name> ["Title"]`. `<name>` is up to 10 characters of a-z, 0-9 and `-`. It prints the address and the page id. Report both.

## Update, take down, bring back

- `python3 $SKILL/simplesite.py update <id> <file>` — same address, new content. Do not publish a second copy of the same page unless the user wants a second link.
- `python3 $SKILL/simplesite.py remove <id>` takes it down (kept). `python3 $SKILL/simplesite.py restore <id>` brings it back at the same address.
- `python3 $SKILL/simplesite.py list` — every page and link with id, status, address, and title.

## Optional extras

- Numbered footnotes from `[label](url)` citations: `python3 $SKILL/footnotes.py in.html out.html` (puts the list at `<!--SOURCES-->`).
- A whole folder (for example a deck with media) uses the `deck` skill's `tools/sitesync.py`, not a single-file page.
