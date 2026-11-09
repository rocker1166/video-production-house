// Carousel engine (any brand). Usage: node kc.mjs <jobs|gen|sheet|render|pdf> <spec-slug> [--only a,b] [--variant <style>]
//   node kc.mjs variants            lists the available variants (styles.json)
// variant = the design: a per-run --variant beats slide.variant, which beats spec.variant (spec.style still works). A --variant run
// writes to <slug>~<variant> (art/, out/, pdf/) so one spec can live in every design side by side.
// Data lives in $CAROUSEL_HOME (default: this folder): specs/, art/, out/, pdf/, optional styles.json + brand.json.
// Spec: specs/<slug>.json = { slug, style, title, slides:[{ key, scene, pick, tone, kick, h, p, lab, sign, size, pg, top, phone:{src,off}, photo, style }] }
// Art goes to art/<slug>/<key>-a|b.png, finished slides to out/<slug>/slide-NN.png, PDF to pdf/<slug>.pdf.
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const H = dirname(fileURLToPath(import.meta.url)); // engine
const D = process.env.CAROUSEL_HOME ? resolve(process.env.CAROUSEL_HOME) : H; // brand data
const EDGE = createRequire(import.meta.url)("../engine/browser.cjs").binary(); // Edge / Chrome / Chromium on any OS
const GEN = `${H}/gen.mjs`;
const REF = "anchor.png"; // optional style anchor image in <data>/art/ (the approved look); styles with "useRef" use it when present
// CI and root containers cannot run Chrome's sandbox: set BROWSER_NO_SANDBOX=1 (done automatically for root on Linux)
const NOSB = process.env.BROWSER_NO_SANDBOX || (process.platform === "linux" && process.getuid?.() === 0) ? ["--no-sandbox", "--disable-dev-shm-usage"] : [];
const [cmd, slug, ...rest] = process.argv.slice(2);
const flag = (k) => (rest.includes(k) ? rest[rest.indexOf(k) + 1] : null);
const only = flag("--only")?.split(",") ?? null;
const V = flag("--variant");
const has = (p) => existsSync(p);
const styles = JSON.parse(readFileSync(has(`${D}/styles.json`) ? `${D}/styles.json` : `${H}/styles.json`, "utf8"));
const brand = has(`${D}/brand.json`) ? JSON.parse(readFileSync(`${D}/brand.json`, "utf8")) : {};
if (cmd === "variants") { for (const [k, v] of Object.entries(styles)) console.log(`${k.padEnd(12)} ${v.label}`); process.exit(0); }
if (V && !styles[V]) { console.error(`unknown variant "${V}". Options: ${Object.keys(styles).join(", ")}`); process.exit(1); }
const spec = JSON.parse(readFileSync(`${D}/specs/${slug}.json`, "utf8"));
const styleOf = (s) => V || s.variant || s.style || spec.variant || spec.style;
const tag = V ? `${slug}~${V}` : slug; // folder name under art/, out/, pdf/
const RULES = "STRICT RULES: portrait 4:5. The top 30 percent of the canvas is calm open space or soft negative space (no busy detail) so a headline can be placed there. Draw NO text, NO letters, NO numbers, NO logo, NO watermark, NO frame or border. Signs, papers, receipts and phone screens must be blank or show only abstract shapes, never words.";

if (cmd === "jobs") {
  const jobs = [];
  for (const s of spec.slides.filter((s) => s.scene && (!only || only.includes(s.key)))) {
    const st = styles[styleOf(s)];
    const prompt = ["ART DIRECTION: " + (st.useRef && has(`${D}/art/${REF}`) ? "Same style as Image 1 (technique, palette and mood only; do NOT reuse its composition or subjects). " : "") + st.prompt,
      (spec.subject || spec.place) ? "SUBJECT: " + (spec.subject || spec.place) : "", "SCENE: " + s.scene, RULES].filter(Boolean).join("\n\n");
    for (const seed of s.seeds || ["a"]) jobs.push({ name: `${s.key}-${seed}`, refs: st.useRef && has(`${D}/art/${REF}`) ? [REF] : [], prompt, aspect: "4:5" });
  }
  mkdirSync(`${D}/art/${tag}`, { recursive: true });
  writeFileSync(`${D}/art/${tag}/jobs.json`, JSON.stringify(jobs, null, 2));
  console.log(`${jobs.length} jobs -> art/${tag}/jobs.json (about $${(jobs.length * 0.13).toFixed(2)}; ask the owner first above $2)`);
} else if (cmd === "gen") {
  execFileSync("node", [GEN, `${D}/art/${tag}/jobs.json`, `${D}/art/${tag}`, "--model", "gemini-3-pro-image", "--size", "2K", ...(only ? ["--only", only.join(",")] : [])], { stdio: "inherit" });
} else if (cmd === "sheet") {
  const files = readdirSync(`${D}/art/${tag}`).filter((f) => f.endsWith(".png")).sort();
  const list = files.map((f) => `file '${D}/art/${tag}/${f}'\nduration 1`).join("\n");
  writeFileSync(`${D}/art/${tag}/.concat`, list);
  const out = `${D}/art/${tag}/_sheet.jpg`;
  execFileSync("ffmpeg", ["-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", `${D}/art/${tag}/.concat`, "-vf", `fps=1,scale=360:450,tile=${Math.min(files.length, 7)}x${Math.ceil(files.length / 7)}:padding=6:color=white`, "-frames:v", "1", out]);
  console.log(files.join("  ") + "\n" + out);
} else if (cmd === "render" || cmd === "pdf") {
  const abs = (p) => (p && !/^(file:|\/)/.test(p) ? `file://${D}/${p}` : p);
  const full = { slug: tag, brand: { ...brand, ...(spec.brand || {}) }, slides: spec.slides.map((s) => ({ ...s, img: s.photo ? abs(s.photo) : `file://${D}/art/${tag}/${s.key}-${s.pick || "a"}.png`, phone: s.phone && { ...s.phone, src: abs(s.phone.src) }, styleDef: styles[styleOf(s)] })) };
  const hash = encodeURIComponent(JSON.stringify(full));
  const out = `${D}/out/${tag}`;
  mkdirSync(out, { recursive: true });
  full.slides.forEach((_, i) => {
    const n = String(i + 1).padStart(2, "0");
    execFileSync(EDGE, [...NOSB, "--headless=new", "--disable-gpu", "--allow-file-access-from-files", "--hide-scrollbars", "--window-size=1080,1350", "--virtual-time-budget=3500", `--screenshot=${out}/slide-${n}.png`, `file://${H}/slide.html?s=${i + 1}#${hash}`], { stdio: "ignore" });
  });
  if (cmd === "pdf") {
    mkdirSync(`${D}/pdf`, { recursive: true });
    const imgs = full.slides.map((_, i) => `<img src="../out/${tag}/slide-${String(i + 1).padStart(2, "0")}.png">`).join("");
    writeFileSync(`${D}/pdf/_${tag}.html`, `<!doctype html><meta charset="utf-8"><style>@page{size:1080px 1350px;margin:0}*{margin:0}body{width:1080px}img{display:block;width:1080px;height:1350px;page-break-after:always}</style>${imgs}`);
    execFileSync(EDGE, [...NOSB, "--headless=new", "--disable-gpu", "--allow-file-access-from-files", "--no-pdf-header-footer", `--print-to-pdf=${D}/pdf/${tag}.pdf`, `file://${D}/pdf/_${tag}.html`], { stdio: "ignore" });
  }
  console.log(`rendered ${full.slides.length} slides -> out/${tag}/` + (cmd === "pdf" ? `, pdf/${tag}.pdf` : ""));
} else console.error("usage: node kc.mjs <jobs|gen|sheet|render|pdf> <slug> [--only key,key]");
