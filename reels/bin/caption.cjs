// Renders each caption in a spec to a transparent 1080x1920 PNG (Hindi + English, shaped by Edge).
//   node caption.cjs <spec.json> <outDir>   → <outDir>/cap0.png, cap1.png, …
const { launch } = require('../../engine/browser.cjs');
const fs = require('fs');
const path = require('path');

const [specPath, outDir] = process.argv.slice(2);
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const styles = JSON.parse(fs.readFileSync(path.join(process.env.REEL_HOME || path.join(__dirname, '..'), 'style.json'), 'utf8'));
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');

function css(s) {
  const p = s.pos || {};
  const pos = p.top != null ? `top:${p.top}px` : p.bottom != null ? `bottom:${p.bottom}px` : 'top:50%;transform:translate(-50%,-50%)';
  // pos.left pins the caption to the left edge (the itinerary "DAY 1" tag); otherwise it is centred.
  const x = p.left != null ? `left:${p.left}px;text-align:left;` : `left:50%;text-align:center;${p.top != null || p.bottom != null ? 'transform:translateX(-50%);' : ''}`;
  return `position:absolute;${x}${pos};width:max-content;max-width:${s.maxWidth || 900}px;text-wrap:balance;` +
    `font-family:${s.font};font-weight:${s.weight};font-size:${s.size}px;color:${s.color};line-height:${s.lineHeight || 1.25};` +
    `${s.upper ? 'text-transform:uppercase;' : ''}${s.italic ? 'font-style:italic;' : ''}${s.spacing ? `letter-spacing:${s.spacing};` : ''}` +
    `${s.shadow ? `text-shadow:${s.shadow};` : ''}` +
    `${s.pill ? `background:${s.pill.bg};padding:${s.pill.pad};border-radius:${s.pill.radius}px;` : ''}`;
}

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const html = path.join(outDir, 'cap.html');
  fs.writeFileSync(html, `<!doctype html><meta charset="utf-8"><link href="file://${path.join(__dirname, 'fonts', 'fonts.css')}" rel="stylesheet">` +
    `<link href="file://${path.join(__dirname, 'fonts', 'extra.css')}" rel="stylesheet">` +
    '<style>html,body{margin:0;width:1080px;height:1920px;background:transparent;overflow:hidden}</style><div id="t"></div>');
  const browser = await launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + html);
  for (const [i, c] of (spec.captions || []).entries()) {
    const s = styles[c.style || 'main'];
    if (!s) throw new Error(`caption ${i}: unknown style "${c.style}" (style.json has ${Object.keys(styles).filter(k => k[0] !== '_')})`);
    await page.evaluate(([h, st]) => { const t = document.getElementById('t'); t.innerHTML = h; t.style.cssText = st; }, [esc(c.text), css(s)]);
    // Web fonts load on first use: wait for this text's faces or the first caption renders in a fallback font.
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(outDir, `cap${i}.png`), omitBackground: true });
  }
  await browser.close();
})();
