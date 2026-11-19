// Screenshot a deck slide at chosen moments and tile them into one contact sheet, so a timed or animated slide can be
// checked in one image. Usage:
//   node tools/timeline.mjs <url#slide> [--click] [--keys=ArrowRight,ArrowRight] [--out=sheet.png] t1 t2 ...
// Times are seconds after the page loads, or after the click/keys when given (--click presses ArrowRight once).
// Needs the playwright npm package and its Chromium browser (or --channel=chrome). Prints page errors and audio play() calls.
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); }
catch { console.error('Install playwright beside this tool: npm install --prefix <skill>/tools playwright'); process.exit(2); }
import { readFileSync } from 'node:fs';
import path from 'path';

const args = process.argv.slice(2);
const url = args.find(a => /^https?:/.test(a));
const opt = k => (args.find(a => a.startsWith(`--${k}=`)) || '').split('=').slice(1).join('=');
const keys = args.includes('--click') ? ['ArrowRight'] : (opt('keys') ? opt('keys').split(',') : []);
const out = path.resolve(opt('out') || 'timeline.png');
const times = args.filter(a => /^\d+(\.\d+)?$/.test(a)).map(Number).sort((a, b) => a - b);
if (!url || !times.length || !out.endsWith('.png')) { console.error('usage: timeline.mjs <url> [--click] [--keys=a,b] [--out=x.png] t1 t2 ...'); process.exit(2); }

const b = await chromium.launch({ ...(opt('channel') ? { channel: opt('channel') } : {}) });
try {
  const p = await b.newPage({ viewport: { width: 1600, height: 900 } });
  p.on('pageerror', e => console.log('PAGE ERROR', e.message));
  await p.addInitScript(() => { const pl = HTMLMediaElement.prototype.play; HTMLMediaElement.prototype.play = function () { console.log('AUDIO play ' + (this.currentSrc || this.src).split('/').pop().slice(0, 40)); return pl.call(this); }; });
  p.on('console', m => m.text().startsWith('AUDIO') && console.log(m.text()));
  await p.goto(url);
  if (keys.length) { await p.waitForTimeout(1200); for (const k of keys) { await p.keyboard.press(k); await p.waitForTimeout(150); } }
  const shots = []; let last = 0;
  for (const t of times) {
    await p.waitForTimeout(Math.max(0, (t - last) * 1000)); last = t;
    const f = out.replace(/\.png$/, `-${shots.length}-${t}.png`);
    await p.evaluate(t => { const d = document.createElement('div'); d.id = '__tl'; d.textContent = t + 's';
      d.style.cssText = 'position:fixed;left:12px;top:12px;z-index:2147483647;font:700 44px system-ui;color:#fff;background:rgba(0,0,0,.7);padding:4px 14px;border-radius:8px'; document.body.append(d); }, t);
    await p.screenshot({ path: f }); await p.evaluate(() => document.getElementById('__tl').remove()); shots.push(f);
  }
  // Tile in the browser: two frames per row, with no image-processing dependency.
  const cols = Math.min(2, shots.length), rows = Math.ceil(shots.length / cols);
  await p.setViewportSize({ width: cols * 640, height: rows * 360 });
  await p.setContent(`<html><body style="margin:0;background:black;display:grid;grid-template-columns:repeat(${cols},640px)">${shots.map(f => `<img style="display:block;width:640px;height:360px" src="data:image/png;base64,${readFileSync(f).toString('base64')}">`).join('')}</body></html>`);
  await p.evaluate(() => Promise.all([...document.images].map(img => img.decode())));
  await p.screenshot({ path: out });
  console.log(out);
} finally {
  await b.close();
}
