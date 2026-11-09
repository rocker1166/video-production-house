---
name: video-editing
description: Parent skill for editing raw talking-head / UGC video into high-retention vertical Reels. Owns the engine (frame-exact jump cuts, punch-ins, person matte, HTML/GSAP scene rendering, foley + music mix, ship gates, independent review), the effects library (17 effects incl. text-behind-person, orbit, frame break, green screen, paper cut, vertigo, glass type, captions) and the editing styles (vox = paper editorial). Picks the style and the right effect per beat. Use on "/video-edit", "edit this reel/video", "UGC edit", "make it vox style", "add effects", "edit the latest video". Not for TTS-narrated films from a script (vox-skill) or hard-sell ads.
---

# Video editing — raw footage in, retention-edited Reel out

**Target: under 30 minutes start to finish, ~3–5 min of it machine time.** Never debug the pipeline
mid-edit. If a script misbehaves, read `ledger/LEARNINGS.md`, then `docs/ENV.md`.

```
video-editing/
  engine/      ingest · build (cut, plates, compose, gates) · render · matte · cutout · qc · doctor · base.html vocabulary
  effects/     fx.js + EFFECTS.md (catalogue + which effect for which beat) + examples/fx-gallery
  styles/      <style>/STYLE.md (look, scene archetypes, rules) + examples/   — vox is the first style
  assets/      cached SFX + music (never regenerate) · LEARNINGS.md (read first, append last)
```
`S=$CLAUDE_PROJECT_DIR/engine`. `W` = a work dir next to the video (e.g. `<project>/ugc/work`).

## The flow (budget per step)

| # | Step | Budget | Command / artifact |
|---|---|---|---|
| 0 | Doctor | 1 min | `bash $S/doctor.sh` → READY (self-repairs playwright/venv/cutout) |
| 1 | Ingest | 3 min | `python3 $S/ingest.py [video] $W` → transcript.txt, faces_NN.jpg, plan.json skeleton |
| 2 | Context | 2 min | derive or ask once (below) |
| 3 | Style | 1 min | pick from `styles/` (below), then read its STYLE.md |
| 4 | Plan | 6 min | beats → effects per `effects/EFFECTS.md` + style archetypes → `$W/plan.json` |
| 5 | Assets | 2 min | `bash $S/cutout.sh $W name=sec …` (style cut-outs) · logo PNG in `$W/assets/` |
| 6 | Scenes | 6 min | `$W/scenes.js` from the style's examples; effects need no code, only plan entries |
| 7 | Stills QC | 2 min | `build.py $W jobs` → (`build.py $W aroll plates` if any plate effect) → `qc.sh $W stills` → Read `qc/sheet.png` |
| 8 | Build | 3 min | `node $S/render.cjs $W` ∥ `build.py $W aroll` → `build.py $W compose check` |
| 9 | Review | 4 min | one independent reviewer → fix round → re-render touched scenes only |
| 10 | Learn | 1 min | append `ledger/LEARNINGS.md` + loop log (`signature: ugc-reel-edit`) |

Parallel by default: render ∥ aroll. Render runs one Edge per worker (6, `--workers N`). Fonts and GSAP are
vendored, so no network. Measured: ingest 40s · cut-outs 5s · stills 6s · aroll 32s ∥ render 67s
(plain scenes; plate effects ~3x) · matte 70s + plates 45s (only with plate effects) · compose + gates 30s.

## 1. Which video
If the user names a file, use it. Otherwise `ingest.py` takes the newest video in `~/Downloads`. Say which file, in one line.

## 2. Context — derive first, ask once
Needed: **product** (what it does, the real screen and copy), **audience/ICP + pain**, **CTA**, **captions?**
(the default is none: leave the bottom 420px for the user's own), **language/tone**. Derive them from the working dir
(README, AGENTS.md, landing copy, the product source for real UI strings) and the transcript. Ask only
what's missing, in one batched AskUserQuestion. Never type passwords into a live site.

## 3. Pick the style
| Style | When | Doc |
|---|---|---|
| `vox` | explainer, pain → solution, product story, "here's what's broken" | `styles/vox/STYLE.md` |

If the user names a style (`/vox-edit`, "vox style"), use it. Otherwise pick by the table. Styles are listed in `styles/INDEX.md`; read the chosen style's `STYLE.md` **and its `RULES.md`** (earned rules,
read them as law). A new style goes through the `style-forge` skill.

## 4. Plan — the only per-video artifact
Read `transcript.txt` (words with **source** seconds, gaps marked). Write the beat sheet: one line per
idea, typed by `EFFECTS.md`'s beat types. Then `plan.json`:
- `scenes`: `{name, from, to, alpha, plate?, layer?, captions?, cues:{word: srcSec}, props}`. All times
  are source seconds; build.py maps them through the cut. Effects are scenes too: just name them.
- Mix: the style's own B-roll scenes carry the argument. Effects land on specific words (the EFFECTS.md
  selection table + budget: ≤1 plate effect per ~5s, no repeats).
- `punch`: `{srcStartOfCut: zoom}` on emotional words (1.2–1.3). Other cuts alternate 1.0/1.12.
- `sfx`: transitions/accents only (`{k, t|out|at:"end", v}`). Foley on element arrival is automatic.
- `cutouts`: eyes-open, expressive frames from `faces_NN.jpg` (cell k of sheet n = 16n + 0.5k s).

## 8. Ship gates (`build.py $W check`) — all must PASS before showing anyone
A/V sync · no still hold ≥0.4s · no black frames · loudness −16..−13 LUFS, peak ≤ −1. Then read the
`qc.sh $W final` sheets yourself: graphics on the beat, no 1–8 frame A-roll flashes, nothing in dead zones.

## 9. Independent review (one subagent, Sonnet, fresh eyes)
Brief: output path, speech timeline in OUTPUT seconds (`build.py jobs` prints the scene windows), what each
scene/effect should show, the reserved caption zone, "problems only, ranked, timestamp + fix, max 15";
use contact sheets, full-res stills, freezedetect, volumedetect. **Verify its top claims on the frames before fixing.**

## 10. Learn — do not skip
Log the run: `python3 ledger/house.py log '{...}'` (the Stop hook blocks until you do). Then append to `ledger/LEARNINGS.md`: date, video, style, effects used, wall-clock per step vs budget, user
corrections, what the reviewer caught that the gates didn't. A repeat becomes a rule in the right file:
engine → a script fix, look → STYLE.md, effect choice → EFFECTS.md.

## Deliver
The mp4 (SendUserFile, render) + `thumbnail.png`: the strongest full-screen frame, never frame 0 or a blink. Report
length, style + effects used, gate results, what is rebuilt rather than filmed, and what is not done.
