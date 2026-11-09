// Demo invoice-chasing reel (2026-10-25): project-specific props + scenes.
// Loaded after base.html; uses its vocabulary (paper, rise, slam, stamp, stroke, draw, subject, fg, ring, cue, IMG).
window.LEDGER = [['12 Aug', 'Sharma Textiles', '85,000'], ['18 Aug', 'Bloom Café', '42,500'], ['02 Sep', 'Northwind Realty', '1,20,000'],
  ['09 Sep', 'Kavya Jewels', '28,000'], ['21 Sep', 'Urban Fit Gym', '36,000'], ['30 Sep', 'Pixel & Pine', '54,000']];
function invoiceDoc({ x = 170, y = 930, rot = -4, z = 20 } = {}) {
  return el(`<div class="abs doc" style="left:${x}px;top:${y}px;width:640px;padding:40px 48px;transform:rotate(${rot}deg);z-index:${z}">
    <div style="display:flex;justify-content:space-between;align-items:baseline"><div class="serif" style="font-size:62px">Invoice</div><div class="meta" style="font-size:20px">No. INV-0047</div></div>
    <div style="height:3px;background:var(--deep);margin:18px 0 22px"></div>
    <div class="pt" style="display:flex;justify-content:space-between;font-size:28px"><span>Billed to</span><b>Sharma Textiles</b></div>
    <div class="pt" style="display:flex;justify-content:space-between;font-size:28px;margin-top:10px"><span>Due</span><b>12 August</b></div>
    <div style="height:1px;background:rgba(22,17,13,.25);margin:22px 0"></div>
    <div style="display:flex;justify-content:space-between;align-items:baseline"><span class="meta" style="font-size:20px">Amount due</span><span class="head" style="font-size:78px;letter-spacing:-3px">₹85,000</span></div>
  </div>`);
}

// Faithful rebuild of Finance → Needs attention (demo-web NeedsAttentionList.tsx).
const INVOICES = [
  ['Sharma Textiles', 'INV-0047', 'Overdue by 94 days', '₹85,000', 'red'],
  ['Bloom Café', 'INV-0052', 'Overdue by 41 days', '₹42,500', 'red'],
  ['Northwind Realty', 'INV-0058', 'Overdue by 23 days', '₹1,20,000', 'red'],
  ['Kavya Jewels', 'INV-0061', 'Overdue by 9 days', '₹28,000', 'red'],
  ['Urban Fit Gym', 'INV-0064', 'Due in 3 days', '₹36,000', 'amber'],
];
function needsScreen(parent, { x = 40, y = 230, w = 880 } = {}) {
  return el(`<div class="abs screen" style="left:${x}px;top:${y}px;width:${w}px;padding:34px 26px;z-index:14">
    <div style="display:flex;justify-content:space-between;align-items:center;padding:0 10px 18px">
      <div style="font:600 36px Inter;color:#F2F0F7">Needs attention</div><div style="font:500 24px Inter;color:#9D98AB">All invoices →</div></div>
    ${[['⚠', 'Overdue', '4', '#FF8A80', 'odcount'], ['◷', 'Due in 7 days', '3', '#EDEAF5', ''], ['▤', 'Drafts not sent', '1', '#EDEAF5', '']].map(([i, l, v, col, id]) =>
      `<div ${id ? 'id="odrow"' : ''} style="display:flex;align-items:center;gap:20px;padding:12px 10px;border-radius:16px"><div style="width:50px;height:50px;border-radius:14px;background:#1D1D23;display:grid;place-items:center;color:${col};font-size:24px">${i}</div>
       <div style="flex:1;font:500 28px Inter;color:#C9C5D6">${l}</div><div ${id ? `id="${id}"` : ''} style="font:700 34px Inter;color:${col}">${v}</div></div>`).join('')}
    <div style="font:700 20px Montserrat;letter-spacing:.12em;color:#8E89A0;margin:22px 10px 8px;text-transform:uppercase">Chase first</div>
    ${INVOICES.map(([n, num, due, amt, tone], i) => `
      <div class="ds-row"><div class="ds-av">${n.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()}</div>
        <div style="flex:1;min-width:0;position:relative">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:16px">
            <span class="nm" style="font:500 35px Inter;color:#EDEAF5">${n}</span>
            <span class="amt" style="font:700 35px Inter;color:${tone === 'red' ? '#FF8A80' : '#EDEAF5'};position:relative">${amt}</span></div>
          <div style="margin-top:6px;font:500 29px Inter;color:#8E89A0;position:relative">${num} · <span class="od" style="position:relative;color:${tone === 'red' ? '#FF8A80' : '#FFCF70'}">${due}</span>
            ${i === 0 ? `<span id="tag0" style="margin-left:10px;font:700 19px Montserrat;letter-spacing:.08em;text-transform:uppercase;padding:6px 12px;border-radius:99px;color:#7EE0A6;background:rgba(60,200,120,.14);opacity:0">Reminded</span>` : ''}</div>
        </div></div>`).join('')}
  </div>`, parent);
}

// ---- scenes ----  (safe frame: x 0–930, y 180–1500; bottom 420 stays clear for captions)
Object.assign(SCENES, {
  hookTag(c) {
    const n = el(`<div class="abs doc" style="left:70px;top:210px;padding:18px 28px;transform:rotate(-2deg);z-index:20">
      <div class="head" style="font-size:46px;letter-spacing:-1px">Agency owners</div></div>`);
    const u = stroke('M95 300 C 260 288, 420 296, 560 286', { width: 10 });
    rise(n, 0, 200); draw(u, .35, .3);
    tl.to([n, u.parentNode], { opacity: 0, duration: .2 }, c.end - .2);
  },

  invoiceStamp(c) {
    const tag = el(`<div class="abs doc" style="left:70px;top:210px;padding:18px 28px;transform:rotate(-2deg);z-index:20">
      <div class="head" style="font-size:50px;letter-spacing:-1px">Agency owners</div></div>`);
    const u = stroke('M95 304 C 260 292, 420 300, 590 290', { width: 10 });
    tl.fromTo(tag, { scale: 1.25 }, { scale: 1, duration: .25, ease: 'back.out(2)', immediateRender: true }, 0);
    draw(u, .2, .3);
    const inv = invoiceDoc({ x: 200, y: 1090, rot: -4 });
    inv.style.transform += ' scale(.9)'; inv.style.transformOrigin = '0 0';
    const s = stamp(inv, 'UNPAID', 'var(--red)', { x: 150, y: 150, rot: -13, size: 96 });
    rise(inv, c.thing - .1, 520);
    slam(s, c.wrong - .1, inv);
  },

  calendar(c) {
    paper();
    const kick = el(`<div class="abs meta" style="left:70px;top:230px;font-size:30px;z-index:20">Days since the invoice went out</div>`);
    const num = el(`<div class="abs head" style="left:52px;top:270px;font-size:330px;letter-spacing:-14px;z-index:20"><span class="hl"><span class="bar"></span><span id="n">1</span></span></div>`);
    const cal = el(`<div class="abs doc" style="left:80px;top:690px;width:380px;height:440px;overflow:hidden;transform:rotate(-4deg);z-index:16">
      <div style="height:110px;background:var(--red)"></div>
      <div id="mo" class="head" style="position:absolute;top:24px;left:0;right:0;text-align:center;color:#fff;font-size:60px">AUG</div>
      <div id="dd" class="serif" style="position:absolute;top:150px;left:0;right:0;text-align:center;font-size:200px;line-height:1">12</div>
      <div id="st" class="meta" style="position:absolute;bottom:34px;left:0;right:0;text-align:center;font-size:22px">Invoice due</div></div>`);
    const her = subject(IMG.her_shock, { x: 470, y: 600, w: 470, side: 1 });
    fg(1180, 0);
    const status = el(`<div class="abs type" style="left:70px;top:1260px;font-size:44px;z-index:25;color:var(--deep)">STATUS: <span style="color:var(--red)">payment pending</span></div>`);
    rise(kick, 0, 120); rise(num, .05, 200); rise(cal, .1); rise(her, .25); rise(status, .3, 120);
    const counter = { v: 1 }, M = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
    tl.to(counter, { v: 94, duration: c.end - .9, ease: 'power2.in', onUpdate: () => {
      $('#n').textContent = Math.round(counter.v);
      const d = new Date(2026, 7, 12 + Math.round(counter.v) - 1);
      $('#mo').textContent = M[d.getMonth()]; $('#dd').textContent = d.getDate();
      $('#st').textContent = counter.v < 2 ? 'Invoice due' : 'Still unpaid';
    } }, .25);
    hl($('.bar', num), c.months - .1, .45);
    const r = stroke('M60 560 C 20 400, 120 300, 330 290 C 560 280, 640 400, 600 560 C 560 660, 140 660, 80 590', { width: 12 });
    draw(r, c.end - .65, .4);
    tl.fromTo(stage, { scale: 1 }, { scale: 1.05, duration: c.end, ease: 'none', transformOrigin: '50% 40%' }, 0);
  },

  sentNote(c) {
    const inv = invoiceDoc({ x: 200, y: 1090, rot: 3 });
    inv.style.transformOrigin = '0 0'; gsap.set(inv, { scale: .9 });
    const s = stamp(inv, 'SENT ✓', '#2E7D4F', { x: 210, y: 112, rot: -9, size: 84 });
    const note = el(`<div class="abs" style="left:640px;top:960px;width:280px;height:250px;background:var(--hl);transform:rotate(7deg);box-shadow:0 28px 26px var(--shadow);padding:30px 26px;z-index:22">
      <div class="hand" style="font-size:62px;line-height:1">Follow up<br>on Friday!</div></div>`);
    rise(inv, 0, 520);
    slam(s, c.sent - .1, inv);
    rise(note, c.forget - .75, 300);
    tl.to(note, { opacity: 0, filter: 'blur(16px)', scale: .82, duration: .45, ease: 'power1.in' }, c.forget + .05);
    tl.to(inv, { y: 500, opacity: 0, duration: .3, ease: 'power2.in' }, c.end - .3);
  },

  noSystem(c) {
    paper();
    const title = el(`<div class="abs head" style="left:70px;top:230px;font-size:112px;z-index:20"><span class="hl"><span class="bar"></span>Follow-up</span><br>system</div>`);
    const list = el(`<div class="abs doc" style="left:70px;top:520px;width:800px;padding:40px 46px;transform:rotate(-1.5deg);z-index:16">
      <div class="meta" style="font-size:22px;margin-bottom:10px">Accounts receivable · checklist</div>
      ${['Day 7 — gentle reminder', 'Day 15 — second nudge', 'Day 30 — call the client'].map(s =>
        `<div class="type" style="display:flex;gap:24px;align-items:center;margin:18px 0;font-size:42px;color:var(--deep)"><div style="width:46px;height:46px;border:4px solid var(--deep)"></div>${s}</div>`).join('')}
    </div>`);
    const strikes = [0, 1, 2].map(i => stroke(`M140 ${640 + i * 65} C 380 ${630 + i * 65}, 600 ${648 + i * 65}, 840 ${634 + i * 65}`, { width: 12 }));
    const nope = el(`<div class="abs hand" style="left:620px;top:900px;font-size:118px;color:var(--red);transform:rotate(-8deg);z-index:23">none.</div>`);
    const mail = el(`<div class="abs doc" style="left:90px;top:1030px;width:760px;padding:30px 36px;display:flex;gap:24px;align-items:center;z-index:18;transform:rotate(2deg)">
      <div style="width:76px;height:76px;background:var(--paper);display:grid;place-items:center;font-size:42px">✉</div>
      <div><div class="pt" style="font-size:42px;font-weight:700">Re: Invoice INV-0047</div><div class="pt" style="font-size:34px;color:#5A544A">Unread for 3 weeks</div></div></div>`);
    fg(1260, 0);
    const arch = stamp(stage, 'IGNORED', 'var(--red)', { x: 500, y: 1000, rot: -8, size: 70 }); arch.style.zIndex = 26;
    rise(title, 0, 160); hl($('.bar', title), .2); rise(list, .1);
    strikes.forEach((p, i) => draw(p, c.no - .1 + i * .13, .14));
    tl.from(nope, { scale: 0, rotation: -30, duration: .22, ease: 'back.out(3)' }, c.no + .3);
    rise(mail, c.clients - .3, 300);
    slam(arch, c.forget, mail);
  },

  chat(c) {
    paper();
    const phone = el(`<div class="abs" style="left:60px;top:240px;width:620px;height:1200px;border-radius:64px;background:#111;padding:16px;z-index:14;transform:rotate(-2deg);box-shadow:0 40px 50px rgba(55,45,31,.38)">
      <div style="width:100%;height:100%;border-radius:50px;overflow:hidden;position:relative;background:#EFE7DD">
        <div style="height:150px;background:#F7F5F1;display:flex;align-items:flex-end;padding:0 30px 20px;gap:18px">
          <div style="width:74px;height:74px;border-radius:50%;background:#B8A88E;display:grid;place-items:center;font:700 32px Inter;color:#fff">R</div>
          <div><div style="font:700 32px Inter">Rahul · Sharma Textiles</div><div style="font:500 22px Inter;color:#7A7468">last seen today</div></div></div>
        <div id="msgs" style="position:absolute;left:0;right:0;top:150px;bottom:120px"></div>
        <div style="position:absolute;left:18px;right:18px;bottom:22px;height:90px;border-radius:45px;background:#fff;display:flex;align-items:center;padding:0 32px;font-size:30px">
          <span id="typed" class="hi" style="font-weight:500"></span><span style="width:3px;height:38px;background:#3A9BDC;margin-left:3px"></span></div>
      </div></div>`);
    const msgs = $('#msgs');
    [['12 Aug', 'Hi Rahul, July invoice attached 📎 ₹85,000', 30], ['28 Aug', 'Gentle reminder on the invoice 🙏', 250], ['10 Sep', 'Hi, any update on the payment?', 430]]
      .forEach(([d, m, y], i) => {
        const chip = el(`<div class="abs" style="left:50%;transform:translateX(-50%);top:${y}px;background:rgba(255,255,255,.85);border-radius:12px;padding:6px 16px;font:600 19px Inter;color:#556">${d}</div>`, msgs);
        const b = el(`<div class="bubble" style="right:26px;top:${y + 50}px;max-width:470px">${m}<div class="m">10:4${i} am <span class="tick">✓✓</span></div></div>`, msgs);
        const at = Math.max(.05, c.message - .3) + i * .38; cue('send', at);
        tl.fromTo([chip, b], { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: .22, ease: 'back.out(2)', immediateRender: true }, at);
      });
    const fc = el(`<div class="abs" style="left:50%;transform:translateX(-50%);top:650px;background:rgba(255,255,255,.85);border-radius:12px;padding:6px 16px;font:600 19px Inter;color:#556;opacity:0">26 Sep · 11:02 pm</div>`, msgs);
    const fin = el(`<div class="bubble hi" style="right:26px;top:700px;max-width:520px;font-size:38px;font-weight:600;opacity:0">भैया payment का क्या हुआ? 🙏<div class="m">Seen · no reply <span class="tick">✓✓</span></div></div>`, msgs);
    const her = subject(IMG.her_ask, { x: 560, y: 720, w: 430, side: 1 });
    fg(1230, 0);
    const cap = el(`<div class="abs type" style="left:70px;top:1310px;font-size:46px;z-index:25;color:var(--deep)">Follow-up #4. <span style="color:var(--red)">Still waiting.</span></div>`);
    rise(phone, 0, 300); rise(her, .2); rise(cap, .3, 100);
    const text = 'भैया payment का क्या हुआ?', typed = { n: 0 };
    cue('typing', c.bhaiya - .15); cue('send', c.asked + .05);
    tl.to(typed, { n: text.length, duration: c.asked - c.bhaiya, ease: 'none', onUpdate: () => { $('#typed').textContent = text.slice(0, Math.round(typed.n)); } }, c.bhaiya - .15);
    tl.set('#typed', { textContent: '' }, c.asked + .05);
    tl.fromTo([fc, fin], { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: .2, ease: 'back.out(2)' }, c.asked + .05);
    tl.fromTo(stage, { scale: 1 }, { scale: 1.12, duration: c.end, ease: 'power1.in', transformOrigin: '35% 50%' }, 0);
  },

  demoIntro(c) {
    paper();
    const logo = el(`<img class="abs" src="${IMG.demo_ink}" style="left:140px;top:640px;width:800px;z-index:20">`);
    const u = stroke('M150 860 C 380 842, 640 850, 930 836', { width: 14 });
    rise(logo, 0, 260); draw(u, .3, .35);
  },

  needs(c) {
    paper();
    const kick = el(`<div class="abs meta" style="left:44px;top:190px;font-size:26px;z-index:20">Demo · Finance</div>`);
    const scr = needsScreen(stage);
    const rows = $$('.ds-row');
    const odRings = $$('.od').slice(0, 4).map((n, i) => ring(n, c.days - .1 + i * .18));
    $$('.amt').slice(0, 4).forEach((n, i) => ring(n, c.howmuch + .05 + i * .14, { round: 999, pad: 12 }));
    fg(1330, 0);
    const cap = el(`<div class="abs type" style="left:70px;top:1400px;font-size:44px;z-index:25;color:var(--deep)">One screen. Every unpaid invoice.</div>`);
    rise(scr, 0, 420); rise(kick, 0, 100); rise(cap, .2, 100);
    tl.from(rows, { y: 30, opacity: 0, duration: .3, stagger: .06, ease: 'power2.out' }, .25);
    // who → spotlight the client names (other rows dim, nothing pans out of frame)
    $$('.nm').slice(0, 4).forEach((n, i) => tl.fromTo(n, { color: '#EDEAF5' }, { color: '#F5C518', duration: .14, yoyo: true, repeat: 1 }, c.which + i * .2));
    tl.to(rows.slice(4), { opacity: .35, duration: .2 }, c.which);
    tl.to(odRings, { opacity: 0, duration: .2 }, c.howmuch - .3);
    tl.fromTo('#odcount', { scale: 1 }, { scale: 1.45, duration: .2, yoyo: true, repeat: 1 }, c.since + .1);
    tl.fromTo('#odrow', { backgroundColor: 'rgba(245,197,24,0)' }, { backgroundColor: 'rgba(245,197,24,.16)', duration: .2 }, c.since);
  },

  strike(c) {
    paper();
    const lines = ['Gentle reminder on the invoice 🙏', 'Hi, any update on the payment?', 'भैया payment का क्या हुआ? 🙏'];
    const nodes = lines.map((m, i) => el(`<div class="bubble hi" style="left:${70 + i * 18}px;top:${300 + i * 190}px;font-size:40px;font-weight:600;z-index:16;transform:rotate(${i % 2 ? 2 : -2}deg)">${m}</div>`));
    const strikes = nodes.map((n, i) => stroke(`M${50 + i * 18} ${360 + i * 190} C 300 ${340 + i * 190}, 520 ${380 + i * 190}, ${720 + i * 10} ${350 + i * 190}`, { width: 16 }));
    const her = subject(IMG.her_finger, { x: 560, y: 760, w: 420, side: 1 });
    fg(1280, 0);
    const done = el(`<div class="abs head" style="left:70px;top:1340px;font-size:62px;z-index:26"><span class="hl"><span class="bar"></span>Manual follow-ups: 0</span></div>`);
    nodes.forEach((n, i) => rise(n, i * .07, 260)); rise(her, .15);
    strikes.forEach((p, i) => draw(p, c.over - .5 + i * .15, .15));
    rise(done, c.over - .05, 120); hl($('.bar', done), c.over + .15, .3);
  },

  remind(c) {
    paper();
    needsScreen(stage);
    const row0 = $('.ds-row');
    row0.style.background = 'rgba(255,255,255,.06)';
    row0.style.paddingBottom = '74px';
    el(`<div class="abs" style="right:28px;bottom:18px;display:flex;gap:26px;font:700 30px Inter"><span id="remindBtn" style="color:#C9C5D6">Remind</span><span style="color:#D0BCFF">Record payment</span></div>`, row0);
    fg(1330, 0);
    const dim = el(`<div class="abs" style="left:40px;top:230px;width:880px;height:1080px;border-radius:34px;background:rgba(10,10,12,.6);opacity:0;z-index:30"></div>`);
    const dlg = el(`<div class="abs screen" style="left:60px;top:560px;width:840px;padding:52px;background:#17181B;opacity:0;z-index:31">
      <div style="font:700 50px Inter;color:#F2F0F7">Send a reminder?</div>
      <div style="font:400 38px/1.35 Inter;color:#B4AFC2;margin-top:18px">This emails Sharma Textiles about the overdue balance.</div>
      <div style="display:flex;justify-content:flex-end;gap:20px;margin-top:44px"><div style="font:600 34px Inter;color:#C9C5D6;padding:22px 30px">Cancel</div><div id="sendBtn" class="btn-grad" style="font-size:34px">Send reminder</div></div></div>`);
    const toast = el(`<div class="abs" style="left:60px;width:820px;top:1360px;background:#1B1C20;border-radius:28px;padding:30px 34px;display:flex;gap:22px;align-items:center;box-shadow:0 30px 50px rgba(55,45,31,.4);opacity:0;z-index:40">
      <div style="width:60px;height:60px;border-radius:50%;background:#2E9C5A;display:grid;place-items:center;color:#fff;font:800 34px Inter;flex:none">✓</div>
      <div style="font:600 36px Inter;color:#F2F0F7">Reminder emailed to Sharma Textiles</div></div>`);
    const cur = el(`<svg class="cursor" viewBox="0 0 24 24" style="left:780px;top:1150px"><path d="M4 2 L4 20 L9 15.5 L12.5 22 L15.5 20.6 L12.2 14.3 L19 14 Z" fill="#fff" stroke="#111" stroke-width="1.4" stroke-linejoin="round"/></svg>`);
    const r = $('#remindBtn').getBoundingClientRect(), sb = $('#sendBtn').getBoundingClientRect();
    cue('click', c.click); cue('click', c.reminder - .1); cue('ding', c.reminder + .08);
    tl.to(cur, { left: r.left + r.width * .4, top: r.top + r.height * .3, duration: Math.max(.2, c.click - .05), ease: 'power2.inOut' }, 0);
    tl.to(cur, { scale: .8, duration: .06, yoyo: true, repeat: 1 }, c.click);
    tl.to('#remindBtn', { color: '#FFFFFF', duration: .04 }, c.click);
    // state changes are near-cuts (2 frames): a slow crossfade reads as ghosted, doubled UI
    tl.to([dim, dlg], { opacity: 1, duration: .06 }, c.click + .06);
    tl.fromTo(dlg, { scale: .94 }, { scale: 1, duration: .16, ease: 'back.out(2)' }, c.click + .06);
    tl.to(cur, { left: sb.left + sb.width * .45, top: sb.top + sb.height * .45, duration: .26, ease: 'power2.inOut' }, c.click + .12);
    tl.to(cur, { scale: .8, duration: .06, yoyo: true, repeat: 1 }, c.reminder - .1);
    tl.to('#sendBtn', { scale: .95, duration: .06, yoyo: true, repeat: 1 }, c.reminder - .1);
    tl.to([dim, dlg, cur], { opacity: 0, duration: .06 }, c.reminder);
    tl.fromTo(toast, { opacity: 0, y: 80 }, { opacity: 1, y: 0, duration: .25, ease: 'back.out(2)' }, c.reminder + .08);
    tl.to('#tag0', { opacity: 1, duration: .15 }, c.reminder + .2);
  },

  // "या जानबूझकर टाल देते हैं" — small overlay over the A-roll
  seen(c) {
    const card = el(`<div class="abs doc" style="left:70px;top:1080px;padding:26px 32px;border-radius:22px;transform:rotate(-3deg);z-index:20;display:flex;gap:20px;align-items:center">
      <div style="width:70px;height:70px;border-radius:50%;background:#B8A88E;display:grid;place-items:center;font:700 32px Inter;color:#fff">R</div>
      <div><div style="font:700 36px Inter">Rahul · Sharma Textiles</div><div style="font:600 32px Inter;color:#3A9BDC">✓✓ Seen 11:02 pm</div></div></div>`);
    const s = stamp(stage, 'NO REPLY', 'var(--red)', { x: 430, y: 1210, rot: -9, size: 66 }); s.style.zIndex = 22;
    rise(card, 0, 360);
    slam(s, c.dodge - .1, card);
  },

  // "बिना तुम्हारे awkward feel किए" — callback to the bubble, now sent by the system
  noAwkward(c) {
    const b = el(`<div class="bubble hi" style="left:110px;top:1110px;font-size:42px;font-weight:600;z-index:16;transform:rotate(-2deg)">भैया payment का क्या हुआ? 🙏</div>`);
    const p = stroke('M90 1170 C 330 1150, 600 1185, 860 1160', { width: 16 });
    const tag = el(`<div class="abs doc" style="left:300px;top:1250px;padding:16px 26px;transform:rotate(3deg);z-index:24"><div class="head" style="font-size:40px;letter-spacing:-1px">Auto-reminder sent ✓</div></div>`);
    rise(b, 0, 300);
    draw(p, c.awk - .25, .2);
    rise(tag, c.awk + .05, 160);
  },

  paid(c) {
    const inv = invoiceDoc({ x: 200, y: 1090, rot: -4 });
    inv.style.transformOrigin = '0 0'; gsap.set(inv, { scale: .9 });
    const old = stamp(inv, 'UNPAID', 'var(--red)', { x: 130, y: 120, rot: -13, size: 96 }); old.style.opacity = .93;
    const s = stamp(inv, 'PAID', '#2E7D4F', { x: 190, y: 160, rot: -6, size: 130 });
    rise(inv, 0, 520);
    tl.to(old, { opacity: .15, duration: .1 }, c.easy - .02);
    slam(s, c.easy - .12, inv);
  },

  endCard(c) {
    paper(true);
    const her = subject(IMG.her_smile, { x: 600, y: 760, w: 400, side: 1 });
    const logo = el(`<img class="abs" src="${IMG.demo_ink}" style="left:70px;top:250px;width:560px;z-index:20">`);
    const line = el(`<div class="abs head" style="left:70px;top:420px;font-size:84px;z-index:20">Stop<br>chasing.<br><span class="hl"><span class="bar"></span>Let it</span><br><span class="hl"><span class="bar"></span>follow up.</span></div>`);
    fg(1250, 0);
    const url = el(`<div class="abs type" style="left:70px;top:1330px;font-size:54px;z-index:25;color:var(--deep)">demo.com</div>`);
    const u = stroke('M70 1405 C 200 1398, 330 1402, 400 1396', { width: 10, z: 26 });
    rise(logo, 0, 200); rise(line, .12, 260); rise(her, .2);
    $$('.bar', line).forEach((b, i) => hl(b, .55 + i * .2));
    rise(url, .5, 120); draw(u, .9, .3);
  },
});
