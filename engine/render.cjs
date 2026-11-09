// Renders a project's scenes to PNG frames with a pool of pages in one headless Edge.
//   node render.cjs <work> [scene,scene] [--stills] [--workers 6]
// <work> holds jobs.json (from build.py jobs), scenes.js and assets.js; base.html is the shared vocabulary.
// --stills writes one QC frame per scene (at 85% of its length) to <work>/qc/ for the contact sheet.
const { launch } = require('./browser.cjs');
const fs = require('fs');
const path = require('path');

const FPS = 30;
const argv = process.argv.slice(2);
const flag = (k, d) => { const i = argv.indexOf(k); return i < 0 ? d : argv.splice(i, 2)[1]; };
const workers = +flag('--workers', 6);
const stills = argv.includes('--stills');
const [work, names] = argv.filter(a => a !== '--stills');
const W = path.resolve(work);
const only = names ? names.split(',') : null;
const jobs = JSON.parse(fs.readFileSync(path.join(W, 'jobs.json'), 'utf8')).filter(j => !only || only.includes(j.name));
// Long scenes first so the pool finishes together.
jobs.sort((a, b) => b.cues.end - a.cues.end);

// Web fonts load only on first use: request every face up front or the first scene renders blank text.
const FACES = ['900 40px "Playfair Display"', '400 40px "PT Serif"', '700 40px "PT Serif"', '40px "Special Elite"',
  '700 40px Montserrat', '400 40px Inter', '500 40px Inter', '600 40px Inter', '700 40px Inter', '700 40px Caveat',
  '500 40px "Noto Sans Devanagari"', '600 40px "Noto Sans Devanagari"'];

async function openPage() {
  // One Edge per worker: pages inside one browser share its compositor and render no faster than one.
  const browser = await launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.error('pageerror', e.message));
  await page.goto('file://' + path.join(__dirname, 'base.html'));
  await page.addScriptTag({ path: path.join(__dirname, '..', 'effects', 'fx.js') });   // shared effect library
  for (const f of ['assets.js', 'scenes.js']) if (fs.existsSync(path.join(W, f))) await page.addScriptTag({ path: path.join(W, f) });
  // CDP session must open after goto: a file:// navigation swaps renderer and detaches an earlier one.
  const cdp = await page.context().newCDPSession(page);
  await page.evaluate(f => Promise.all(f.map(x => document.fonts.load(x, 'abcअ₹'))), FACES);
  // Transparent page once, then raw CDP captures: ~10x faster than omitBackground per frame.
  await cdp.send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
  const shot = async file => fs.writeFileSync(file, Buffer.from((await cdp.send('Page.captureScreenshot', { format: 'png' })).data, 'base64'));
  return { page, shot };
}

async function renderJob({ page, shot }, job) {
  // setup/seek return nothing on purpose: returning a GSAP timeline makes evaluate() serialise it and hang.
  await page.evaluate(([n, c, p]) => window.setup(n, c, p), [job.name, job.cues, job.props || {}]);
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => Promise.all([...document.images].map(i => i.complete || new Promise(r => (i.onload = i.onerror = r)))));
  if (stills) {
    await page.evaluate(t => window.seek(t), job.cues.end * 0.85);
    return shot(path.join(W, 'qc', job.name + '.png'));
  }
  const dir = path.join(W, 'frames', job.name);
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(W, 'frames', job.name + '.sfx.json'), JSON.stringify(await page.evaluate(() => window.sfx())));
  const n = Math.ceil(job.cues.end * FPS);
  for (let f = 0; f < n; f++) {
    await page.evaluate(t => window.seek(t), f / FPS);
    await shot(path.join(dir, String(f).padStart(5, '0') + '.png'));
  }
  console.log(job.name, n, 'frames');
}

(async () => {
  const t0 = Date.now();
  fs.mkdirSync(path.join(W, 'qc'), { recursive: true });
  const queue = [...jobs];
  await Promise.all(Array.from({ length: Math.min(workers, jobs.length) }, async () => {
    const p = await openPage();
    for (let job; (job = queue.shift());) await renderJob(p, job);
  }));
  console.log(`rendered ${jobs.length} scene(s) in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  // Edge's close() can hang after a long run; frames are on disk, so exit without closing.
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
