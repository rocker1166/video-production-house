> Examples below come from the travel niche (the proven one). The structures are niche-blind: read "place" as the brand's subject. See `brands/NICHES.md`.

# How we make short reels

Built from 32 reference reels: 7 the owner picked (`refs/`) and 25 scouted from Instagram's public popular pages for #travelreels,
#indiatravel, #himachalpradesh, #travelindia, #uttarakhand, #goa, #kerala, #solotravelindia and #roadtripindia (`refs/scout/`).
Every analysis (cuts, frame sheet, song, lyrics) is in `refs/ana/<id>.*`.

## What the references have in common
- **Short.** Most land at 8–19s. Drone holds run 8–24s, voiceover and itinerary reels 30–60s.
- **Cuts land on the beat**, on a 0.45–0.75s grid for fast songs and 1.5–2s for slow ones. Plain cuts, no fancy transitions.
- **The movement is inside the shot:** drone pushes, handheld drift, flags in wind, someone walking away from the camera.
- **The song starts at the part people know.** When the reel used a sped-up or remixed version, its own audio is the version (song.py does this automatically).
- **Text is small.** The most-liked reel (8.3M) is one drone shot with a tiny tag.
- **People are seen from behind.** It lets the viewer picture themselves there.

## The 16 formats (`bin/make.py <format> --help`)

| # | Format | What it is | Proof (likes) | Good songs (`bin/bgm.py`) |
|---|---|---|---|---|
| 1 | `drone` | 1–3 long aerial holds (~4s each) and a tiny place tag | 8.3M, 1.8M, 780k | love-story-indila, thenkizhakku |
| 2 | `flip` (myth) | "The India you see online:" over chaos → "The India I experienced:" over beauty → closing line | 1.85M, 993k | tujh-mein-rab, silver-springs |
| 3 | `audio` | No text, the song carries it. Best letterboxed wide shots | 804k | time-go |
| 4 | `mood` | One handwritten line for the whole reel | 620k | mitwa |
| 5 | `flip` (contrast) | "Everyone wants…" over normal life → "But I want this" over the place | 573k | finding-her-hua-main |
| 6 | `quote` | 1–3 slow shots under a relatable top line; `--look bold` for the insider hook ("Only real … know this 🔥") | 511k, 240k | back-to-friends, baudi-ritu, the-one-jorja |
| 7 | `voice` | Narration with word-by-word captions and a fixed top hook; one place per sentence | 468k, 201k | child-in-us (bed) |
| 8 | `solution` | Pain words on black, one per beat → the place at the drop | 464k | chahvan-sohneya |
| 9 | `title` | One thin serif place word for the whole reel | 316k | maahi-ve |
| 10 | `itinerary` | "3-day plan 📥 save this", then a DAY tag + one step per act | 307k | pahadi-folk |
| 11 | `lyrics` | The song's own words, line by line or word by word | 307k, 153k | safar-bayaan, dil-ye-bekarar |
| 12 | `cinematic` | 16:9 clips letterboxed on black, tiny spaced serif label, folk song | 283k | pahadi-folk |
| 13 | `pov` | "pov: you finally take that trip", journey shots (train, plane) → the place | 202k | pakeezah-ungli |
| 14 | `recap` | Route card → STRANGERS → DAY 1… → FAMILY: the group-trip story | 106k | maahi-ve |
| 15 | `story` | Setup line, punchline on the cut | 62k | jaan-se-guzarte-hain |
| 16 | `listicle` | "Best places for your FIRST GROUP TRIP", then one place name per act across places | 39k | pakeezah-ungli |

**Not buildable from stock:** the spin trend, talking-head tips and "travel reel idea" tutorials all need the creator on camera.
They're worth doing with real trip footage later. `recap` is also best with real trip footage: it's the brand's own pitch.

## Pipeline (one brief → many reels)

```
brief: place + format + song (+ text)               e.g. Spiti · solution · chahvan-sohneya · "Monday, EMI, …" → "Ilaaj: Spiti"
  0. refs      bin/ref.py <instagram url>: cuts, sheet, Shazam, lyrics → refs/ana/<id>.*
  1. song      bin/song.py <slug> "<title>" --ref refs/ana/<id>.mp3: hook aligned to the reel, beat grid (BGM store: bin/bgm.py)
  2. clips     Pexels via the built-in browser → bin/fetch.py <library> (a *-wide library keeps 16:9)
  3. voice     bin/voice.py <slug> "<script>": free neural TTS + word timings (voice format only)
  4. spec      bin/make.py <format> …: acts (library + length + cut rule) on the beats, plus captions
  5. render    bin/render.py: cuts, grade, letterbox, captions, voice over a quiet song bed → out/<NNN>-<name>.mp4
  6. check     qc/<NNN>-<name>.jpg + full-size caption frames; then the owner's verdict → LEARNINGS.md
```
Libraries: places (ladakh, spiti, kashmir, manali, meghalaya, kerala), categories (city = the "before" act of `flip`, journey = the start of `pov`)
and `himalaya-wide` (16:9 for `cinematic`). `batches/<date>-b<N>.sh` holds each batch's commands, so any batch can be re-run.

**One export per reel:** `out/<NNN>-<name>.mp4`, numbered for good (`numbers.json`), with the song in it. No silent copy.

## Where the clips come from (best first)
1. **the brand's own trips:** real footage that we own, showing the actual trip. Long term this should be the main source.
2. **Pexels:** free for commercial use. Collect via the browser (`reels/pexels.md`). India-specific footage is thin for some places.
3. **Other creators' clips:** only with permission and a credit.

## Learning loop
Every reel goes into `runs.jsonl`. the owner's reply is the verdict: corrections become rules in `LEARNINGS.md`, and look changes go into `style.json`.
After 3 batches in a row approved with no changes, I make whole batches without asking. Posting always stays with the owner.
| 17 | `stack` | **Teaser / intro (agency-style).** Dark editorial bg + film dust. 0–3s voiced words one at a time ("hi!" → "we are" → brand) with small B&W people cards popping round the text, "and we" zooms through → a held two-line serif line ("build trips") while cards pile up at a flat ~0.23s cadence (small stickers/tiles at first, then photos, app screens, growing to full-bleed) with the text turning to blend-difference on a HIT at ~5.5s → hard clear, "with" / "you" → logo reveal. 14.5s. | ref 19.5k likes (coconat.creatives) | gone-gone-tyler |
| 18 | `teaser-drop` | Brand sting built on one song drop: tease captions on slow shots → accelerating flurry (0.3→0.17s) with app cards → font-flip INTRODUCING + clay icons → iris wipe ON the drop → logo + tagline. 12.4s. | own (the owner's Downloads sting rebuilt) | maahi-ve (start 7.207s) |

## Teaser / intro playbook (formats 17, 18) — use for any teaser or intro video
- **Plan (from the ref, measured):** voice+sparse music 0–3s → held line 3–5.5s with a slow, small pile → one HIT at ~5.5s → fast pile to full-bleed → clear → short words → logo. The only hard sync points are the spoken words and the HIT; cards cut at a FLAT cadence (6 frames @25fps = 0.24s), not on the beat grid (earshot: 29% on grid = chance).
- **Tone:** near-black bg (#121212 → #1d1d1d vignette) + animated dust, high-contrast serif (Cormorant Garamond 500, -0.03em, line-height .84), B&W people cards, brand colours only in tiles/photos, logo on brand teal. No emoji, no gradients.
- **Voice:** edge-tts en-IN-NeerjaNeural, one clip per word (silenceremove-trimmed) placed on the ref's word times; music ducked (0.42) under it, full at the HIT.
- **BGM:** `gone-gone-tyler` (ref's own song, hook at 275.1s, matched 0.75) for stack; `maahi-ve` from 7.207s for teaser-drop. Align a song by its HITS (stabs, kick, drop), not aubio's grid.
- **Build:** HTML page with `seek(frame)` → Edge CDP jpeg frames → ffmpeg. Template + assets in `spec/stack-intro/` (index.html, render.cjs, voice wavs). Swap the card lists (`FACES`, `P2`, `PH`, `APP`, `ICONS`) and the words in the `.tx` divs.
- **Reuse rule:** take structure, pacing, type and colour mood from a ref, not its people or client work. the brand's cards are our own stills, clay icons and app screens.
- **Kinetic upgrade (024):** pile cadence 4–5f instead of the ref's 0.24s, flash frames, 6 card entrances, camera push/shake on hits, kinetic letters. Fonts: Playfair Display 900 + Playfair italic (orange accent word) + Geist Bold for the brand word. Audio unchanged (the ref's own cut: `gone-gone-tyler-reel`).
- **Story version (025):** one idea per beat, one motion per beat, captions that describe the picture; see LEARNINGS 2026-11-06. Beats are timed to the ref audio hits (5.44s places, 7.98s crew, 9.36s app, 10.94s clear, ~13.3s logo).
