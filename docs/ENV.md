# Machine traps for rendering (read only when a render misbehaves)

Collected from real runs, 2026-11-09.

## Headless frame rendering (reel pipeline, 2026-10-26)
- Playwright Chromium download stalls on this Mac; use `chromium.launch({ channel: 'msedge' })` (Edge is installed), Playwright >=1.55.
- Open the CDP session AFTER `page.goto(file://...)` — a file:// navigation swaps renderer and silently detaches an earlier session (every send hangs).
- `page.evaluate(() => fn())` hangs if fn returns a GSAP timeline (serialises the object graph) — return undefined.
- Edge `browser.close()` can hang after long runs — `process.exit(0)` after frames are written.
- ffmpeg overlay of a PNG sequence mixing rgb24/rgba frames: add `-reinit_filter 0` on that input, or the graph reinitialises mid-stream, drops frames and can deadlock the audio mix.
- CSS mask-image refuses file:// images — inline as data URIs.
- Webfonts load only on first use: `document.fonts.load()` every face before frame 0.
- VidCap MCP: each VidCap page keeps its OWN Groq key + projects (per browser, incl. the Claude app's browser pane). With several pages open, commands go to the last-focused one (v0.1.1+) — check `openTabs` and which page holds the key before transcribing. Per-line `y` is ignored (one global box), so pick one height that clears the graphics. `hormozi` = the bold yellow karaoke look; the template search misses it.
- ffmpeg `adelay` is silently ignored when the input is AAC/mp4 inside a filter graph (clip ends up short): decode to WAV first (a mix script should do this).
- Playwright/Edge frame rendering of heavy HTML pages: several parallel workers were ~30x slower than one on this Mac (313s vs 10s per 40 frames). Use 1; time before raising.
- Playwright chromium-1140 and puppeteer Chrome for Testing die silently on this Mac (exit 137); use `channel: 'msedge'`.
