# Effects library — what exists and when to use it

All effects are scenes in `effects/fx.js`, loaded on every render, so any style can use them.
Effects marked **plate** composite the creator's own frames: set `"plate": true` on the scene and run
`build.py $W plates` after `aroll`. That step makes `matte.mov` (an Apple Vision person matte, every frame,
~70s for 47s of footage) and per-scene frame dirs. Plate scenes are opaque and replace the A-roll for
their window. Each plate frame loads 2 images, so a plate scene renders ~3x slower than a plain one.

## Choosing effects (the selection rules)

Read the beat sheet. For each beat, find its **type**, then take the first effect in that row that
fits the style and hasn't been used yet in this reel.

| Beat type (what the line does) | First choice → alternatives |
|---|---|
| Hook / bold claim (first 2s) | `couchWall` (the claim behind them) → `coverStory` → `digitalZoom` on the key word |
| A number, stat, money, days | `pullBack` (counter) → `paperCut` (ransom-note number) → `chartGrow` |
| Growth, result, before → after | `chartGrow` → `vertigo` on the realisation |
| A list, steps, "how it works" | `checklist` → `phoneMockup` → `listTracker` (when the whole reel is a listicle) |
| Product / tool / UI demo | `uiWorld` → `phoneMockup` → `frameBreak` (they "step out" of the product) |
| The problem, piling up, chaos | `headlineWall` → `orbit` (the many things they juggle) |
| Realisation, tension, "wait…" | `vertigo` → `digitalZoom` |
| Topic shift / new section | `zoomThrough` (land on the next cut) |
| Playful aside, personality | `doodleBoil` → `paperCut` |
| Context or setting change | `greenScreen` (put them in the place they're talking about) |
| Brand word, payoff, CTA word | `glassType` → `coverStory` |
| Emphasis on one word | `digitalZoom` (punch 1.3–1.45, 0.35s) |
| Sound-off viewers (on request) | `captions` on layer 2, keywords in `highlight` |

**Budget rules**
- Use at most one plate effect per ~5s of runtime. In between come A-roll, punch-ins and the style's own B-roll.
  Effects are seasoning; if every beat has one, none of them land.
- Don't repeat an effect in one reel, except `digitalZoom` and `captions` (or a listicle that *is* about effects).
- An effect must illustrate the words spoken over it. If you can't say which word it lands on, cut it.
- 2–3.5s per effect. Put cue `hit` on the word.

## Catalogue

| Scene | Plate | What it does | Key props / cues |
|---|---|---|---|
| `orbit` | ✓ | cards circle the person: behind on the far side, in front on the near side | `cards[]`, `turns`, `y` |
| `couchWall` | ✓ | giant type on the wall **behind** them (auto-fit to width) | `text`, `size`, `y`; cue `hit` |
| `uiWorld` | ✓ | product UI panel on top, video below, items drop in | `title`, `items[]`; cue `drop` |
| `frameBreak` | ✓ | video in a window; the person spills out over its edge | — |
| `digitalZoom` | ✓ | eased sub-pixel punch on a word (no judder) | `from`,`to`,`dur`,`back`; cue `hit` |
| `phoneMockup` | ✓ | floating phone beside them, steps advance | `steps[]` |
| `checklist` | – | glass panel ticking items off (an `alpha` overlay) | `items[]`; cues `tick0..n` |
| `headlineWall` | ✓ | newspaper scraps slap onto the wall behind them | `headlines[]`; cue `hit` |
| `zoomThrough` | ✓ | push into the frame with blur across a cut, then land | cue `cut` |
| `chartGrow` | ✓ | glowing line chart draws behind them + label pill | `points[]`,`label`,`dur` |
| `pullBack` | ✓ | full-frame video pulls back into a card on a page + counter | `to`,`suffix`,`label` |
| `greenScreen` | ✓ | the person keyed onto a designed background | `kicker`,`timer`,`text`,`scale` |
| `paperCut` | ✓ | the person as a white-bordered sticker on scribbled paper + ransom-note text | `text` |
| `doodleBoil` | ✓ | hand-drawn outline boiling at 10fps + doodles | `doodles[]` |
| `vertigo` | ✓ | dolly zoom: the room recedes, the person holds size | `amount` |
| `coverStory` | ✓ | magazine masthead behind their head + cover lines | `title`,`lines[]`,`linesY` |
| `glassType` | ✓ | giant frosted letters refracting the video | `text`,`size`,`y` |
| `captions` | – | word-by-word pop captions, keywords yellow and bigger | scene `"captions": true`, `"highlight": [..]`, `"layer": 2` |
| `listTracker` | – | corner list whose active item lights up | `items[]`; cues `item0..n`; `"layer": 3` |

**Layers:** a scene with `"layer": N` goes on its own track above the lower layers (captions = 2,
trackers = 3). Scenes on one layer never overlap. When captions are on, keep scene text above y ≈ 1150.

**Rules learned building these**
- One plate still contains the person, so the subject layer must never be smaller than the video
  layer behind it. Vertigo doubled the head until this was fixed.
- Matte PNGs are white with the matte as alpha, made from one finite stream. A lavfi colour source never ends.
- Everything composites in the HTML canvas with GSAP transforms: sub-pixel smooth. Never zoom with ffmpeg `zoompan`.

## Adding an effect
Write it in `fx.js` as `name(c, p)`, using `usePlate(p)`, `plateLayer('video'|'subject'|'outline'|'sticker')`,
GSAP on `tl`, and `cue(kind, t)` for foley. Add a row to the catalogue and a row in the selection
table, then render it into `examples/fx-gallery` to check it before using it in a client edit.
