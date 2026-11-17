// Cross-platform browser + Playwright helpers shared by every renderer (macOS, Linux, Windows/WSL).
//   const { chromium, launch, binary } = require('.../engine/browser.cjs')
//   launch(): Playwright browser. Order: $BROWSER_CHANNEL, msedge, chrome, then Playwright's bundled chromium.
//   binary(): path of an installed Edge/Chrome/Chromium for plain `--headless --screenshot` use ($BROWSER or $EDGE wins).
//   gpuArgs(want): flags that make headless Chrome draw on the GPU. Headless draws in software (SwiftShader) by default.
//     A caller asks with launch({ gpu: true }) (engine/film.cjs does); it gets them on Linux with a GPU render node, not as root, not in CI.
//     BROWSER_GPU=1 gives them to every caller on any platform; BROWSER_GPU=0 refuses them to all. Chrome's own driver blocklist still applies.
//     GPU frames differ from software frames at antialiased edges: render one film in one mode, never mix.
const os = require('os'), fs = require('fs'), path = require('path');
const PW = path.join(os.homedir(), '.cache', 'reeltools', 'node_modules', 'playwright');
const chromium = () => require(PW).chromium;

const GPU_ARGS = ['--use-gl=angle', '--use-angle=gl-egl', '--enable-gpu-rasterization'];
function gpuArgs(want) {
  const v = process.env.BROWSER_GPU;
  if (v === '0') return [];
  if (v === '1') return GPU_ARGS;
  if (!want) return [];
  const root = process.getuid && process.getuid() === 0;
  const node = fs.existsSync('/dev/dri') && fs.readdirSync('/dev/dri').some((f) => f.startsWith('renderD'));
  return process.platform === 'linux' && node && !root && !process.env.CI && !process.env.BROWSER_NO_SANDBOX ? GPU_ARGS : [];
}

async function launch(opts = {}) {
  // `gpu` is our own option, not Playwright's. Caller flags come last, so a caller can still override a GPU flag.
  const { gpu: want, ...rest } = opts; opts = rest;
  const gpu = gpuArgs(want);
  if (gpu.length) opts = { ...opts, args: [...gpu, ...(opts.args || [])] };
  if (process.env.BROWSER_NO_SANDBOX || (process.platform === 'linux' && process.getuid && process.getuid() === 0)) opts = { ...opts, args: ['--no-sandbox', '--disable-dev-shm-usage', ...(opts.args || [])] };
  const tried = [];
  for (const channel of [process.env.BROWSER_CHANNEL, 'msedge', 'chrome', null].filter((c) => c !== undefined)) {
    try { return await chromium().launch(channel ? { channel, ...opts } : opts); }
    catch (e) { tried.push(`${channel || 'bundled chromium'}: ${String(e.message).split('\n')[0]}`); }
  }
  throw new Error('no browser could launch. Install Edge or Chrome, or run `npx playwright install chromium`.\n' + tried.join('\n'));
}

function binary() {
  const env = process.env.BROWSER || process.env.EDGE;
  if (env) return env;
  const win = ['PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'].map((k) => process.env[k]).filter(Boolean);
  const cands = {
    darwin: ['/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium'],
    linux: ['/usr/bin/microsoft-edge', '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/snap/bin/chromium'],
    win32: win.flatMap((b) => [path.join(b, 'Microsoft/Edge/Application/msedge.exe'), path.join(b, 'Google/Chrome/Application/chrome.exe')]),
  }[process.platform] || [];
  const hit = cands.find((p) => fs.existsSync(p));
  if (!hit) throw new Error('no Edge/Chrome/Chromium found; install one or set BROWSER=/path/to/binary');
  return hit;
}
module.exports = { PW, chromium, launch, binary, gpuArgs };
if (require.main === module) console.log(binary());
