---
name: reel-factory
description: Make short vertical reels for ANY product or niche - topic, subject or a reference reel in, numbered reels out, cut on a song's beats or a voiceover, with original captions in the brand's voice. 16 formats plus HTML teaser/intro reels. Use on "/reel", "make reels", "reel batch", "make a reel like this <link>", "next batch", or a topic for a brand that has been onboarded.
---

# Reel factory: brief in, numbered reels out (any brand)

`R=reels/rf <brand>` runs every engine script inside that brand's workspace (`workspaces/<brand>/`). No workspace yet -> `brand-onboard`.
Read first, in this order: `brands/<brand>/BRAND.md`, `workspaces/<brand>/LEARNINGS.md`, `reels/FORMATS.md` (the formats and what the references taught).

## 0. Tools (1 min)
`bash engine/doctor.sh`, then `which ffmpeg aubio yt-dlp`; Python deps in `.venv` (`numpy`, `shazamio`, `edge-tts`). Missing: `brew install aubio yt-dlp`.

## 1. Brief -> one line per reel
A brief = **subject + format + song + caption text**. `subject` is the brand's `reels.subject_label` (a place, product, scene, dish, exercise). Formats are structures, not topics: pick by what the line does.
| The reel does | Format | Note |
|---|---|---|
| one stunning thing, no words | `drone`, `audio` | least edit, often the top performer |
| one feeling in one line | `mood`, `title` | tiny type |
| contrast: normal life vs the thing | `flip` | myth-buster or "everyone wants X / but I want Y" |
| pain -> product/subject at the drop | `solution` | one pain word per beat; pains come from BRAND.md |
| setup -> punchline | `story`, `quote` | punchline lands on the cut |
| a plan or steps | `itinerary`, `listicle` | "save this" energy |
| narrated | `voice` | edge-tts voice + word timings |
| the song's own words | `lyrics` | only if you may use the song |
| group / community recap | `recap`, `pov` | best with real footage |
| teaser / intro / launch | `stack`, `teaser-drop` (HTML-seek) | `reels/template-stack-intro/`, playbook at the end of FORMATS.md |
Topic only -> pick 3-7 formats that fit the niche (`brands/NICHES.md`). Reference reel link -> `$R ref.py <url>`, read `refs/ana/<id>.dense.jpg` + `.cues.json`, match a format or add one to `reels/bin/make.py` + a row in FORMATS.md. Copy structure, never words, faces or client work. Nothing -> the next batch: rotate subjects x formats not yet in `numbers.json`.

## 2. Clips
Library per subject in `workspaces/<brand>/library/clips/<subject>/`; need about 3x the shots of the longest reel. Own footage first, then Pexels / Mixkit (free commercial licence, record it in SOURCES.jsonl via `fetch.py`).
Pexels collection recipe: `reels/pexels.md`. Curate by slug: drop other regions/niches and off-vibe clips (a selfie at the lens, a hotel bed).
Mixkit works with plain curl: `mixkit.co/free-stock-video/<q>/`, files at `assets.mixkit.co/videos/<id>/<id>-{720,1080,2160}.mp4`.

## 3. Song or voice
`$R song.py <slug> "<title artist>" [--ref refs/ana/<id>.mp3 | --start SEC] --len 30 --mood "tags"` -> finds the hook, builds the beat grid, files it in the store (`$R bgm.py` lists it).
A weak ref match means the reel used another version: use the reel's own audio. Align to the audio's HITS (`$R cues.py`), not aubio's grid.
Follow the brand's `music_policy` (licensed song / royalty-free / "post with the platform's Use audio", never baked in). Voice: `$R voice.py <slug> "<script>" [--voice ...]`.

## 4. Captions: original, short, in the brand's voice
Write them yourself from BRAND.md pains and voice; examples live in `brands/example-travel/`. Fonts are locked in the workspace `style.json`; never letter-space non-Latin scripts.
Captions must describe what is on screen and read as a sentence in order.

## 5. Make + render
`$R make.py <format> <subject> <song> [--text --words --lines --intro --every --seed] --render` (`--help` lists options). Write the batch's commands to `workspaces/<brand>/batches/<date>-b<N>.sh`. Output `out/<NNN>-<name>.mp4`, numbered for good, song included, no silent copy.

## 6. QC before showing
Craft rules (each one cost a rejected cut): no effect twice in a reel; one idea and one motion per beat; real music not ticks and bells; sync to HITS; read FULL-SIZE frames at every caption (a contact sheet hides spelling and clipped words);
the opener is an iconic shot; payoff shot after a drop shows a person; sibling reels of one subject do not share most shots (change `--seed`). Fix, re-render that reel only. Judge audio with `earshot`, never by assertion.

## 7. Deliver and learn
Send the numbered reels with a table: number - subject - format - song - caption. Name weak spots (thin library, unverified claim). **Never post**: the owner posts.
The reply is the verdict: `house.py verdict last ... --tags` and one dated rule in the workspace `LEARNINGS.md` (a look change -> `style.json`). `house.py log` the batch (style `beatcut`).
Autonomy: propose batches until 3 in a row come back approved, then build batches unasked (still never post). `house.py score` shows the level.
