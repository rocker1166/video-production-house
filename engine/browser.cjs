// Cross-platform browser + Playwright helpers shared by every renderer (macOS, Linux, Windows/WSL).
//   const { chromium, launch, binary } = require('.../engine/browser.cjs')
//   launch(): Playwright browser. Order: $BROWSER_CHANNEL, msedge, chrome, then Playwright's bundled chromium.
//   binary(): path of an installed Edge/Chrome/Chromium for plain `--headless --screenshot` use ($BROWSER or $EDGE wins).
const os = require('os'), fs = require('fs'), path = require('path');
const PW = path.join(os.homedir(), '.cache', 'reeltools', 'node_modules', 'playwright');
const chromium = () => require(PW).chromium;

async function launch(opts = {}) {
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
module.exports = { PW, chromium, launch, binary };
if (require.main === module) console.log(binary());
