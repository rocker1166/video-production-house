#!/usr/bin/env node
// engine/film.cjs - the one renderer for page films: an HTML page whose picture is a function of time (for example style html-teaser).
// A job never writes its own renderer. Start a film from engine/film-template/ and use these commands. All times are seconds.
//
//   node engine/film.cjs info   <film>                               size, fps, length, acts, draw mode, page load time
//   node engine/film.cjs stills <film> --at 1,2.5,7 [--sheet]         full-size PNGs at exact times (ONE call for all the times you need)
//   node engine/film.cjs stills <film> --n 12 [--from 10 --to 40] [--sheet]   evenly spaced stills
//   node engine/film.cjs pure   <film> [--at 12,90.4]                 gate: a direct seek shows the same picture as playing in order (grain-level noise is ignored)
//   node engine/film.cjs frames <film> [--changed | --acts a6,a7 | --from 10 --to 40] [--draft] [--clean]
//   node engine/film.cjs encode <film> <out.mp4> [--audio mix.wav] [--draft]   frames -> mp4, then the ship gates
//   node engine/film.cjs draft  <film> <out.mp4> [--audio mix.wav] [--all]     QC cut: JPEG frames, only changed acts re-rendered, fast encode, gates
//                               (--from 10 --to 13 makes a 3 s sample of that stretch: the freeze test before a full render)
//   node engine/film.cjs final  <film> <out.mp4> --audio mix.wav [--serial]    master: clean full PNG render, encode, every ship gate
//   node engine/film.cjs check  <video> [--silent]                    ship gates on any video (--silent: picture gates only, for a cut without sound)
//   node engine/film.cjs sheet  <out.png> <image...> [--cols 6] [--width 360]   contact sheet
//   node engine/film.cjs selftest
//   <film> = a folder with index.html, or the html file. Options: --workers N  --out <dir>  --size 1920x1080  --fps 30  --duration 20.5  --query k=v
//
// The page contract (engine/film-template/index.html implements it):
//   window.seek(t)     draws the film at t seconds; may be async. No wall clock, no unseeded random, no CSS transitions.
//   window.__ready     true, or a Promise that resolves when fonts, images and acts are built; window.__error = message on failure.
//   window.filmInfo()  { fps, width, height, total, acts: [{ id, from, to }] }. Without it pass --size, --fps and --duration.
//   ?export=1 is always sent (hide preview controls). ?acts=a,b is sent by `stills --acts`: the page may load only those acts.
//   One act = one file acts/<id>.<ext>. That is what makes `--changed` work: an edited act file re-renders that act's time range only;
//   any other changed file the page loads (index.html, lib, fonts, data) re-renders the whole film.
//
// Rules the tool enforces:
//   - ONE render at a time per user on this machine (lock file ~/.cache/reeltools/render.lock): a second `frames`, `encode`, `draft`
//     or `final` waits for the first. `info`, `stills` and `pure` use one or two browsers and do not take the lock.
//   - Draws on the GPU when the machine has one (engine/browser.cjs; BROWSER_GPU=0 forces software) and prints the draw mode it got.
//   - One film, one draw mode: GPU and software frames differ at antialiased edges, so a frame folder never mixes them.
//   - `final` always renders every frame again. `--changed` trusts the act files, so it is for drafts, not for the master.
//   - One picture per time (`pure`): run by `draft` and `final`. A page that fails it gets fixed, or its master is rendered with
//     --serial (one worker, every frame in order: exact, several times slower).
//   - `final` sets the ledger's unlogged flag: log the run (`ledger/house.py log`). If the flag cannot be written, `final` fails.
//   - Temp files of one run live in one folder under $FILM_TMP, else the system temp folder, and are removed when the run ends.
//     Chrome needs a short path there (a unix socket, 108 characters in all): set FILM_TMP to a short folder if the system one is long or full.
'use strict';
const fs = require('fs'), os = require('os'), path = require('path'), cp = require('child_process'), crypto = require('crypto'), url = require('url');
const { launch, gpuArgs } = require('./browser.cjs');

const BLOCK = 24;                                  // fewer frames than this per worker is not worth another browser
let LOCK = path.join(os.homedir(), '.cache', 'reeltools', 'render.lock');   // selftest points this at its own file
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const now = () => Number(process.hrtime.bigint() / 1000000n);
const sha = (f) => { try { return crypto.createHash('sha1').update(fs.readFileSync(f)).digest('hex'); } catch (e) { return 'missing'; } };
const readJson = (f) => { try { return JSON.parse(fs.readFileSync(f, 'utf8')); } catch (e) { return null; } };
const frameName = (f, ext) => String(f).padStart(5, '0') + '.' + ext;
class Stop extends Error {}
const stop = (m) => { throw new Stop(m); };

// ---- temp folder: one per run, short path (Chrome puts a unix socket under TMPDIR, 108 characters max), removed on exit ----
let TMP = null;
const dropTmp = () => { try { if (TMP) fs.rmSync(TMP, { recursive: true, force: true }); } catch (e) {} };
function tmpRoot() {
  if (TMP) return TMP;
  for (const b of [process.env.FILM_TMP, os.tmpdir(), '/tmp'].filter(Boolean)) {
    if (b.length > 48) continue;
    try { fs.mkdirSync(b, { recursive: true }); TMP = fs.mkdtempSync(path.join(b, 'film-')); break; } catch (e) {}
  }
  if (!TMP) stop('no short writable temp folder: set FILM_TMP to a short path');
  process.env.TMPDIR = TMP;
  process.on('exit', dropTmp);
  return TMP;
}

// ---- render lock: one render at a time per user ----
// The lock file names its owner (pid) and the boot it was made in. A lock whose owner is gone, or that is left from an earlier boot,
// is moved aside by ONE waiter (rename is atomic) and the wait goes on; a live owner is never robbed, however long it takes.
const bootTime = () => Math.round((Date.now() - os.uptime() * 1000) / 60000);   // minutes since 1970, stable within a boot
let held = false;
async function withLock(label, fn) {
  if (held) return fn();
  const lockFile = LOCK;
  fs.mkdirSync(path.dirname(lockFile), { recursive: true });
  const t0 = now(); let told = 0;
  for (;;) {
    try { fs.writeFileSync(lockFile, JSON.stringify({ pid: process.pid, boot: bootTime(), label, since: new Date().toISOString() }), { flag: 'wx' }); break; } catch (e) {
      if (e.code !== 'EEXIST') throw e;
      const o = readJson(lockFile); let age = 0, alive = false;
      try { age = Date.now() - fs.statSync(lockFile).mtimeMs; } catch (e2) { continue; }
      if (o && o.pid) {
        try { process.kill(o.pid, 0); alive = true; } catch (e2) { alive = e2.code === 'EPERM'; }
        if (o.boot != null && Math.abs(o.boot - bootTime()) > 2) alive = false;   // the pid belongs to another boot
      } else alive = age < 10000;                                                 // half-written lock: give it 10 s
      if (!alive) {
        const aside = lockFile + '.' + process.pid;
        try {
          fs.renameSync(lockFile, aside);                                          // only one waiter wins this
          const got = readJson(aside);
          if (got && o && got.pid !== o.pid) { try { fs.linkSync(aside, lockFile); } catch (e2) {} }   // it was a newer, live lock: put it back
          fs.unlinkSync(aside);
        } catch (e2) {}
        continue;
      }
      if (now() - told > 30000) { console.log(`waiting: another render is running (pid ${o.pid}, ${o.label}), ${((now() - t0) / 1000).toFixed(0)} s so far`); told = now(); }
      await sleep(500);
    }
  }
  held = true;
  const release = () => { const o = readJson(lockFile); if (o && o.pid === process.pid) { try { fs.unlinkSync(lockFile); } catch (e) {} } held = false; };
  process.on('exit', release);
  try { return await fn(); } finally { release(); process.removeListener('exit', release); }
}

// ---- the page ----
function resolveFilm(arg) {
  if (!arg) stop('which film? give a folder with index.html');
  const p = path.resolve(arg), html = fs.existsSync(p) && fs.statSync(p).isDirectory() ? path.join(p, 'index.html') : p;
  if (!fs.existsSync(html)) stop('no film page at ' + html);
  return { html, dir: path.dirname(html) };
}
const browsers = [];
async function closeAll() { const b = browsers.splice(0); await Promise.race([Promise.all(b.map((x) => x.close().catch(() => {}))), sleep(4000)]); }

// Load (or load again) the film page and wait until it says it is ready.
async function load(page, href) {
  await page.goto(href);
  const ready = page.evaluate(() => new Promise((res) => {   // resolves to null when ready, or to the error text
    let waiting = false;
    const iv = setInterval(() => {
      if (window.__error) { clearInterval(iv); res(String(window.__error)); }
      else if (window.__ready !== undefined && !waiting) { waiting = true; Promise.resolve(window.__ready).then(() => { clearInterval(iv); res(null); }, (e) => { clearInterval(iv); res(String((e && e.message) || e)); }); }
    }, 50);
  }));
  let timer; const late = new Promise((res) => { timer = setTimeout(() => res('TIMEOUT'), 120000); });
  const err = await Promise.race([ready, late]); clearTimeout(timer);
  if (err === 'TIMEOUT') stop('page not ready after 120 s: it must set window.__ready (and window.__error on failure)');
  if (err) stop('page error: ' + err);
  if (!(await page.evaluate(() => typeof window.seek === 'function'))) stop('page has no window.seek(t)');
  await page.evaluate(async () => { await window.seek(0); });   // never return seek's value: a returned timeline object would be serialised
}

async function open(film, o) {
  tmpRoot();
  const browser = await launch({ gpu: true }); browsers.push(browser);
  process.removeListener('exit', dropTmp); process.on('exit', dropTmp);   // keep it last: Playwright's own exit hook must stop the browsers first
  let mode = 'unknown';
  try { const st = (await (await browser.newBrowserCDPSession()).send('SystemInfo.getInfo')).gpu.featureStatus || {}; mode = String(st.rasterization || '').startsWith('enabled') ? 'gpu' : 'software'; } catch (e) {}
  const page = await browser.newPage({ viewport: { width: o.width, height: o.height }, deviceScaleFactor: 1 });
  const reqs = new Set();
  page.on('request', (r) => reqs.add(r.url().split(/[?#]/)[0]));
  page.on('pageerror', (e) => console.error('pageerror:', e.message));
  page.on('console', (m) => { if (m.type() === 'error') console.error('console.error:', m.text()); });
  const q = ['export=1', o.only ? 'acts=' + o.only : '', o.query || ''].filter(Boolean).join('&'), href = url.pathToFileURL(film.html).href + '?' + q;
  const t0 = now();
  await load(page, href);
  const loadMs = now() - t0;
  const info = await page.evaluate(() => {
    const f = (typeof window.filmInfo === 'function' ? window.filmInfo() : window.FILM) || {};
    return { fps: f.fps, width: f.width, height: f.height, total: f.total != null ? f.total : f.duration, acts: (f.acts || []).map((a) => ({ id: String(a.id), from: +a.from, to: +a.to })) };
  });
  if (!o.sized && !o.forced && info.width && info.height && (info.width !== o.width || info.height !== o.height)) {   // the page knows its own size: reopen at it
    browsers.splice(browsers.indexOf(browser), 1); await Promise.race([browser.close().catch(() => {}), sleep(3000)]);
    return open(film, { ...o, width: info.width, height: info.height, sized: true });
  }
  const cdp = await page.context().newCDPSession(page);
  return { page, cdp, mode, reqs, loadMs, info, href, size: { width: o.width, height: o.height } };
}

function metaOf(w, o) {
  const fps = +o.fps || w.info.fps || 30, total = +o.duration || w.info.total;
  if (!total) stop('the page gives no length: add window.filmInfo() or pass --duration <seconds>');
  return { fps, total, width: w.size.width, height: w.size.height, acts: w.info.acts, frames: Math.ceil(total * fps - 1e-9) };
}
function sizeOpt(o) {
  const m = /^(\d+)x(\d+)$/.exec(o.size || '');
  return m ? { width: +m[1], height: +m[2], forced: true } : { width: 1080, height: 1920 };
}
const deps = (workers) => { const d = {}; for (const w of workers) for (const u of w.reqs) if (u.startsWith('file:')) { const f = url.fileURLToPath(u); d[f] = d[f] || sha(f); } return d; };
const network = (workers) => [...new Set(workers.flatMap((w) => [...w.reqs]).filter((u) => /^https?:/.test(u)))];

async function render(film, first, jobs, o) {   // jobs: [{ t, file }] in time order
  const nW = Math.max(1, Math.min(o.workers, Math.ceil(jobs.length / BLOCK)));
  // One contiguous run per worker: few seams, and forward seeks are cheap.
  const chunks = Array.from({ length: nW }, (_, k) => jobs.slice(Math.floor((jobs.length * k) / nW), Math.floor((jobs.length * (k + 1)) / nW)));
  const shot = o.format === 'jpg' ? { format: 'jpeg', quality: 90 } : { format: 'png', optimizeForSpeed: true };
  const draw = async (w, j) => {
    await w.page.evaluate(async (t) => { await window.seek(t); }, j.t);
    fs.writeFileSync(j.file + '.part', Buffer.from((await w.cdp.send('Page.captureScreenshot', shot)).data, 'base64'));
    fs.renameSync(j.file + '.part', j.file);
  };
  const t0 = now();
  let alone = 0;                                     // ms per frame for one worker with the machine to itself
  if (nW > 1) { const head = chunks[0].splice(0, Math.min(6, chunks[0].length)); const a = now(); for (const j of head) await draw(first, j); alone = (now() - a) / head.length; }
  const more = await Promise.all(Array.from({ length: nW - 1 }, () => open(film, { ...first.size, sized: true, only: o.only, query: o.query })));
  const workers = [first, ...more];
  if (new Set(workers.map((w) => w.mode)).size > 1) stop('workers disagree on the draw mode (' + workers.map((w) => w.mode).join(', ') + '): refusing to mix GPU and software frames. Set BROWSER_GPU=0 to force software.');
  const t1 = now(), left = chunks.reduce((n, c) => n + c.length, 0);
  await Promise.all(workers.map(async (w, k) => { for (const j of chunks[k]) await draw(w, j); }));
  const secs = (now() - t0) / 1000, each = left ? ((now() - t1) * nW) / left : 0;   // ms per frame per worker while all of them run
  const fighting = nW > 1 && alone > 0 && each > alone * Math.max(3, nW / 2);
  if (fighting) console.log(`WARNING ${nW} workers ran at ${each.toFixed(0)} ms per frame each; one alone took ${alone.toFixed(0)} ms. They are fighting for the machine: try --workers ${Math.max(1, Math.floor(nW / 3))}.`);
  return { workers, secs, fps: jobs.length / Math.max(secs, 0.001), nW, alone, each };
}
function loadNote(w) {
  const s = (w.loadMs / 1000).toFixed(1);
  return w.loadMs > 2000 ? `page load ${s} s: SLOW. Every sample call pays this. Do less work at load` + (w.mode === 'software' ? ' (draw mode is software: a GPU cuts load time)' : '') : `page load ${s} s`;
}

// ---- commands ----
async function cmdInfo(arg, o) {
  const film = resolveFilm(arg), w = await open(film, { ...sizeOpt(o), query: o.query }), m = metaOf(w, o);
  console.log(`${film.html}\n${m.width}x${m.height}, ${m.fps} fps, ${m.total} s, ${m.frames} frames, draw mode ${w.mode}, ${loadNote(w)}`);
  console.log(m.acts.length ? 'acts: ' + m.acts.map((a) => `${a.id} ${a.from}-${a.to}`).join(' | ') : 'acts: none declared (window.filmInfo().acts): --acts and --changed work on the whole film only');
  const net = network([w]); if (net.length) console.log('WARNING page loads from the network (not repeatable): ' + net.slice(0, 5).join(' '));
  const l = readJson(LOCK); console.log(l ? `render lock: held by pid ${l.pid} (${l.label}) since ${l.since}` : 'render lock: free');
  return m;
}

async function cmdStills(arg, o) {
  const film = resolveFilm(arg), w = await open(film, { ...sizeOpt(o), only: o.acts, query: o.query }), m = metaOf(w, o);
  let times;
  if (o.at) times = String(o.at).split(',').map(Number);
  else if (o.n) { const a = +o.from || 0, b = o.to != null ? +o.to : m.total, n = +o.n; times = Array.from({ length: n }, (_, i) => a + ((b - a) * (i + 0.5)) / n); }
  else stop('stills needs --at t1,t2,... or --n <count>');
  if (times.some((t) => !(t >= 0))) stop('bad time in --at');
  const dir = path.resolve(o.out || path.join(film.dir, 'stills')); fs.mkdirSync(dir, { recursive: true });
  const jobs = times.map((t) => { const f = Math.min(m.frames - 1, Math.round(t * m.fps)); return { t: f / m.fps, file: path.join(dir, `t_${(f / m.fps).toFixed(2).padStart(7, '0')}.png`) }; });
  const r = await render(film, w, jobs, { workers: Math.min(4, Math.ceil(jobs.length / 12)), format: 'png', only: o.acts, query: o.query });
  const cues = await w.page.evaluate(() => (window.cues === undefined ? null : JSON.parse(JSON.stringify(window.cues)))).catch(() => null);
  if (cues) fs.writeFileSync(path.join(dir, 'cues.json'), JSON.stringify(cues));
  console.log(`${jobs.length} still(s) in ${r.secs.toFixed(1)} s, draw mode ${w.mode}, ${loadNote(w)}`);
  jobs.forEach((j) => console.log(j.file));
  if (o.sheet) console.log(sheet(path.join(dir, 'sheet.png'), jobs.map((j) => j.file), o));
  return jobs.map((j) => j.file);
}

// Which frames does --changed need? Compare what the page loads now with what it loaded for the frames on disk.
function changedPlan(man, m, mode, cur, filmDir) {
  if (!man || !man.deps || !Object.keys(man.deps).length) return { all: true, why: 'no earlier full render' };
  const ids = m.acts.map((a) => a.id);
  if (JSON.stringify(ids) !== JSON.stringify((man.acts || []).map((a) => a.id))) return { all: true, why: 'the act list changed' };
  const files = [...new Set([...Object.keys(cur), ...Object.keys(man.deps)])].filter((f) => cur[f] !== man.deps[f]);
  const acts = new Set(m.acts.filter((a, i) => a.from !== man.acts[i].from || a.to !== man.acts[i].to).map((a) => a.id));   // retimed acts
  for (const f of files) {
    const hit = /^acts\/([^/]+)\.[A-Za-z0-9]+$/.exec(path.relative(filmDir, f).split(path.sep).join('/'));
    if (hit && ids.includes(hit[1])) acts.add(hit[1]); else return { all: true, why: 'a shared file changed: ' + path.relative(filmDir, f) };
  }
  return { all: false, acts: [...acts], why: acts.size ? 'changed acts: ' + [...acts].join(', ') : 'nothing changed' };
}

async function cmdFrames(arg, o) {
  return withLock('frames ' + arg, async () => {
    const film = resolveFilm(arg), ext = o.draft ? 'jpg' : 'png';
    const dir = path.resolve(o.out || path.join(film.dir, o.draft ? 'frames-draft' : 'frames')); fs.mkdirSync(dir, { recursive: true });
    const w = await open(film, { ...sizeOpt(o), query: o.query }), m = metaOf(w, o), mfile = path.join(dir, 'film.json');
    let man = readJson(mfile);
    const fits = man && man.mode === w.mode && man.format === ext && ['fps', 'total', 'width', 'height', 'frames'].every((k) => man[k] === m[k]);
    const isFrame = (f) => /^\d{5}\.(png|jpg)(\.part)?$/.test(f);
    if (o.clean || o.fresh || !fits) {
      const old = fs.readdirSync(dir).filter(isFrame);
      if (old.length && !man && !o.clean) stop(`${dir} holds ${old.length} frame(s) this tool did not make. Pass --clean to replace them, or --out <another folder>.`);
      if (old.length) console.log(`${o.clean ? '--clean' : o.fresh ? 'a master is drawn from nothing' : 'frames on disk are from another size, length or draw mode'}: removing ${old.length} old frame(s)`);
      old.forEach((f) => fs.unlinkSync(path.join(dir, f)));
      man = null;
    }
    const range = (a, b) => { const out = []; for (let f = Math.max(0, Math.floor(a * m.fps + 1e-9)); f < Math.min(m.frames, Math.ceil(b * m.fps - 1e-9)); f++) out.push(f); return out; };
    const actRange = (id) => { const a = m.acts.find((x) => x.id === id); if (!a) stop(`unknown act ${id}; the film has: ${m.acts.map((x) => x.id).join(', ') || 'none'}`); return range(a.from, a.to); };
    const cur = deps([w]);
    let want, why, full = false;
    if (o.changed) {
      const p = changedPlan(man, m, w.mode, { ...(man ? Object.fromEntries(Object.keys(man.deps || {}).map((f) => [f, sha(f)])) : {}), ...cur }, film.dir);
      why = p.why; full = true;
      want = new Set(p.all ? range(0, m.total) : p.acts.flatMap(actRange));
      const before = want.size;
      for (let f = 0; f < m.frames; f++) if (!fs.existsSync(path.join(dir, frameName(f, ext)))) want.add(f);   // frames missing on disk
      if (!p.all && want.size > before) why += `, ${want.size - before} frame(s) missing on disk`;
    } else if (o.acts) { want = new Set(String(o.acts).split(',').flatMap(actRange)); why = 'acts ' + o.acts; }
    else if (o.from != null || o.to != null) { want = new Set(range(+o.from || 0, o.to != null ? +o.to : m.total)); why = `${+o.from || 0} s to ${o.to != null ? +o.to : m.total} s`; }
    else { want = new Set(range(0, m.total)); why = 'whole film'; full = true; }
    const list = [...want].sort((a, b) => a - b), jobs = list.map((f) => ({ t: f / m.fps, file: path.join(dir, frameName(f, ext)) }));
    let workers = [w], line = `0 of ${m.frames} frames to render (${why})`;
    if (jobs.length) {
      const r = await render(film, w, jobs, { workers: +o.workers || Math.max(2, Math.min(12, os.cpus().length - 4)), format: ext, query: o.query });
      workers = r.workers;
      line = `rendered ${jobs.length} of ${m.frames} frames (${why}) in ${r.secs.toFixed(1)} s: ${r.fps.toFixed(1)} frames/s, ${r.nW} worker(s), draw mode ${w.mode}`;
    }
    const net = network(workers); if (net.length) console.log('WARNING page loads from the network (not repeatable): ' + net.slice(0, 5).join(' '));
    // A full or --changed render makes the folder current for everything the page loaded. A hand-picked range leaves the record alone.
    const all = { ...(man && man.deps ? Object.fromEntries(Object.keys(man.deps).map((f) => [f, sha(f)])) : {}), ...deps(workers) };
    fs.writeFileSync(mfile, JSON.stringify({ fps: m.fps, total: m.total, width: m.width, height: m.height, frames: m.frames, mode: w.mode, format: ext, acts: full ? m.acts : (man && man.acts) || m.acts, deps: full ? all : (man && man.deps) || {} }));
    console.log(`${line}\n${loadNote(w)} -> ${dir}`);
    return { rendered: jobs.length, dir, meta: m, mode: w.mode };
  });
}

function ffmpeg(args, capture) {
  const r = cp.spawnSync('ffmpeg', args, { encoding: 'utf8', stdio: capture ? ['ignore', 'pipe', 'pipe'] : ['ignore', 'inherit', 'inherit'], maxBuffer: 1 << 28 });
  if (r.error) stop('ffmpeg did not start: ' + r.error.message);
  if (r.status !== 0 && !capture) stop('ffmpeg failed');
  return r;
}

async function cmdEncode(arg, out, o) {
  if (!out) stop('encode needs an output file: film.cjs encode <film> <out.mp4>');
  return withLock('encode ' + out, async () => {
    const film = resolveFilm(arg), ext = o.draft ? 'jpg' : 'png';
    const dir = path.resolve(o.frames || path.join(film.dir, o.draft ? 'frames-draft' : 'frames')), man = readJson(path.join(dir, 'film.json'));
    if (!man) stop(`no rendered frames in ${dir}: run film.cjs frames first`);
    const a = o.from != null ? Math.max(0, Math.floor(+o.from * man.fps + 1e-9)) : 0, b = o.to != null ? Math.min(man.frames, Math.ceil(+o.to * man.fps - 1e-9)) : man.frames;
    const gone = []; for (let f = a; f < b && gone.length < 5; f++) if (!fs.existsSync(path.join(dir, frameName(f, ext)))) gone.push(f);
    if (gone.length) stop(`frames missing in ${dir} (first: ${gone.join(', ')}): run film.cjs frames --changed`);
    fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
    const args = ['-v', 'error', '-y', '-framerate', String(man.fps), '-start_number', String(a), '-i', path.join(dir, '%05d.' + ext)];
    if (o.audio) { if (!fs.existsSync(o.audio)) stop('no audio file ' + o.audio); args.push('-ss', String(a / man.fps), '-t', String((b - a) / man.fps), '-i', o.audio); }
    args.push('-frames:v', String(b - a), '-c:v', 'libx264', ...(o.draft ? ['-preset', 'veryfast', '-crf', '23'] : ['-preset', 'medium', '-crf', '18', '-maxrate', '18M', '-bufsize', '36M']), '-pix_fmt', 'yuv420p', '-r', String(man.fps));
    if (o.audio) args.push('-c:a', 'aac', '-b:a', '192k', '-ar', '48000');
    args.push('-movflags', '+faststart', out);
    const t0 = now(); ffmpeg(args);
    console.log(`encoded ${out}: ${b - a} frames, ${((b - a) / man.fps).toFixed(2)} s, ${(fs.statSync(out).size / 1e6).toFixed(1)} MB, ${((now() - t0) / 1000).toFixed(0)} s to encode${o.draft ? ' (draft quality)' : ''}`);
    return cmdCheck(out, { silent: !o.audio });
  });
}

// Ship gates, the same numbers as engine/build.py check: A/V length, no still hold >= 0.4 s, no black frames, -16..-13 LUFS, peak <= -1 dB.
function cmdCheck(video, o) {
  if (!video || !fs.existsSync(video)) stop('no video file ' + video);
  const dur = (s) => { const r = cp.spawnSync('ffprobe', ['-v', 'error', '-select_streams', s, '-show_entries', 'stream=duration', '-of', 'csv=p=0', video], { encoding: 'utf8' }); return parseFloat((r.stdout || '').trim().split('\n')[0]); };
  const vd = dur('v:0'), ad = dur('a:0'), hasAudio = !Number.isNaN(ad);
  const log = ffmpeg(['-hide_banner', '-v', 'info', '-i', video, '-vf', 'freezedetect=n=-60dB:d=0.4,blackdetect=d=0.1:pix_th=0.05', ...(hasAudio ? ['-af', 'ebur128=peak=true'] : ['-an']), '-f', 'null', '-'], true).stderr || '';
  const all = (re) => [...log.matchAll(re)].map((x) => x[1]);
  const freezes = all(/freeze_start: ([\d.]+)/g), blacks = all(/black_start:([\d.]+)/g);
  let ok = true; const say = (pass, text) => { console.log(`[${pass ? 'PASS' : 'FAIL'}] ${text}`); ok = ok && pass; };
  if (hasAudio) say(Math.abs(vd - ad) < 0.05, `A/V sync: video ${vd.toFixed(3)} s vs audio ${ad.toFixed(3)} s`);
  say(!freezes.length, 'no still hold >= 0.4 s' + (freezes.length ? ': freeze_start ' + freezes.join(' ') : ''));
  say(!blacks.length, 'no black frames' + (blacks.length ? ': black_start ' + blacks.join(' ') : ''));
  if (hasAudio) {
    const lufs = parseFloat(all(/I:\s+(-?[\d.]+) LUFS/g).pop()), peak = parseFloat(all(/Peak:\s+(-?[\d.]+) dBFS/g).pop());
    say(lufs >= -16 && lufs <= -13 && peak <= -1, `loudness ${lufs} LUFS, peak ${peak} dBFS (want -16..-13, <= -1)`);
  } else if (!o.silent) say(false, 'no audio stream (use --silent for a picture-only cut)');
  console.log(hasAudio || !o.silent ? 'SHIP GATES: ' + (ok ? 'ALL PASS' : 'FIX BEFORE SHOWING') : 'PICTURE GATES: ' + (ok ? 'ALL PASS' : 'FIX') + ' (no sound: not a master)');
  return ok;
}

function sheet(out, imgs, o) {
  if (!imgs.length) stop('sheet needs images');
  const probe = cp.spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', imgs[0]], { encoding: 'utf8' }).stdout.trim().split(',').map(Number);
  const tall = probe[1] > probe[0], cols = Math.min(imgs.length, +o.cols || (tall ? 6 : 4)), width = +o.width || (tall ? 360 : 480);
  const list = path.join(tmpRoot(), 'sheet.txt');
  fs.writeFileSync(list, imgs.map((f) => `file '${path.resolve(f).replace(/'/g, "'\\''")}'\nduration 1`).join('\n'));
  ffmpeg(['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-vf', `fps=1,scale=${width}:-2,tile=${cols}x${Math.ceil(imgs.length / cols)}:padding=6:color=0x777777`, '-frames:v', '1', out]);
  return `sheet (${cols} per row, left to right, top to bottom): ${out}`;
}

// One picture per time. A render worker and a stills call jump straight to a time; a viewer plays in order. Both must show the same
// picture, or parallel rendering, changed-act re-rendering and QC stills cannot be trusted. Samples: 12 spread over the film plus
// 0.5 s into every act (or --at). The usual cause of a FAIL: a tween without explicit start values, a counter, a value read back from the DOM.
async function cmdPure(arg, o) {
  const film = resolveFilm(arg), w = await open(film, { ...sizeOpt(o), query: o.query }), m = metaOf(w, o);
  const times = o.at ? String(o.at).split(',').map(Number) : [...Array.from({ length: 12 }, (_, i) => (m.total * (i + 0.5)) / 12), ...m.acts.map((a) => Math.min(a.to, a.from + 0.5))];
  const frames = [...new Set(times.map((t) => Math.min(m.frames - 1, Math.max(0, Math.round(t * m.fps)))))].sort((a, b) => a - b).slice(0, 32);
  const shot = async () => Buffer.from((await w.cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true })).data, 'base64');
  const seek = (f) => w.page.evaluate(async (t) => { await window.seek(t); }, f / m.fps);
  const want = new Set(frames), inOrder = new Map(), t0 = now();
  for (let f = 0; f <= frames[frames.length - 1]; f++) { await seek(f); if (want.has(f)) inOrder.set(f, await shot()); }   // play in order
  const bad = [];
  for (const f of frames) {                                                                                               // fresh page, straight there
    await load(w.page, w.href);
    w.cdp = await w.page.context().newCDPSession(w.page);   // a file:// navigation detaches the earlier session
    await seek(f);
    const direct = await shot();
    if (direct.equals(inOrder.get(f))) continue;
    const a = path.join(tmpRoot(), 'pure-a.png'), b = path.join(tmpRoot(), 'pure-b.png'); fs.writeFileSync(a, direct); fs.writeFileSync(b, inOrder.get(f));
    // Count pixels that differ by more than 40 of 255: film grain and antialiasing stay far below that, a moved edge does not.
    const r = ffmpeg(['-hide_banner', '-v', 'error', '-i', a, '-i', b, '-filter_complex', "[0:v]format=gbrp[x];[1:v]format=gbrp[y];[x][y]blend=all_mode=difference,format=gray,lutyuv=y='gt(val,40)*255',signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", '-f', 'null', '-'], true);
    const hit = /YAVG=([\d.]+)/.exec(r.stdout || ''), moved = hit ? Math.round((parseFloat(hit[1]) / 255) * m.width * m.height) : Infinity;
    if (moved > Math.max(20, m.width * m.height * 2e-5)) bad.push(`${(f / m.fps).toFixed(2)} s (${moved} px)`);
  }
  await closeAll();
  const secs = ((now() - t0) / 1000).toFixed(0);
  if (!bad.length) console.log(`[PASS] one picture per time: ${frames.length} sample times, a direct seek equals playing in order (${secs} s)`);
  else console.log(`[FAIL] one picture per time: a direct seek differs from playing in order at ${bad.join(', ')}.\n       The picture depends on how the clock got there, so stills, parallel workers and changed-act renders are not exact.\n       Fix the page (explicit start values in tweens, no counters, no values read back from the DOM), or render the master with --serial.`);
  return !bad.length;
}

async function cmdDraft(arg, out, o) {
  return withLock('draft ' + out, async () => {
    await cmdFrames(arg, { ...o, draft: true, changed: !o.all && !o.acts && o.from == null && o.to == null, from: o.from, to: o.to });
    await closeAll();
    const ok = await cmdEncode(arg, out, { draft: true, audio: o.audio, frames: o.out, from: o.from, to: o.to });
    if (o.from != null || o.to != null) return ok;   // a short sample: the whole-film check would cost more than the sample
    return (await cmdPure(arg, { size: o.size, fps: o.fps, duration: o.duration, query: o.query })) && ok;   // found early, a path-dependent page is a small fix
  });
}

async function cmdFinal(arg, out, o) {
  if (!o.audio) stop('final needs --audio <mix.wav>: a master without sound cannot pass the ship gates');
  return withLock('final ' + out, async () => {
    if (o.serial) console.log('[PASS] one picture per time: --serial, one worker draws every frame in order');
    else if (!(await cmdPure(arg, { size: o.size, fps: o.fps, duration: o.duration, query: o.query }))) { console.log('NOT rendered: fix the page, or run final again with --serial (one worker, exact, several times slower)'); return false; }
    const r = await cmdFrames(arg, { ...o, draft: false, changed: false, acts: null, from: null, to: null, fresh: true, workers: o.serial ? 1 : o.workers });
    await closeAll();
    const ok = await cmdEncode(arg, out, { audio: o.audio, frames: o.out });
    let marked = true;
    if (ok) {   // a master is a run: the Stop hook asks for `house.py log` until it is recorded
      try {
        const d = cp.execFileSync('python3', [path.join(__dirname, '..', 'ledger', 'home.py'), 'data'], { encoding: 'utf8' }).trim();
        fs.mkdirSync(path.join(d, 'ledger'), { recursive: true }); fs.closeSync(fs.openSync(path.join(d, 'ledger', '.unlogged'), 'w'));
      } catch (e) { marked = false; console.log(`[FAIL] ledger: the unlogged flag could not be set (${String(e.message).split('\n')[0]}). The master exists, but nothing will remind you: record the run now with \`python3 ledger/house.py log\`.`); }
    }
    if (ok && !o.keepFrames) { fs.readdirSync(r.dir).filter((f) => /^\d{5}\.png$/.test(f)).forEach((f) => fs.unlinkSync(path.join(r.dir, f))); fs.rmSync(path.join(r.dir, 'film.json'), { force: true }); console.log(`removed ${r.meta.frames} PNG frames (rebuildable; --keep-frames keeps them)`); }
    console.log(ok ? `MASTER: ${out}\nNow look at the master itself: frames from this file at the hook, the climax, the end and every time QC flagged. Gates do not see a wrong picture.` : 'NOT a master: fix the failed gate (frames are kept; after an audio-only fix run `encode` again)');
    return ok && marked;
  });
}

async function selftest() {
  const assert = (c, m) => { if (!c) throw new Error('selftest: ' + m); };
  const stops = async (fn) => { try { await fn(); return false; } catch (e) { await closeAll(); return e instanceof Stop; } };
  const root = fs.mkdtempSync(path.join(tmpRoot(), 'selftest-')), film = path.join(root, 'film'), keep = { ...process.env };
  fs.cpSync(path.join(__dirname, 'film-template'), film, { recursive: true });
  LOCK = path.join(root, 'lock');                                   // never wait behind, or block, a real render
  process.env.HOUSE_HOME = path.join(root, 'home'); fs.mkdirSync(process.env.HOUSE_HOME);   // the ledger flag goes to a throwaway data home
  // GPU drawing is asked for by the caller or forced by the owner, and BROWSER_GPU=0 always wins
  delete process.env.BROWSER_GPU; assert(gpuArgs(false).length === 0, 'no GPU flags unless a caller asks');
  process.env.BROWSER_GPU = '1'; assert(gpuArgs(false).length > 0, 'BROWSER_GPU=1 forces the flags');
  process.env.BROWSER_GPU = '0'; assert(gpuArgs(true).length === 0, 'BROWSER_GPU=0 refuses the flags');
  if (keep.BROWSER_GPU === undefined) delete process.env.BROWSER_GPU; else process.env.BROWSER_GPU = keep.BROWSER_GPU;
  const m = await cmdInfo(film, {}); await closeAll();
  assert(m.frames === 120 && m.acts.length === 2 && m.width === 1080, 'template is 4 s, 2 acts, 1080 wide');
  const st = await cmdStills(film, { at: '0.5,2.5', sheet: true }); await closeAll();
  assert(st.every((f) => fs.statSync(f).size > 1000) && fs.existsSync(path.join(film, 'stills', 'sheet.png')), 'stills and sheet written');
  const run = async (o = {}) => { const r = await cmdFrames(film, { draft: true, changed: true, workers: 2, ...o }); await closeAll(); return r.rendered; };
  assert((await run()) === 120, 'first render draws every frame');
  assert((await run()) === 0, 'nothing changed: nothing rendered');
  fs.appendFileSync(path.join(film, 'acts', 'a2.js'), '\n// touched\n');
  assert((await run()) === 60, 'an edited act re-renders only its own 2 s');
  fs.appendFileSync(path.join(film, 'index.html'), '\n<!-- touched -->\n');
  assert((await run()) === 120, 'an edited shared file re-renders the whole film');
  fs.unlinkSync(path.join(film, 'frames-draft', frameName(7, 'jpg')));
  assert((await run()) === 1, 'a missing frame is drawn again');
  assert((await cmdEncode(film, path.join(root, 'draft.mp4'), { draft: true })) === true, 'the template passes the picture gates');
  assert((await cmdPure(film, {})) === true, 'the template shows one picture per time');
  const bad = path.join(root, 'impure'); fs.cpSync(path.join(__dirname, 'film-template'), bad, { recursive: true });
  fs.writeFileSync(path.join(bad, 'acts', 'a1.js'), fs.readFileSync(path.join(bad, 'acts', 'a1.js'), 'utf8').replace('240 + 300 * u', '240 + 300 * u + (this.n = (this.n || 0) + 1)'));
  assert((await cmdPure(bad, {})) === false, 'a page that counts its seeks must fail the one-picture-per-time gate');
  ffmpeg(['-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=0x8899AA:s=320x568:r=30:d=2', '-pix_fmt', 'yuv420p', path.join(root, 'still.mp4')]);
  assert(cmdCheck(path.join(root, 'still.mp4'), { silent: true }) === false, 'a held picture must fail the freeze gate');
  ffmpeg(['-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=320x568:r=30:d=1', '-pix_fmt', 'yuv420p', path.join(root, 'black.mp4')]);
  assert(cmdCheck(path.join(root, 'black.mp4'), { silent: true }) === false, 'black frames must fail');
  // sound gates, the sample cut, the QC cut and the master (a 1 kHz tone: about -14 LUFS loud, about -34 LUFS quiet)
  const loud = path.join(root, 'loud.wav'), quiet = path.join(root, 'quiet.wav');
  ffmpeg(['-v', 'error', '-y', '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=4,volume=7dB', '-ar', '48000', loud]);
  ffmpeg(['-v', 'error', '-y', '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=4,volume=-13dB', '-ar', '48000', quiet]);
  assert((await cmdDraft(film, path.join(root, 'sample.mp4'), { from: 1, to: 2 })) === true && fs.existsSync(path.join(root, 'sample.mp4')), 'a 1 s sample cut');
  await closeAll();
  assert((await cmdDraft(film, path.join(root, 'qc.mp4'), { audio: loud })) === true, 'the QC cut passes picture, sound and one-picture gates');
  assert((await cmdEncode(film, path.join(root, 'quiet.mp4'), { draft: true, audio: quiet })) === false, 'a mix that is too quiet must fail the loudness gate');
  assert(await stops(() => cmdFinal(film, path.join(root, 'm.mp4'), {})), 'a master without sound is refused');
  const alien = path.join(root, 'alien'); fs.mkdirSync(alien); fs.writeFileSync(path.join(alien, '00001.png'), 'not ours');
  assert(await stops(() => cmdFinal(film, path.join(root, 'm.mp4'), { audio: loud, out: alien })), 'a master is not drawn over frames this tool did not make');
  assert(fs.readFileSync(path.join(alien, '00001.png'), 'utf8') === 'not ours', 'and those frames are left alone');
  assert((await cmdFinal(film, path.join(root, 'master.mp4'), { audio: loud })) === true, 'the template makes a master');
  assert(fs.existsSync(path.join(process.env.HOUSE_HOME, 'ledger', '.unlogged')), 'a master sets the unlogged flag');
  assert(!fs.readdirSync(path.join(film, 'frames')).some((f) => f.endsWith('.png')), 'and removes its PNG frames');
  // lock: a dead owner and a lock from another boot are replaced at once; a live owner makes the next render wait
  fs.writeFileSync(LOCK, JSON.stringify({ pid: 2 ** 22 + 12345, boot: bootTime(), label: 'dead' }));
  let t = now(); await withLock('a', async () => {}); assert(now() - t < 1500, 'a dead owner loses the lock');
  const child = cp.spawn(process.execPath, ['-e', 'setTimeout(()=>{},3000)'], { stdio: 'ignore' });
  fs.writeFileSync(LOCK, JSON.stringify({ pid: child.pid, boot: bootTime() - 9999, label: 'old boot' }));
  t = now(); await withLock('b', async () => {}); assert(now() - t < 1500, 'a lock from another boot is not honoured');
  fs.writeFileSync(LOCK, JSON.stringify({ pid: child.pid, boot: bootTime(), label: 'live' }));
  t = now(); await withLock('c', async () => {}); assert(now() - t >= 1000, 'a live owner makes the next render wait');
  assert(!fs.existsSync(LOCK), 'lock released');
  for (const k of ['HOUSE_HOME']) { if (keep[k] === undefined) delete process.env[k]; else process.env[k] = keep[k]; }
  fs.rmSync(root, { recursive: true, force: true });
  console.log('selftest ok');
}

async function main() {
  const argv = process.argv.slice(2), o = {};
  const VAL = ['at', 'n', 'from', 'to', 'acts', 'workers', 'out', 'size', 'fps', 'duration', 'audio', 'cols', 'width', 'query', 'frames'], FLAG = ['changed', 'draft', 'clean', 'sheet', 'silent', 'all', 'keep-frames', 'serial'];
  const pos = [];
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i].startsWith('--') ? argv[i].slice(2) : null;
    if (k && VAL.includes(k)) o[k] = argv[++i];
    else if (k && FLAG.includes(k)) o[k === 'keep-frames' ? 'keepFrames' : k] = true;
    else if (k) stop('unknown option --' + k);
    else pos.push(argv[i]);
  }
  const [cmd, a, b] = pos;
  let ok = true;
  if (cmd === 'info') await cmdInfo(a, o);
  else if (cmd === 'stills') await cmdStills(a, o);
  else if (cmd === 'frames') await cmdFrames(a, o);
  else if (cmd === 'encode') ok = await cmdEncode(a, b, o);
  else if (cmd === 'draft') ok = await cmdDraft(a, b, o);
  else if (cmd === 'final') ok = await cmdFinal(a, b, o);
  else if (cmd === 'pure') ok = await cmdPure(a, o);
  else if (cmd === 'check') ok = cmdCheck(a, o);
  else if (cmd === 'sheet') console.log(sheet(a, pos.slice(2), o));
  else if (cmd === 'selftest') await selftest();
  else stop('usage: film.cjs info|stills|pure|frames|encode|draft|final|check|sheet|selftest ...  (read the header of engine/film.cjs)');
  return ok;
}

if (require.main === module) {
  main().then(async (ok) => { await closeAll(); process.exit(ok ? 0 : 1); })
    .catch(async (e) => { console.error(e instanceof Stop ? 'film: ' + e.message : e); await closeAll(); process.exit(e instanceof Stop ? 2 : 1); });
}
module.exports = { cmdInfo, cmdStills, cmdPure, cmdFrames, cmdEncode, cmdDraft, cmdFinal, cmdCheck, sheet, withLock };
