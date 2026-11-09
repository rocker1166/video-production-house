// Effect library: reusable scenes that composite the creator's own video (a "plate") with graphics.
// A plate scene sets  "plate": true  in plan.json; build.py extracts that window's A-roll frames + person
// matte to plates/<scene>/, and render.cjs passes the dir as props.plateDir. Scenes then draw:
//   video   — the full frame              subject — the person only (matte-cut)
//   outline — a white boiling outline of the person (doodle)
// Every layer is a <canvas> moved with GSAP transforms (sub-pixel smooth, unlike ffmpeg zoompan).
// All plate scenes are opaque (alpha:false): they replace the A-roll for their window.

const PLATE = { dir: null, layers: [], frame: -1, seed: 1 };
const loadImg = src => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.onerror = () => r(null); i.src = src; });

function plateLayer(kind, style = '', z = 10) {
  const c = el(`<canvas class="abs" width="1080" height="1920" style="left:0;top:0;width:1080px;height:1920px;z-index:${z};transform-origin:50% 40%;${style}"></canvas>`);
  PLATE.layers.push({ kind, c, ctx: c.getContext('2d') });
  return c;
}
const pad5 = n => String(n).padStart(5, '0');
// Shrink a one-line headline until it fits `max` px wide (long words otherwise run off the frame).
function fit(node, max) { const fs = parseFloat(getComputedStyle(node).fontSize); const r = document.createRange(); r.selectNodeContents(node); const w = r.getBoundingClientRect().width; if (w > max) node.style.fontSize = fs * max / w + 'px'; }
// Seeded jitter so a re-render boils identically.
const rnd = n => { const x = Math.sin(n * 12.9898 + PLATE.seed * 78.233) * 43758.5453; return x - Math.floor(x); };

async function drawPlate(f) {
  if (!PLATE.dir || !PLATE.layers.length || f === PLATE.frame) return;
  PLATE.frame = f;
  const [v, m] = await Promise.all([loadImg(`file://${PLATE.dir}/v_${pad5(f)}.jpg`), loadImg(`file://${PLATE.dir}/m_${pad5(f)}.png`)]);
  if (!v) return;
  for (const { kind, ctx } of PLATE.layers) {
    ctx.globalCompositeOperation = 'source-over';
    ctx.clearRect(0, 0, 1080, 1920);
    if (kind === 'video') { ctx.drawImage(v, 0, 0, 1080, 1920); continue; }
    if (!m) continue;
    if (kind === 'subject') {
      ctx.drawImage(v, 0, 0, 1080, 1920);
      ctx.globalCompositeOperation = 'destination-in';
      ctx.drawImage(m, 0, 0, 1080, 1920);
    }
    if (kind === 'outline' || kind === 'sticker') {
      // Dilate the matte by stamping it round a circle, then cut the matte out: a ring hugging the body.
      const step = Math.floor(f / 3);          // boil at 10fps, like hand-drawn animation
      const r = kind === 'sticker' ? 16 : 7 + rnd(step) * 3;
      for (let a = 0; a < 16; a++) {
        const ang = a / 16 * Math.PI * 2 + (kind === 'outline' ? rnd(step + a) * .6 : 0);
        ctx.drawImage(m, Math.cos(ang) * r, Math.sin(ang) * r, 1080, 1920);
      }
      ctx.globalCompositeOperation = 'source-in';
      ctx.fillStyle = kind === 'sticker' ? '#FFFFFF' : '#F7F5EE'; ctx.fillRect(0, 0, 1080, 1920);
      ctx.globalCompositeOperation = 'destination-out';
      ctx.drawImage(m, 0, 0, 1080, 1920);
    }
  }
}

function usePlate(props) {
  PLATE.dir = props.plateDir || null; PLATE.layers = []; PLATE.frame = -1; PLATE.seed = (props.seed || 1);
  if (!PLATE.dir) throw new Error('plate scene without plateDir: set "plate": true on the scene in plan.json');
}
const ease = 'power2.inOut';

Object.assign(SCENES, {
  // 01 orbit — cards circle the person; behind them on the far side, in front on the near side.
  orbit(c, p) {
    usePlate(p);
    plateLayer('video', '', 1); plateLayer('subject', '', 10);
    const items = p.cards || ['Leads', 'Approvals', 'Invoices', 'Projects', 'Reports'];
    const cards = items.map(t => el(`<div class="abs doc" style="left:0;top:0;padding:22px 30px;border-radius:22px;font:700 40px Inter;white-space:nowrap">${t}</div>`));
    const st = { a: 0 };
    tl.to(st, { a: Math.PI * 2 * (p.turns || 0.8), duration: c.end, ease: 'none', onUpdate: () => cards.forEach((n, i) => {
      const ang = st.a + i / cards.length * Math.PI * 2, z = Math.sin(ang);
      gsap.set(n, { x: 540 + Math.cos(ang) * 400 - 120, y: (p.y || 760) + z * 90, scale: .8 + z * .25, zIndex: z > 0 ? 15 : 5, opacity: .55 + z * .45 });
    }) }, 0);
    cards.forEach((n, i) => cue('slide', .1 + i * .08));
  },

  // 02 couch wall — big type pinned to the wall behind the person (text-behind-subject).
  couchWall(c, p) {
    usePlate(p);
    plateLayer('video', '', 1); plateLayer('subject', '', 10);
    const words = (p.text || 'STOP CHASING').split(' ');
    words.forEach((w, i) => {
      const n = el(`<div class="abs head" style="left:0;right:0;top:${(p.y || 330) + i * 210}px;text-align:center;font-size:${p.size || 230}px;color:#fff;letter-spacing:-6px;z-index:5;text-shadow:0 10px 40px rgba(0,0,0,.25);white-space:nowrap">${w}</div>`);
      fit(n, 1000);
      rise(n, (c.hit ?? .15) + i * .18, 160);
    });
  },

  // 03 ui world — the creator lives inside a product UI: panel up top, video below, items drop in.
  uiWorld(c, p) {
    usePlate(p);
    el('<div class="abs" style="inset:0;background:#F4F2EC;z-index:0"></div>');
    const v = plateLayer('video', 'clip-path:inset(46% 0 0 0 round 40px 40px 0 0)', 2);
    const panel = el(`<div class="abs" style="left:50px;right:50px;top:200px;height:640px;border-radius:36px;background:#fff;box-shadow:0 30px 60px rgba(0,0,0,.12);z-index:6;padding:40px">
      <div class="meta" style="font-size:24px">${p.title || 'Workspace'}</div><div id="ui-slots" style="display:flex;gap:18px;margin-top:30px"></div></div>`);
    rise(panel, 0, 200);
    (p.items || ['Brief', 'Draft', 'Review', 'Approved']).forEach((t, i) => {
      const s = el(`<div style="flex:1;height:200px;border-radius:22px;background:#EEEAF8;display:grid;place-items:center;font:700 30px Inter">${t}</div>`, $('#ui-slots'));
      tl.fromTo(s, { y: -260, opacity: 0 }, { y: 0, opacity: 1, duration: .35, ease: 'back.out(1.6)', immediateRender: true }, (c.drop ?? .4) + i * .22);
      cue('slide', (c.drop ?? .4) + i * .22);
    });
  },

  // 04 frame break — the video sits in a window; the person spills out over its edge.
  frameBreak(c, p) {
    usePlate(p);
    paper();
    const win = plateLayer('video', 'clip-path:inset(18% 12% 22% 12% round 44px);', 2);
    plateLayer('subject', '', 10);
    const border = el('<div class="abs" style="left:130px;top:346px;width:820px;height:1152px;border-radius:44px;box-shadow:0 0 0 10px #fff, 0 30px 60px rgba(55,45,31,.3);z-index:3"></div>');
    tl.fromTo([win, border], { scale: 1.12 }, { scale: 1, duration: .5, ease: 'expo.out', immediateRender: true }, 0);
    cue('thump', 0);
  },

  // 05 digital zoom — fast eased punch on a word, the frame stays sharp (no pixel-snap judder).
  digitalZoom(c, p) {
    usePlate(p);
    const v = plateLayer('video', '', 1);
    tl.fromTo(v, { scale: p.from || 1 }, { scale: p.to || 1.45, duration: p.dur || .35, ease: 'expo.out', immediateRender: true }, c.hit ?? 0);
    if (p.back) tl.to(v, { scale: p.from || 1, duration: .4, ease }, c.end - .45);
    cue('whoosh', c.hit ?? 0);
  },

  // 06 phone mockup — a floating phone screen beside the person, steps advancing.
  phoneMockup(c, p) {
    usePlate(p);
    plateLayer('video', '', 1);
    const ph = el(`<div class="abs" style="left:560px;top:420px;width:400px;height:820px;border-radius:56px;background:#111;padding:14px;z-index:8;box-shadow:0 40px 60px rgba(0,0,0,.4);transform:rotate(6deg)">
      <div style="width:100%;height:100%;border-radius:44px;background:#F7F5F1;padding:60px 26px" id="ph"></div></div>`);
    rise(ph, 0, 500);
    (p.steps || ['Upload clip', 'Pick style', 'Export']).forEach((s, i) => {
      const r = el(`<div style="background:#fff;border-radius:18px;padding:22px;margin-bottom:16px;font:600 28px Inter;box-shadow:0 4px 10px rgba(0,0,0,.06)">${i + 1}. ${s}</div>`, $('#ph'));
      tl.from(r, { x: 60, opacity: 0, duration: .25 }, .4 + i * .3); cue('pop', .4 + i * .3);
    });
  },

  // 07 checklist — a glass panel that ticks itself off on the cues.
  checklist(c, p) {
    const items = p.items || ['Cut the dead air', 'Add the B-roll', 'Mix the sound'];
    const panel = el(`<div class="abs" style="left:70px;right:150px;top:220px;padding:30px 34px;border-radius:30px;background:rgba(20,20,24,.72);backdrop-filter:blur(18px);z-index:20">
      ${items.map((t, i) => `<div style="display:flex;gap:22px;align-items:center;margin:14px 0;font:600 36px Inter;color:#EDEAF5"><div class="ck" style="width:44px;height:44px;border-radius:50%;border:4px solid #8E89A0;display:grid;place-items:center;font-size:28px;color:#111"></div>${t}</div>`).join('')}</div>`);
    rise(panel, 0, 200);
    $$('.ck').forEach((k, i) => {
      const at = c['tick' + i] ?? (.5 + i * .5);
      tl.to(k, { backgroundColor: '#F5C518', borderColor: '#F5C518', duration: .12 }, at);
      tl.set(k, { textContent: '✓' }, at); cue('pen', at);
    });
  },

  // 08 headline wall — newspaper scraps pop onto the wall around the person (behind them).
  headlineWall(c, p) {
    usePlate(p);
    plateLayer('video', '', 1); plateLayer('subject', '', 10);
    const hs = p.headlines || ['Clients pay late, again', '94 days overdue', 'Agencies lose 20% to chasing', 'The awkward follow-up'];
    hs.forEach((h, i) => {
      const x = [60, 600, 80, 620, 330][i % 5], y = [230, 260, 520, 560, 380][i % 5];
      const n = el(`<div class="abs doc" style="left:${x}px;top:${y}px;width:400px;padding:22px 24px;transform:rotate(${i % 2 ? 4 : -5}deg);z-index:5">
        <div class="serif" style="font-size:40px;line-height:1.05">${h}</div><div style="height:2px;background:#16110D;margin:12px 0 8px"></div><div class="meta" style="font-size:16px">Page ${i + 2}</div></div>`);
      tl.fromTo(n, { scale: 1.6, opacity: 0 }, { scale: 1, opacity: 1, duration: .18, ease: 'power4.in', immediateRender: true }, (c.hit ?? .1) + i * .2);
      cue('paper_slap', (c.hit ?? .1) + i * .2 + .15);
    });
  },

  // 09 zoom-through cut — push into the frame with motion blur across a cut, land on the next shot.
  zoomThrough(c, p) {
    usePlate(p);
    const v = plateLayer('video', '', 1);
    const mid = c.cut ?? c.end / 2;
    tl.fromTo(v, { scale: 1, filter: 'blur(0px)' }, { scale: 2.6, filter: 'blur(14px)', duration: mid, ease: 'power3.in', immediateRender: true }, 0);
    tl.to(v, { scale: 1, filter: 'blur(0px)', duration: c.end - mid, ease: 'power3.out' }, mid);
    cue('whoosh2', Math.max(0, mid - .25));
  },

  // 10 chart grow — a line chart draws itself on the wall behind the person, with a label pill.
  chartGrow(c, p) {
    usePlate(p);
    plateLayer('video', '', 1); plateLayer('subject', '', 10);
    const pts = p.points || [5, 9, 8, 14, 19, 26, 40];
    const d = pts.map((v, i) => `${i ? 'L' : 'M'}${120 + i * 140} ${820 - v * 14}`).join(' ');
    const svg = el(`<svg class="abs" style="inset:0;z-index:5" viewBox="0 0 1080 1920" fill="none"><path d="${d}" stroke="#F5C518" stroke-width="16" stroke-linecap="round" stroke-linejoin="round" style="filter:drop-shadow(0 0 18px rgba(245,197,24,.7))"/></svg>`);
    const path = svg.querySelector('path'), L = path.getTotalLength();
    path.style.strokeDasharray = L; path.style.strokeDashoffset = L;
    tl.to(path, { strokeDashoffset: 0, duration: p.dur || 1.2, ease: 'power2.out' }, c.hit ?? .1); cue('marker', c.hit ?? .1);
    const pill = el(`<div class="abs head" style="left:${120 + (pts.length - 1) * 140 - 150}px;top:${820 - pts.at(-1) * 14 - 110}px;background:#F5C518;color:#111;padding:12px 22px;border-radius:999px;font-size:34px;letter-spacing:0;z-index:6">${p.label || 'SCALE ↗'}</div>`);
    tl.from(pill, { scale: 0, duration: .25, ease: 'back.out(3)' }, (c.hit ?? .1) + (p.dur || 1.2) - .1); cue('pop', (c.hit ?? .1) + (p.dur || 1.2));
  },

  // 11 pull-back reveal — full-frame video shrinks back into a card on a page, then the page reads.
  pullBack(c, p) {
    usePlate(p);
    el(`<div class="abs" style="inset:0;background:#F4F2EC;z-index:0"></div>`);
    const page = el(`<div class="abs" style="left:70px;right:70px;top:240px;z-index:1">
      <div class="head" style="font-size:150px;letter-spacing:-6px" id="pb-num">0</div><div class="meta" style="font-size:28px;margin-top:10px">${p.label || 'Hours saved this month'}</div></div>`);
    const v = plateLayer('video', 'border-radius:40px', 3);
    tl.fromTo(v, { scale: 1, x: 0, y: 0, borderRadius: 0 }, { scale: .55, x: 120, y: 330, borderRadius: 60, duration: .8, ease: 'expo.inOut', immediateRender: true }, c.hit ?? .2);
    cue('whoosh', c.hit ?? .2);
    const n = { v: 0 };
    tl.to(n, { v: p.to || 100, duration: .9, ease: 'power2.out', onUpdate: () => $('#pb-num').textContent = Math.round(n.v) + (p.suffix || '') }, (c.hit ?? .2) + .5);
  },

  // 12 green screen — the person keyed onto a designed background (gradient + headline + timer).
  greenScreen(c, p) {
    usePlate(p);
    el(`<div class="abs" style="inset:0;background:linear-gradient(160deg,#5B3DF5,#2A1B8F 60%,#140C4A);z-index:0"></div>`);
    const card = el(`<div class="abs doc" style="left:70px;right:70px;top:230px;padding:36px 40px;border-radius:30px;z-index:2">
      <div class="meta" style="font-size:22px">${p.kicker || 'Live'}</div><div class="head" style="font-size:84px;margin-top:10px" id="gs-t">${p.timer || '00:45'}</div>
      <div class="serif" style="font-size:52px;margin-top:6px">${p.text || 'Everything else waits.'}</div></div>`);
    rise(card, 0, 220);
    const s = plateLayer('subject', '', 10);
    tl.fromTo(s, { scale: p.scale || .78, y: 260 }, { y: 230, duration: c.end, ease: 'none', immediateRender: true }, 0);
  },

  // 13 paper cut — the person as a sticker (white border) on scribbled paper; ransom-note numbers.
  paperCut(c, p) {
    usePlate(p);
    paper();
    el(`<svg class="abs" style="inset:0;z-index:1" viewBox="0 0 1080 1920"><path d="M80 300 C 300 200, 500 420, 760 260 S 1000 420, 900 600" stroke="#7FA7E8" stroke-width="70" fill="none" opacity=".55" stroke-linecap="round"/><path d="M120 1250 C 380 1120, 700 1360, 980 1180" stroke="#F5C518" stroke-width="90" fill="none" opacity=".6" stroke-linecap="round"/></svg>`);
    const st = plateLayer('sticker', '', 8), s = plateLayer('subject', '', 9);
    tl.fromTo([st, s], { scale: .82, rotation: -2 }, { scale: .86, rotation: 1, duration: c.end, ease: 'none', immediateRender: true }, 0);
    const txt = (p.text || '100%').split('');
    txt.forEach((ch, i) => {
      const n = el(`<div class="abs" style="left:${80 + i * 130}px;top:240px;width:116px;height:150px;display:grid;place-items:center;background:${['#fff', '#16110D', '#E04329', '#F5C518'][i % 4]};color:${i % 4 === 1 ? '#fff' : '#16110D'};font:900 110px ${['Playfair Display', 'Arial Black', 'PT Serif', 'Special Elite'][i % 4]};transform:rotate(${(i % 2 ? 5 : -6)}deg);z-index:12;box-shadow:0 10px 18px rgba(55,45,31,.3)">${ch}</div>`);
      tl.fromTo(n, { scale: 2, opacity: 0 }, { scale: 1, opacity: 1, duration: .14, ease: 'power4.in', immediateRender: true }, (c.hit ?? .2) + i * .15);
      cue('paper_slap', (c.hit ?? .2) + i * .15 + .12);
    });
  },

  // 14 doodle boil — a hand-drawn outline round the person that wobbles at 10fps, doodles pop in.
  doodleBoil(c, p) {
    usePlate(p);
    plateLayer('video', 'filter:saturate(.85) brightness(.92)', 1);
    plateLayer('outline', '', 8);
    (p.doodles || ['★', '♥', '✎']).forEach((d, i) => {
      const n = el(`<div class="abs hand" style="left:${[90, 830, 140][i % 3]}px;top:${[420, 520, 1100][i % 3]}px;font-size:120px;color:#F7F5EE;z-index:9">${d}</div>`);
      tl.fromTo(n, { scale: 0, rotation: -20 }, { scale: 1, rotation: 0, duration: .2, ease: 'back.out(3)', immediateRender: true }, (c.hit ?? .3) + i * .3);
      tl.to(n, { rotation: 8, duration: .1, yoyo: true, repeat: Math.floor(c.end * 5), ease: 'steps(1)' }, (c.hit ?? .3) + i * .3 + .2);
      cue('pen', (c.hit ?? .3) + i * .3);
    });
  },

  // 15 vertigo — dolly zoom: the room rushes back while the person holds their size.
  vertigo(c, p) {
    usePlate(p);
    // One plate still contains the person, so the person layer must never be smaller than the background:
    // hold her at 1+k and let the room recede 1+k -> 1 (same origin), and the background copy stays hidden behind her.
    const o = 'transform-origin:50% 48%';
    const bg = plateLayer('video', o, 1), s = plateLayer('subject', o, 10);
    const k = p.amount || .3;
    tl.fromTo(bg, { scale: 1 + k }, { scale: 1, duration: c.end, ease: 'power1.inOut', immediateRender: true }, 0);
    gsap.set(s, { scale: 1 + k });
    cue('riser', 0);
  },

  // 16 cover story — a magazine masthead behind the person's head, cover lines in front.
  coverStory(c, p) {
    usePlate(p);
    plateLayer('video', '', 1); plateLayer('subject', '', 10);
    const mast = el(`<div class="abs serif" style="left:0;right:0;top:${p.y || 230}px;text-align:center;font-size:${p.size || 300}px;letter-spacing:.06em;color:#fff;z-index:5;line-height:1">${p.title || 'EDIT'}</div>`);
    tl.fromTo(mast, { letterSpacing: '.4em', opacity: 0 }, { letterSpacing: '.06em', opacity: 1, duration: .7, ease: 'expo.out', immediateRender: true }, c.hit ?? .1);
    (p.lines || ['The 30-minute reel', 'Inside the agency stack']).forEach((l, i) => {
      const n = el(`<div class="abs" style="left:70px;top:${(p.linesY || 960) + i * 80}px;font:800 44px Inter;color:#fff;z-index:12;text-shadow:0 4px 18px rgba(0,0,0,.5)">${l}</div>`);
      rise(n, (c.hit ?? .1) + .4 + i * .2, 120, 'typewriter');
    });
    cue('shutter', c.hit ?? .1);
  },

  // 17 glass type — giant frosted letters that blur and brighten the video behind them.
  glassType(c, p) {
    usePlate(p);
    plateLayer('video', '', 1);
    const word = p.text || 'DESIGN';
    const svg = encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='1080' height='420'><text x='540' y='330' text-anchor='middle' font-family='Arial Black' font-weight='900' font-size='${p.size || 250}' letter-spacing='-8'>${word}</text></svg>`);
    const g = el(`<div class="abs" style="left:0;top:${p.y || 640}px;width:1080px;height:420px;z-index:6;backdrop-filter:blur(16px) brightness(1.35) saturate(1.2);-webkit-mask:url(&quot;data:image/svg+xml,${svg}&quot;) center/100% 100% no-repeat"></div>`);
    const rim = el(`<div class="abs" style="left:0;top:${p.y || 640}px;width:1080px;height:420px;z-index:7;background:linear-gradient(180deg,rgba(255,255,255,.55),rgba(255,255,255,.05) 55%,rgba(255,255,255,.25));-webkit-mask:url(&quot;data:image/svg+xml,${svg}&quot;) center/100% 100% no-repeat;mix-blend-mode:screen"></div>`);
    tl.fromTo([g, rim], { y: 80, opacity: 0, scale: 1.08 }, { y: 0, opacity: 1, scale: 1, duration: .6, ease: 'expo.out', immediateRender: true }, c.hit ?? .1);
    cue('whoosh', c.hit ?? .1);
  },

  // Kinetic captions (wrapper): 1–4 word groups popping on each word, keywords in yellow and larger.
  // props.words: [{w, t, hl}] with t in scene-local seconds (build.py fills it from stt when "captions": true).
  captions(c, p) {
    const groups = [];
    (p.words || []).forEach(w => { const g = groups.at(-1); if (!g || g.length >= (p.per || 3) || w.t - g.at(-1).t > .6) groups.push([w]); else g.push(w); });
    groups.forEach((g, gi) => {
      const box = el(`<div class="abs" style="left:60px;right:150px;top:${p.y || 1180}px;text-align:center;z-index:30;opacity:0"></div>`);
      g.forEach(w => {
        const s = el(`<span style="display:inline-block;margin:0 10px;font:900 ${w.hl ? 96 : 62}px 'Arial Black',Inter;color:${w.hl ? '#F5C518' : '#fff'};text-shadow:0 6px 24px rgba(0,0,0,.55);letter-spacing:-1px">${w.w}</span>`, box);
        tl.fromTo(s, { scale: .6, opacity: 0 }, { scale: 1, opacity: 1, duration: .12, ease: 'back.out(3)', immediateRender: true }, w.t);
      });
      const end = groups[gi + 1] ? groups[gi + 1][0].t : c.end;
      tl.set(box, { opacity: 1 }, g[0].t); tl.set(box, { opacity: 0 }, end);
    });
  },

  // Numbered list tracker (wrapper): a corner list whose active item lights up on cues "item0".."itemN".
  listTracker(c, p) {
    const items = p.items || [];
    const box = el(`<div class="abs" style="left:50px;top:200px;padding:20px 26px;border-radius:24px;background:rgba(20,20,24,.6);backdrop-filter:blur(12px);z-index:25">
      ${items.map((t, i) => `<div class="lt" style="font:800 30px Inter;color:rgba(255,255,255,.55);margin:6px 0"><span style="font:700 20px Montserrat;margin-right:12px">${String(i + 1).padStart(2, '0')}</span>${t}</div>`).join('')}</div>`);
    rise(box, 0, 100, null);
    $$('.lt').forEach((n, i) => { if (c['item' + i] != null) { tl.to(n, { color: '#F5C518', scale: 1.06, transformOrigin: 'left center', duration: .12 }, c['item' + i]); if ($$('.lt')[i - 1]) tl.to($$('.lt')[i - 1], { color: 'rgba(255,255,255,.55)', scale: 1, duration: .12 }, c['item' + i]); } });
  },
});
