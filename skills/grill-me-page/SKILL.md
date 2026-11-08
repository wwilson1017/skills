---
name: grill-me-page
description: "Run a grill (an interview that stress-tests a plan or design) as one web page the person answers in a single sitting, instead of one question at a time in chat. Each question gets a recommended answer marked ★, a plain-English why, optional pre-set options, a box for an answer in the person's own words, a notes box, and a mockup or diagram where a picture explains it. A page holds one round: the decisions that can be settled now. Answers come back to the session by themselves when a collector runs beside the page, or as text to paste when it does not. Use when someone says 'grill me on a page', 'make it a page I can answer', 'question page', 'send these questions to X', or when a grill would run more than a handful of questions."
disable-model-invocation: true
---

# /grill-me-page

A grill is the interview you run before building something: map the decisions, recommend an answer for each, and settle them with the person. It comes from Matt Pocock's `grill-me` skill (github.com/mattpocock/skills), which asks in chat, one round at a time. That works for five questions. At thirty, the person scrolls, loses the thread, cannot see how the decisions depend on each other, and cannot answer anywhere but at the keyboard.

This skill puts a round on one page. The person reads it top to bottom, keeps your recommendation wherever they agree, picks another option or writes their own answer where they do not, adds notes, asks their own questions, and presses Go. The answers come back here. Then you run the next round on the same page.

**The page replaces the one-question-at-a-time chat, not the thinking.**

## 1. Do the grill yourself first

- Map the **design tree** the way `grill-me` does: every decision branches into the decisions that hang off it.
- **Find facts by looking, never by asking.** Read the code, query the data read-only, check the issues and docs. Only real decisions go on the page.
- **A page is one round: the frontier.** The frontier is every decision whose prerequisites are already settled. A question whose answer depends on another question still open on this page belongs to the next round, not this one. List those deferred topics in `NEXT` as topics, not as questions with options, and the page shows them as "Waiting on your answers".
- **The stop rule.** When an answer would open more than a handful of new decisions, or you reach anything you cannot settle by reading code or data, stop. Build the round with what you have, hand it over and wait. Never fill a gap with a guess to keep going, and never try to put the whole tree on one page. If the goal is too unclear to form a frontier at all, ask in chat first.
- **Every question gets a recommendation (★) and a "why" of 1 to 3 plain sentences** with the real numbers behind it. Word the question so taking ★ means "yes". Options are 2 to 4 mutually exclusive choices, each a short label plus an optional one-line consequence. Options are a shortcut, not a fence: every card also has a box for an answer in the person's own words.
- Group the questions into lettered sections (A, B, ...) in dependency order. Open each section with a one-line takeaway.
- **Draw where a picture explains.** A screen mockup for UI questions, a flow for processes, side-by-side cards for "option A vs B", a timeline for sequencing, a table for codes or mappings. If you use made-up amounts in a mockup, say so in its caption.
- Lead the page with an "In plain English" box, a few stat tiles of real numbers, and a collapsible "already decided, not asked" list.

## 2. Write the parts

Make a working folder for this grill (e.g. `grills/<slug>/`). `example/` beside this file is a complete, small grill to copy from, and `example/round2/` is its second round.

**`config.js`**
```js
const PAGE = 'billing-grill', VERSION = 1;     // PAGE is stable across rounds; bump VERSION each round
// const MULTI = true;                          // several people answer: adds a required name field
// const ACKS = false;                          // hosted page whose owner cannot write ack files beside it
const NEXT = ['Refund flow (after B1, B2)', 'Export format (after C1)'];   // deferred to the next round
const SECTIONS = [ {k:'A', t:'Where it lives', take:'One-line takeaway.'} ];
const Q = [
 {id:'A1', s:'A', t:'Where does billing live?', why:'Plain-English context with the numbers.', vis:'vis-tile', o:[
   ['tile', 'Its own app tile', 'What that means in one line.', 1],   // 1 = ★ recommended
   ['tab',  'A tab inside Orders', '']]},
 {id:'G5', s:'G', t:'Reports in v1', multi:true, why:'Tick every one you want.', o:[ ['aging','Aging summary','',1], ['trend','Monthly trend',''] ]},
 {id:'J1', s:'J', t:'Pull anything into v1?', multi:true, none_rec:true, why:'Blank means they stay out.', o:[ ['pay_links','Pay-now links',''] ]},
];
```
Write `why`, labels and descriptions as plain JS strings and escape apostrophes (`don\'t`). The engine HTML-escapes them. `multi:true` makes checkboxes. `none_rec:true` means a blank answer is "none", not "take ★".

**`body.html`**: the intro (a `.pill` with the version and date, `<h1>`, `.sub`, `.lead` box, `.tiles`, `details.decided`, any diagrams). In round 2 and later, put `<!--LOCKED-->` where the previous answers table goes, then a section answering the person's notes and questions (one `.q` card each, no inputs).

**`visuals.html`** (optional): `<template id="vis-...">...</template>` blocks, used by `vis:` on a question or by `<div data-vis="vis-..."></div>` anywhere in body.html or after.html. **`after.html`** (optional): content after the questions, such as the build plan.

**CSS kit** (in `template.html`, light and dark already):
- Mockups: `.screen > .screen-bar (.dot x3) + .screen-body`, `.mock-h`, `.mock-tabs span.on`, `.kpis .kpi .n/.l`, `.queue .qrow (.grow, .act)`, `table.mt`, `.form .fld`, `.apptile`.
- Flows: `.flow > .node(.built|.new|.ext|.warn)` with `.arrow` between; they stack vertically on phones. `.ext` is an outside system.
- Comparisons and layout: `.cols2 .colcard`, `.grid3 .phase`, `.timeline .tl-track .tl-seg` with `.tl-marks`, `.how` (a row of small step boxes).
- Labels and captions: `.pill(.new|.built|.warn|.info)`, `.vis-cap`, `.small`, `.muted`.

Keep wide mockups inside `.screen-body` or a `<div style="overflow-x:auto">` so the page never scrolls sideways on a 390 px phone.

## 3. Build, check and hand it over

```bash
SK=<this skill's folder>
python3 $SK/build.py <dir> --title "Billing Grill · v1"              # -> <dir>/index.html, one self-contained file
python3 $SK/build.py <dir> --title "Billing Grill · v2" --locked <dir>/answers-v1.json   # round 2+
```

If you can drive a browser (Playwright or similar), check before handing it over: 1280 px and 390 px wide, light and dark; screenshot the top and every card with a visual; confirm `#sections .q[data-id]` count equals `Q.length` and `document.documentElement.scrollWidth - innerWidth == 0`; click "Take ★", then Go, and confirm the box fills.

**How the answers get back.** The page decides this itself when it loads, by probing for a collector at `submit.php` beside it (3 s timeout). The page tells the person which mode it is in.

| Transport | When | How answers return |
|---|---|---|
| Local collector | You run `collect.py serve` and open the served URL | By themselves: `collect.py watch` wakes you with the record |
| Hosted PHP adapter | The page sits on a PHP host with `hosted/submit.php` beside it | `collect.py watch <URL>` polls the host; see `hosted/HOSTED.md` |
| Copy box | Opened from disk, a static host, or the collector is down | Go fills a box with a summary and an `ANSWERS JSON (for the next round):` line; the person pastes it here |

Drafts are kept in that browser's local storage in every mode, per page and version, so closing the tab loses nothing.

**Default: the local collector.** Start it in the background, open the page, then watch for Go in the background too:

```bash
python3 $SK/collect.py serve <dir> --port 8765                       # background; serves only index.html and submit.php, loopback only
open http://localhost:8765/                                           # xdg-open on Linux, start on Windows
python3 $SK/collect.py watch <dir> <PAGE> <VERSION> <dir>/answers-v<VERSION>.json   # background; exits when Go lands
```

In Claude Code run `serve` and `watch` as Bash calls with `run_in_background: true`; `watch` exits when the record arrives and that re-invokes the session. In a harness without that, re-run `watch` when you come back (`--hours` sets how long it waits, default 48). `watch` is idempotent: if the Go is already in `answers.jsonl` it writes the file and exits at once, so a session that died loses nothing. While it runs it writes a heartbeat, and the page shows "a session is watching this page". When it finds the Go it writes `ack-received.json`, and the page turns green: "The session has your answers". For a phone on the same network or tailnet add `--bind 0.0.0.0`; the collector prints a warning because anyone on that network can then read and answer the page.

Tell the person: answer it, press Go, and you will pick it up. Then stop and wait.

**From disk or a static host.** Open `<dir>/index.html` directly, or put it anywhere static files are served. Go gives a box to copy; the person pastes it back here. Only share a page with the person's say-so, and remember that anyone with the link can read the questions.

## 4. Read the answers, run the next round

The record is `<dir>/answers-v<N>.json` (the collector's `{at, data}` envelope) or the pasted text. `build.py --locked` reads either, and also a bare record. Each answer is `{picked:[values], answer, note}`, plus `my_questions`, `missing`, `summary_text` and `questions`.

**Read `picked` and `answer` together.** The ★ rule, applied the same way by the page's summary, by the locked table and by you:
- Both empty, and not `none_rec`: they took ★.
- `picked` only: that option.
- `answer` only: their own words. This is not ★, even if the text sounds like it. The locked table marks it "own answer".
- Both: the option plus their elaboration. A plain correction in the text ("not 9:30, make it 10:00") supersedes the pick; a contradiction you cannot resolve becomes a follow-up question.
- `none_rec` and both empty: none.

Then:
1. Check every "double-check that" or "are you sure" in the notes against the code or data before you write round 2.
2. Recompute the frontier. Round 2 has the locked table (`--locked`), your answers to their notes and questions (draw where it helps), and only the questions their answers unblocked. Anything still blocked stays in `NEXT`. Bump `VERSION` and rebuild into the same file, so the person just reloads. The collector serves the file from disk, so `serve` keeps running across rounds.
3. Tell the page you have acted on it, so the person sees "All applied":
   ```bash
   python3 $SK/collect.py ack <dir> <PAGE> <VERSION> applied "Round 2 is up: reload the page" --record <dir>/answers-v<VERSION>.json
   ```
   `--record` is the file `watch` wrote; the ack carries that record's `submit_id`, so a later Send again never lights up on an old ack.
4. Start `watch` again for the new version, and wait.
5. When no questions are left, the grill is done. Write the decisions down (a short brief or the plan) before anyone builds.

## Several people answering

Set `const MULTI = true`. A name is required before Go, each person's answers are kept under it, and typing a name on a new device restores that person's earlier answers. The page shows "Sent" after Go and does not poll for acks. `watch` exits at the first Go; after that read `<dir>/answers.jsonl` yourself (one `{at, data}` line per save; the newest line with `final: true` per `name` is that person's answer). Give every person the same `VERSION` so their answers line up.

## Rules

- **The collector is a transport, not a database.** It keeps one file, `answers.jsonl`, in the grill folder, and serves only the page and its API. Do not point it at a folder with anything else in it you would mind serving by mistake (it serves only `index.html`, but keep the habit).
- **Hosted means readable.** Once the page is on the web, anyone with the link can read it. Keep passwords, keys, account numbers and private messages off it.
- `body.html`, `after.html` and `visuals.html` are raw HTML you write. Do not paste text from untrusted sources into them unescaped. The engine and `build.py` escape everything that comes from `config.js` and from answers.
- Drafts live in the browser's local storage per page and version; clearing site data loses an unsent draft.
