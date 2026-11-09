#!/usr/bin/env node
// HTML-seek renderer. <dir>/index.html must define window.seek(frame) and set window.READY=true when images/fonts are ready.
// Optional page globals: window.TOTAL_FRAMES (default range end), window.HR_FONTS (CSS font shorthands to preload + verify, e.g. '900 40px "Playfair Display"').
//   node bin/hr_render.cjs <dir> [--from 0] [--to N] [--step 1] [--workers 1] [--out frames] [--fmt jpeg|png] [--lint]
// Why this exists: four hand-copied render loops, a blank first frame from unloaded fonts, and text that ran off the edge were all found by eye.
//   - one Edge per worker, frames interleaved. DEFAULT 1: measured on this Mac (heavy pages: images + blur + canvas) 40 frames took 10s with 1 worker and 313s with 3.
//     A full 435-frame reel is ~110s on one worker. Only raise --workers after timing a 40-frame range both ways.
//   - every font in HR_FONTS is loaded AND checked before frame 0 (a missing face warns instead of silently falling back)
//   - --lint prints the caption script (what text is on screen when) and flags text that stays outside the 1080px frame
const { launch } = require('../../engine/browser.cjs');
const fs = require('fs'), path = require('path');

const argv = process.argv.slice(2);
const flag = (k, d) => { const i = argv.indexOf(k); return i < 0 ? d : (argv.splice(i, 2)[1]); };
const lint = (() => { const i = argv.indexOf('--lint'); if (i < 0) return false; argv.splice(i, 1); return true; })();
const dir = path.resolve(argv[0] || '.');
const from = +flag('--from', 0), step = +flag('--step', 1), workers = Math.max(1, +flag('--workers', 1));
const out = flag('--out', 'frames'), fmt = flag('--fmt', 'jpeg');
let to = flag('--to', null);
const ext = fmt === 'png' ? 'png' : 'jpg';
const W = 1080, H = 1920;

(async () => {
  fs.mkdirSync(path.join(dir, out), { recursive: true });
  const probe = await launch();
  const pg0 = await probe.newPage({ viewport: { width: W, height: H } });
  await pg0.goto('file://' + path.join(dir, 'index.html'));
  await pg0.waitForFunction(() => window.READY, null, { timeout: 90000 });
  const total = await pg0.evaluate(() => window.TOTAL_FRAMES || 0);
  await probe.close();
  if (to === null) to = total ? total - 1 : (() => { throw new Error('pass --to or define window.TOTAL_FRAMES'); })();
  to = +to;
  const frames = []; for (let f = from; f <= to; f += step) frames.push(f);
  const t0 = Date.now();
  const lintRows = []; // {f, id, text, l, r}
  const warns = new Set();

  async function work(w) {
    const mine = frames.filter((_, i) => i % workers === w); if (!mine.length) return;
    const br = await launch();
    const pg = await br.newPage({ viewport: { width: W, height: H } });
    pg.on('pageerror', e => warns.add('pageerror: ' + e.message));
    await pg.goto('file://' + path.join(dir, 'index.html'));
    await pg.waitForFunction(() => window.READY, null, { timeout: 90000 });
    const bad = await pg.evaluate(async () => {
      const list = window.HR_FONTS || [];
      await Promise.all(list.map(x => document.fonts.load(x, 'abcAB0 काफ़िला').catch(() => 0)));
      await document.fonts.ready;
      return list.filter(x => !document.fonts.check(x, 'abcAB0'));
    });
    bad.forEach(x => warns.add('FONT NOT LOADED (silent fallback): ' + x));
    await pg.waitForTimeout(300);
    const cdp = await pg.context().newCDPSession(pg);
    for (const f of mine) {
      await pg.evaluate(f => window.seek(f), f);
      if (lint) {
        const rows = await pg.evaluate(() => [...document.querySelectorAll('.tx,[data-lint]')]
          .filter(e => +getComputedStyle(e).opacity > 0.6 && !e.hasAttribute('data-lint-skip'))
          .map(e => { const rg = document.createRange(); rg.selectNodeContents(e); const b = rg.getBoundingClientRect();
            return { id: e.id || e.className, text: e.textContent.trim().replace(/\s+/g, ' '), l: Math.round(b.left), r: Math.round(b.right) }; }));
        rows.forEach(r => lintRows.push({ f, ...r }));
      }
      const shot = await cdp.send('Page.captureScreenshot', fmt === 'png' ? { format: 'png' } : { format: 'jpeg', quality: 92 });
      fs.writeFileSync(path.join(dir, out, String(f).padStart(4, '0') + '.' + ext), Buffer.from(shot.data, 'base64'));
    }
    await br.close();
  }
  await Promise.all(Array.from({ length: workers }, (_, w) => work(w)));
  console.log(`rendered ${frames.length} frames (${from}..${to}, step ${step}) with ${workers} workers in ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${path.join(dir, out)}`);
  warns.forEach(x => console.log('WARN', x));

  if (lint) {
    // caption script: runs of the same on-screen text per element
    lintRows.sort((a, b) => a.f - b.f);
    const runs = {}, script = [];
    for (const r of lintRows) { const k = r.id + '|' + r.text; const cur = runs[k];
      if (cur && r.f - cur.to <= step * 2) cur.to = r.f; else { if (cur) script.push(cur); runs[k] = { id: r.id, text: r.text, from: r.f, to: r.f, minL: r.l, maxR: r.r }; }
      runs[k].minL = Math.min(runs[k].minL, r.l); runs[k].maxR = Math.max(runs[k].maxR, r.r); }
    Object.values(runs).forEach(r => { if (!script.includes(r)) script.push(r); });
    script.sort((a, b) => a.from - b.from);
    console.log('\nCAPTION SCRIPT (read it: does every line describe the picture, in order, as a sentence?)');
    script.forEach(r => console.log(`  f${r.from}-${r.to}  #${r.id}  "${r.text}"`));
    // overflow = still outside the 1080px frame when the text has SETTLED (its last 3 sampled frames). Slam-ins and zoom-throughs
    // overshoot on purpose; exempt an element that must leave the frame with data-lint-skip.
    const byKey = {};
    lintRows.forEach(r => { (byKey[r.id + '|' + r.text] = byKey[r.id + '|' + r.text] || []).push(r); });
    const sustained = Object.entries(byKey).filter(([, rows]) => { const last = rows.slice(-3);
      return rows.length >= 3 && last.every(r => r.l < -6 || r.r > W + 6); }).map(([k, rows]) => [k, rows.map(r => r.f)]);
    if (sustained.length) { console.log('\nOVERFLOW (text still outside the 1080px frame when it settles):');
      sustained.forEach(([k, fs_]) => console.log(`  ${k.replace('|', '  "')}"  frames ${fs_[0]}..${fs_[fs_.length - 1]}`)); }
    else console.log('\nno settled text overflow');
    fs.writeFileSync(path.join(dir, 'lint.json'), JSON.stringify({ script, overflow: sustained.map(([k, v]) => ({ k, frames: v })) }, null, 1));
  }
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
