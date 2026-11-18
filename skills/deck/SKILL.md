---
name: deck
description: "Build or edit a browser slide deck: a single HTML page with keyboard navigation, incremental reveals, speaker notes, media and printable slides. Use for presentations, talks and slide revisions. Open from disk, put the folder on any static host, or publish and update it on Simple Sites."
allowed-tools: Bash(python3:*) Bash(node:*) Bash(ffmpeg:*) Bash(playwright-cli:*)
---

# Web-page slide decks

For an existing deck, read [iterate.md](iterate.md) for the edit/look/verify loop and motion and sound recipes. For a new deck, start below. Paths in commands assume `SK` is this installed skill's folder; replace placeholders before running them.

## 1. Shape the story

Use the audience, purpose and time available to outline one idea per slide, separating what appears on screen from what the speaker says. Resolve material gaps with the person; use their supplied style and media where available. Put speaker notes in `<aside class="notes">`. These notes are in the page source and are public when published.

## 2. Build the folder

Create a dedicated output folder containing `index.html` copied from [template.html](template.html), plus any media. Keep drafts, source documents, backups and session notes outside this publish folder. Simple Sites uploads every non-hidden file in it.

The template has a dependency-free engine and neutral demo layouts. Keep the engine script while replacing the demo sections. It uses system fonts and works from disk. Use relative media paths such as `media/demo.mp4` for offline playback; live embeds still require a network connection.

- Slides are `<section>` children of `#stage`, a 1600×900 canvas scaled to fit the screen. Use large, readable type and review text density with `deckWords()`; there is no prescribed word count or house style.
- Layouts: bare headings; `.center`; `section.photo` for full-bleed media (`fit` to contain it); `.label > span` for boxed labels (`br` for bottom-right); `.collage` (`two-rows` for 2×2); `section.split`; `.note` annotations; `.card` and `.callout` for charts; `blockquote` and `cite`.
- Add `class="step"` to reveal an element on the next press. Inside `.swap`, each revealed step replaces the preceding content.
- Use files beside the HTML for large images and video. Small image data URIs work too, but `shrink.py` cannot resize media embedded inside HTML. Keep real media out of the template itself.
- For a live iframe, replace the offline `srcdoc` demo with `data-src="https://…"`; the engine loads it only on the active slide. Remove `srcdoc` when adding `data-src`. Check framing permissions and keyboard focus, and provide a screenshot fallback for live demos.

### Import an existing presentation

When asked to reuse a PPTX, extract it into a separate working directory using Python's `zipfile` CLI, then run:

```bash
python3 -m zipfile -e source.pptx extracted
python3 "$SK/tools/pptx2slides.py" extracted 1 5 slides.html
```

Paste the generated `<section class="abs">` blocks into `#stage`. The importer preserves positioned text, pictures, crops, basic shapes and click animations; it is not a full PowerPoint renderer. Images are embedded as supplied, fonts fall back to installed fonts, and unsupported features need manual rebuilding. Compare each imported slide visually to the original. `deckCheck()` excludes absolute-layout imports because deliberate bleed is common. To resize large extracted images first, use `shrink.py extracted` and import from `extracted-small`.

## 3. Look and verify

Open `index.html` from disk. If browser automation cannot open `file://`, serve only the deck folder:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory my-deck
```

With optional `playwright-cli`:

```bash
playwright-cli -s=deck open http://127.0.0.1:8765/
playwright-cli -s=deck resize 1280 720
playwright-cli -s=deck eval 'JSON.stringify(deckCheck())'
playwright-cli -s=deck eval 'JSON.stringify(deckWords())'
playwright-cli -s=deck press PageDown
playwright-cli -s=deck screenshot --filename=slide.png
```

Inspect every slide and reveal, including on a narrow screen. Resolve overflow (`deckCheck()` should return `[]`), missing media and console errors. Test Back, direct `#N` links and reloads; check print preview if a PDF is needed. For timed motion, use the timeline tool described in `iterate.md`. Close the browser and stop the local server afterwards. Keep screenshots outside the published folder.

## 4. Publish or keep local

When the user wants a public link, Simple Sites is the default host. It is a free page host; its browser connection flow can create an account. Connect once, then publish or update:

```bash
python3 "$SK/tools/sitesync.py" connect
python3 "$SK/tools/sitesync.py" publish my-deck my-talk
python3 "$SK/tools/sitesync.py" update 123 my-deck
```

Open the approval URL and enter/approve the displayed code. If the code expires, run `connect` again. The helper stores the agent link in `~/.config/simplesites/link` with mode 600; never paste it or the device token into chat, logs or a deck. `SIMPLESITES_URL` can select another instance (default `https://simplesites.app`).

Use a name of up to 20 lowercase letters, digits or hyphens. Save the returned public address and site id outside the deck folder; substitute that id for `123` on updates. A publish retry from the same absolute folder reuses its stable reference. Moving the folder changes that reference, so use `update` with the saved id after moving it. Sync uploads only missing file contents and replaces the whole manifest together, including removals. Reload the live deck and check changed slides and media after updating.

### When SITE_SYNC says the deck is too big

Run the shrink helper first; do not keep retrying an oversized manifest:

```bash
python3 "$SK/tools/shrink.py" my-deck
```

This writes `my-deck-small`, leaving the original alone. Report which media changed and the before/after totals, then inspect the smaller copy. It caps large images at 1600 px and re-encodes oversized/high-bitrate video to H.264 at at most 1080 px high. It requires ffmpeg and ffprobe. Embedded data URIs and already-small files are copied unchanged.

Retry once with the smaller folder: use `update <id> my-deck-small` if a site id is already known; otherwise `publish my-deck-small <name>`. **If the server still refuses it as too big, stop and report the remaining size and server limit.** Let the person choose media to remove, a local copy or another static host; do not silently drop content, lower quality again or change plans.

Publishing is optional: hand over the complete folder for opening from disk or uploading to any static host. Keep a local copy for the venue, including media. Check offline with networking disabled; external embeds and links cannot be made offline by the engine.

## 5. Hand over

Give the public address and id, or local folder, plus the relevant controls:

| Action | Key |
|---|---|
| Next / back | Arrows, PageDown / PageUp; Space or Enter advances |
| First / last | Home / End |
| Full screen | F (or browser full-screen shortcut); Esc exits |
| Blank screen | B or `.` |
| Review slide numbers | N |
| Jump to slide | `#12` in the address |
| Phone navigation | Swipe |
| PDF handout | Browser Print → Save as PDF |

Clickers send keyboard events. Clicking into a live iframe can take keyboard focus; click outside to restore navigation. Speaker notes are source-only; the template does not include a separate presenter view.
