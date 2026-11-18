# Editing an existing deck

## Edit, look, publish, verify

1. Find the slide by its words, then confirm its current 1-based hash number. Numbers change as slides are inserted; press N to show them while reviewing.
2. Keep a backup outside the publish folder. For scripted replacements, assert that the old text exists and scope the edit to that slide's markup or CSS. Avoid global attribute replacements that can retime unrelated slides.
3. Edit the source. If a block is generated and spliced in, change its source and regenerate it. Prefix classes for new slide-specific components and check for collisions with existing CSS.
4. Serve the dedicated deck folder on loopback and inspect screenshots. Test direct loading, navigation from a different slide, Back, and a fresh browser. A hidden slide has no layout; animation geometry measured at initial load can be zero.
5. For motion, capture the moments that matter with `tools/timeline.mjs` and inspect the contact sheet, page errors and media play calls:

   ```bash
   node "$SK/tools/timeline.mjs" 'http://127.0.0.1:8765/#1' --click --out=timeline.png 1 4 12 30
   ```

   Times are seconds after page load or the supplied navigation keys. `--click` presses ArrowRight once; `--keys=ArrowRight,ArrowRight` sends a sequence. Frames are sampled in ascending time order; capture overhead makes these approximate, not frame-accurate measurements. Store screenshots outside the publish folder.

   This optional tool needs Node, the `playwright` npm package resolvable beside the script, and a Playwright Chromium browser. To prepare it: `npm install --prefix "$SK/tools" playwright`, then `"$SK/tools/node_modules/.bin/playwright" install chromium`. Use `--channel=chrome` to select an installed Chrome instead. The helper keeps normal autoplay restrictions so missing user gestures remain visible; also test audio manually.
6. For a requested publication, run `python3 "$SK/tools/sitesync.py" update <id> <deck-dir>`. Connect once with `sitesync.py connect` if needed; first publication uses `publish <deck-dir> <name>`. Follow the too-big procedure in [SKILL.md](SKILL.md) if SITE_SYNC refuses the size: shrink, explain the changes, retry once, then stop if still over.
7. Reload the public URL, confirm the changed content and fetch/play each changed media file. Re-check local/offline behavior if media paths changed. Update any session notes outside the published folder, then report what changed and what was checked.

## Motion recipes

- **Self-playing slide:** make scenes `.sc` layers with `--t` for start time and `--d` for duration. Derive CSS delays from `calc(var(--t) + Xs)`. One JS elapsed-time clock can drive canvas, counters and sound; keep JS timing tables next to the corresponding CSS numbers.
- **Click to start:** put an invisible `<i class="step x-go"></i>` in the slide and gate animations on `section.on:has(.x-go.shown)`. The slide is a holding screen until the next press.
- **Reversible stops:** add invisible steps with `data-t`. Mark them shown as the clock passes; manual Next/Back seeks to their times. Set `--seek`, subtract it from scene delays, then restart animations with a one-frame `animation:none` class and a reflow. Cancel clocks and audio when leaving a slide and reset them on re-entry.
- **Crawl into the distance:** hinge a plane at the bottom edge with `rotateX(40deg)` and `perspective:420px`. Set perspective-origin Y to P × cot(θ) relative to the plane's origin to place the vanishing point. Check the actual projection at several timestamps; a quiet background keeps the text readable.
- **Fly-ins:** animate from off-screen at scale 2.6 with rotation, hover beside text, then shrink toward the vanishing point at scale .02. Keep natural image aspect ratios, alternate sides, and measure the associated text's position only after the slide becomes visible.
- **Shatter:** generate a grid of clip-path triangles, each carrying the same background image at the correct offset. Animate per-piece `--x`, `--y`, `--z`, `--r` vectors. A Python script can produce deterministic pieces for repeatable checks.
- **Explode words:** wrap letters in spans and animate the same vectors; preserve an accessible text label on the containing element.
- **Other effects:** procedural canvas scenes, a starfield, count-ups, confetti from a fixed set of elements, or a sweeping line followed by two clipped halves falling apart. Choose effects that fit the requested tone. Offer a reduced-motion/static alternative for long or intense animation.

CSS traps: define an explicit `to` keyframe when the element's base style is hidden. Two animations setting `transform` on one element compete; put one on a child. Heavy text shadows muddy gradient text. Give background layers an explicit stacking order. Pause inactive scenes rather than leaving hidden timers running.

## Sound

Use `new Audio('media/cue.m4a')`, start it from a user gesture or an unlocked audio context, schedule cues from the slide clock, and fade with `volume`. Handle rejected `play()` promises. Pause/reset sounds on leaving, and verify that re-entering does not start duplicate playback. Browser autoplay policies still apply.

Trim leading silence with ffmpeg so the cue lands at the intended moment. For a generated chime, use Web Audio oscillators with short gain envelopes. An optional user-selected local audio file can be stored in IndexedDB; it is local to that browser and is not included in a published folder. Use only sound the person is entitled to publish.

## Media and facts

Use supplied or appropriately licensed media; keep attribution and public source URLs in notes when required. Inspect contact sheets before choosing footage. For example, generate a sheet from a local clip with `ffmpeg -i clip.mp4 -vf 'fps=1/4,scale=480:-1,tile=5x6' -frames:v 1 sheet.jpg`.

Prefer primary sources for factual claims. Label illustrative figures, and keep sensitive facts and private messages out of both slides and source notes. Large media should be files beside the deck so the sync helper can reuse unchanged content and the shrink helper can process it.
