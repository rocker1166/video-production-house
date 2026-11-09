# Video editing — learnings log (engine · effects · styles)

Read before every run. Append after every run (newest last). Repeats become rules in SKILL.md or fixes in scripts/.

## 2026-10-25 · Demo invoice-chasing UGC (63s Hinglish → 49.6s) · ~2h wall clock

**Where the time went**
- About 75 minutes went on tooling, all of it now fixed in scripts and doctor.sh:
  - Playwright Chromium download stalled → use Edge (`channel: 'msedge'`).
  - The renderer hung twice: once on a CDP session opened before goto, once on `seek()` returning a GSAP timeline.
  - The ffmpeg overlay deadlocked on mixed rgb24/rgba PNGs → `-reinit_filter 0` + one continuous graphics track.
  - Webfonts were blank in scene 1 → preload every face.
  - CSS masks refuse file:// → data-URI `assets.js`.
  - Edge `close()` hung → `process.exit`.
- About 30 minutes went on serial render/compose cycles → now 6 workers + parallel aroll, ~2 minutes per full render.
- About 15 minutes went on ElevenLabs concurrency (max 4 on this plan) and the music API being paid-only → SFX + music are cached in `assets/`.

**User corrections, now rules**
1. Lips drifted off the voice: per-segment frame rounding. → CFR mezzanine + frame-snapped cuts (build.py).
2. "Video stucks": zoompan judder, overlay framesync stalls, static graphic holds. → static punch-ins, one track, auto camera drift, freezedetect gate.
3. Disliked the creator's expression (eyes half-closed). → pick from faces sheets, eyes-open only, look full-size.
4. The bottom area felt blank. → ledger-paper `fg()` band, low contrast (captions go on top).
5. Wanted Vox SFX depth. → animation-logged foley (`cue()`), room tone, paper/typewriter/stamp/pen takes.

**Independent reviewer caught (the gates didn't)**
- A pan cropped the product UI's amounts off-frame → never pan product screens.
- Ghosted, doubled dialog/toast from slow crossfades → near-cut state changes.
- 8-frame A-roll flashes between graphics → `scene_windows()` closes gaps under 0.35s.
- Invoice prop covering her mouth → overlays at y ≥ 1060.
- Calendar dates didn't match the day counter.
- A 38–47s talking-head stretch with no graphic → no A-roll stretch over ~4s without an overlay.

**Next run should**: hit the 30-min budget. If a step overruns by 2x, note why here.

## 2026-10-26 · Skill verification: rebuilt the Demo reel from scratch through the scripts
- Machine time end to end: ingest 40s, cut-outs 5s, stills 6s, aroll 32s ∥ render 67s, compose + gates 28s. All 4 gates PASS.
- Render was 228s with 6 pages in one Edge: no faster than one page, because they share the compositor. → one Edge per worker.
  Six Edges at once then timed out fetching Google Fonts/GSAP → vendored into `engine/vendor/` (offline, 1.1 MB).
- A re-run STT gives slightly different word timings (speech 47.07s vs 47.03s), so plan cue times are fine as-is (±1 frame).

## 2026-10-26 · Effects library from a reference reel (17 named effects + captions + list tracker)
- The reference was downloaded with yt-dlp (venv at ~/.cache/reeltools/ytenv) into `<project>/ugc/ref/`, for analysis only; never republish it.
  Read it with 4fps contact sheets, then 8fps crops of the demo region. Its labels name the techniques.
- Built as original scenes in `effects/fx.js`. Most need the person separated → `matte.swift` (Vision person segmentation,
  sequence handler for temporal stability) + `build.py plates`. All compositing happens in the HTML canvas, so transforms are sub-pixel smooth.
- Bugs hit: an infinite lavfi colour source in alphamerge wrote 276k PNGs before the kill (fixed: one finite stream + `-frames:v`).
  Vertigo doubled her head (fixed: subject scale ≥ background scale). Captions collided with cover-story lines (fixed: `linesY`).
- Timing: matte 72s, plates 43s, render 159s (plate scenes load 2 images per frame, ~3x a plain scene), compose 30s.
- Gallery: `fx-gallery.mp4` = every effect on the Demo A-roll with captions + tracker; the gates PASS except the deliberate 0.5s tail hold.

## 2026-10-26 · Restructured into parent `video-editing` (engine · effects · styles)
- `vox-editing` is now a thin child (style = vox). `/video-edit` picks the style and effects; `/vox-edit` forces vox.
- Effect choice lives in `effects/EFFECTS.md` (beat type → effect, budget ≤1 plate effect per ~5s, no repeats).
- Verified: doctor READY after the move (venv rebuilt at the new path); the Demo vox plan + a vertigo effect + a captions layer render through the new layout.

## 2026-11-06 · Cross-skill lessons from the Travel-app intro series (series 020-025)
- HTML-seek rendering (page `seek(frame)` + Edge CDP frames + ffmpeg) beats overlay-on-footage when the reel is type/cards/app screens: no per-effect plumbing, blend modes and clip-paths for free. Reference implementation: `reel-funnel/bin/hr_render.cjs`, `hr_build.sh`, `mix.py`, `cues.py`.
- Parallel Edge workers measured 30x SLOWER than one on heavy pages here (313s vs 10s per 40 frames); the `--workers 6` default in `engine/render.cjs` was tuned for light scenes: time a 40-frame range before trusting it.
- ffmpeg: `adelay` is ignored on AAC/mp4 inputs in a filter graph; decode clips to WAV (trimmed with -ss/-t) first. loudnorm can return a slightly different length: pad/trim after it.
- Sync to HITS (a >=9 dB jump in 60 ms) and gaps, not to aubio's beat grid: the grid sat half a beat off a strings intro, and a ref's cuts were 29% on-grid (= chance).
- Never judge a reel from a sparse contact sheet: spelling, clipped words and font glyph bugs only show at full size. Gate it (caption script + full-size frame per caption).
- Repetition is the failure mode of generated motion: plan one idea + one motion per beat, reject plans where two beats share a motion, vary the motion between words.

## 2026-11-07 · Studio teaser + reusable logo motion (HTML-seek, 20.5s vertical, no footage)
- Wall clock well over the 30-min budget, because the brief changed three times mid-run (Travel-app out, Client out, new client in) and logo geometry came first. Machine time was small: full 615-frame render 34s on one Edge, encode + gates under 1 min.
- Best idea to reuse: build the logo motion FIRST as one animated SVG (CSS keyframes, seeked with document.getAnimations()), then make the film's climax that same file on its own clock. One source, every ratio and transparent export comes from it, and the logo earns its meaning (six dots = six things shipped).
- CSS trap: a global `*{animation-fill-mode:both}` loses to any `animation:` shorthand on an id selector; put `both` in each shorthand.
- GSAP scale on nested SVG circles shifted them off position. Set the `r` attribute in seek() instead. Child `visibility:visible` also punches through a hidden parent scene: use opacity.
- A single-frame hr_render call costs ~20s (two Edge launches + decode). Never loop it for samples: a full render is 34s.
- Per-frame film grain made a 20s file 164 MB and would block up after social re-encoding. Opacity .026, new grain every 3 frames, crf 18 + maxrate 18M: 35 MB.
- Reviewer caught what gates can't: dead frames before the key beat, three beats sharing one layout, a number held too briefly, a screen with a name to check. Reviewer got wrong: font sizes judged off 216px sheets (said 24px, real 52px). Tell it to measure on full-size frames, and verify before fixing.
- earshot critique's "music presence" flag fires on sparse vocal-chop sections. Check the song is really playing before treating it as critical.
- Check every third-party source for words the client bans: the client site's hero names companies Studio must not show, so it is cropped. Footers on public sites carry personal phone numbers: stop screenshots above them.

## 2026-11-07 · Studio teaser v3: suspense cut, VO-led, ElevenLabs voice + score + SFX
- Retiming a finished HTML film to a voice took one table: a piecewise map from new time to the film's old clock (slopes under 1 = slow holds). Everything keeps working, and a real-time push-in per scene keeps holds alive. Anything that must keep real speed (pulses, ripples) reads the new clock.
- Eleven Music with a composition_plan hits total length exactly but ignored section directions: "near silent hold" stayed loud and the ending died at 31s. Carve silence with an env, generate the resolve as a second clip, measure its key (asked for Ab, got Bb) and tune any note to it.
- My bug, cost three renders: I replaced part of a line with a trailing `// comment`, and the code after it on that line was commented out, so the logo clock never ran. All gates passed and one wrong diagnosis ("partial renders break it") went out first. Rule: never add a trailing comment to a replaced fragment. Read a frame sheet of the climax after EVERY render, gates do not see it. Grep the edited line before believing a theory.
- Speech-to-text on the final mix is a cheap, objective test that a voice survives the score: 100% of words here.
- ffmpeg -nostats keeps freezedetect output clean. VO pitch down: asetrate + atempo works when rubberband is missing.

## 2026-11-08 · Studio day-6 reel: trend recreation (meme hook → screen), no vox
- Ask: "recreate this reel, same BGM, same hook, add our computer clip". Rebuilt, not copied: hook = free-licence stock (Mixkit 8755, 4K, no attribution) in 3 jump cuts on the song's beats; screen = original HTML render; song NOT baked in. Post with Instagram "Use audio" from the reference at 0:00, so the cut lands on the beat. the owner pushed back ("insta tags it automatically"); told him upload auto-tagging is unreliable and often mutes, and "Use audio" gets the same sound with the tag.
- Mixkit works with plain curl: search `mixkit.co/free-stock-video/<q>/`, files at `assets.mixkit.co/videos/<id>/<id>-{720,1080,2160}.mp4`. Faster than the Pexels-through-browser route.
- Find a reference's cut point by per-frame 1x1 luma (`scale=1:1 -pix_fmt gray`), not `select=gt(scene,…)`: the scene filter printed nothing here. Cut was frame 133 (4.433s), on an aubiotrack beat.
- This ffmpeg has no drawtext (no freetype). All text goes through the HTML render; the hook text is one transparent PNG laid over the stock clip. Keep `html` transparent, not only `body`, or the PNG comes out black.
- Stock 4K crop + scale gives SAR 1214:1215, and concat with rendered PNGs fails. Add `setsar=1` on both branches.
- Freeze gate on a screen recording: 6 small terminals typing still read as 0.4–0.5s holds over the full frame (the reference reel itself would fail). Root fix: a constant slow push-in (1.0→1.14× over 11s) plus agents typing their messages between tool calls. Result: 0 holds.
- render.cjs `rmSync` on the output dir means a stills pass wipes a full render. Stills now go to `<mode>-stills`. Splitting frames across 3 Edge workers per mode cut the full render from ~5 min to ~1.5 min.
- Wall clock ~70 min against the 30 min budget. The time went to two full re-renders (text fix, freeze fix) and a 5-minute single-worker render. Run the freeze gate on a 3-second sample before the full render.
