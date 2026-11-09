// Generate images with the Gemini image API.
// Usage: node gen.mjs <jobs.json> <outDir> [--model gemini-3-pro-image] [--only name,name] [--size 2K]
// jobs.json: [{ "name": "hero-a", "prompt": "...", "refs": ["refs/logo-wordmark.png", ...] }]
// The API key is read from the env var GEMINI_API_KEY (or GOOGLE_GENERATIVE_AI_API_KEY), else from the repo's .env.
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { basename, extname, resolve, dirname } from "node:path";

const args = process.argv.slice(2);
const flag = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const [jobsFile, outDir] = args.filter((a, i) => !a.startsWith("--") && (i === 0 || !args[i - 1].startsWith("--")));
const model = flag("--model", "gemini-3-pro-image");
const only = flag("--only", "")?.split(",").filter(Boolean);
const size = flag("--size", "2K");
if (!jobsFile || !outDir) { console.error("usage: node gen.mjs jobs.json outDir"); process.exit(1); }

function apiKey() {
  const e = process.env.GEMINI_API_KEY || process.env.GOOGLE_GENERATIVE_AI_API_KEY;
  if (e) return e;
  const file = resolve(dirname(new URL(import.meta.url).pathname), "..", ".env");
  const m = existsSync(file) && readFileSync(file, "utf8").match(/^(?:GEMINI_API_KEY|GOOGLE_GENERATIVE_AI_API_KEY)=["']?([^"'\r\n]+)/m);
  if (!m) throw new Error("no GEMINI_API_KEY in the environment or .env");
  return m[1];
}
const KEY = apiKey();
const MIME = { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp" };

async function generate(job, base) {
  const parts = [];
  for (const ref of job.refs ?? []) {
    const p = resolve(base, ref);
    parts.push({ inlineData: { mimeType: MIME[extname(p).toLowerCase()], data: readFileSync(p).toString("base64") } });
  }
  parts.push({ text: job.prompt });
  const body = {
    contents: [{ role: "user", parts }],
    generationConfig: { responseModalities: ["IMAGE"], imageConfig: { aspectRatio: job.aspect ?? "16:9", imageSize: size } },
  };
  for (let attempt = 1; attempt <= 3; attempt++) {
    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${KEY}`, {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = json?.error?.message ?? res.statusText;
      if (res.status === 429 || res.status >= 500) { console.warn(`  ${job.name}: ${res.status} ${msg} (retry ${attempt})`); await new Promise(r => setTimeout(r, 8000 * attempt)); continue; }
      throw new Error(`${res.status} ${msg}`);
    }
    const img = json.candidates?.[0]?.content?.parts?.find(p => p.inlineData)?.inlineData;
    if (!img) {
      const why = json.candidates?.[0]?.finishReason ?? json.promptFeedback?.blockReason ?? JSON.stringify(json).slice(0, 300);
      if (attempt < 3) { console.warn(`  ${job.name}: no image (${why}) — retry ${attempt}`); continue; }
      throw new Error(`no image: ${why}`);
    }
    return Buffer.from(img.data, "base64");
  }
}

const base = dirname(resolve(jobsFile));
const jobs = JSON.parse(readFileSync(jobsFile, "utf8")).filter(j => !only?.length || only.includes(j.name));
mkdirSync(outDir, { recursive: true });
let ok = 0, fail = 0;
// ponytail: sequential on purpose — the image endpoint rate-limits bursts; parallelise if a batch ever exceeds ~20.
for (const job of jobs) {
  const out = resolve(outDir, `${job.name}.png`);
  if (existsSync(out) && !args.includes("--force")) { console.log(`skip ${job.name} (exists)`); continue; }
  const t = Date.now();
  try {
    const png = await generate(job, base);
    writeFileSync(out, png);
    writeFileSync(resolve(outDir, `${job.name}.prompt.txt`), `${model}\nrefs: ${(job.refs ?? []).join(", ")}\n\n${job.prompt}`);
    ok++; console.log(`ok   ${job.name}  ${(png.length / 1024).toFixed(0)}KB  ${((Date.now() - t) / 1000).toFixed(0)}s`);
  } catch (e) { fail++; console.error(`FAIL ${job.name}: ${e.message}`); }
}
console.log(`done: ${ok} ok, ${fail} failed -> ${outDir}`);
