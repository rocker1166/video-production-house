# Style: Vox (paper editorial)

Explainer register. The creator talks; between the lines, the frame cuts to paper-collage B-roll that
makes the argument visible: documents, stamps, counters, struck-through lists, product screens on
paper, and halftone cut-outs of the creator with a red marker outline. Use it for pain → solution
explainers, product stories and "here's what's broken" UGC. Built first on the Demo invoice-chasing reel
(`examples/demo-invoice/`, plan + scenes).

Visual system (from vox-skill): paper `#DAD9D5`, ink `#1A1A1A`, red marker `#E04329`, highlighter
`#F5C518`. Type: Arial Black headlines (uppercase), Playfair/PT Serif documents, Special Elite typewriter, Caveat
for the hand-written. Don't add colours.

## Vocabulary (engine/base.html)
`paper()` · `rise(node, at)` · `slam(stamp, at, target)` · `stamp()` · `stroke(d)` + `draw()` · `hl(bar, at)` ·
`subject(IMG.her_x, {x,y,w,side})` (halftone cut-out + red offset stroke) · `fg(top)` (torn ledger-paper band) ·
`ring(el, at)` · `cue(kind, at)` · `el()` `$` `$$`. Cut-outs come from `engine/cutout.sh`.

## Scene archetypes (copy from examples/demo-invoice/scenes.js)
Document + stamp (UNPAID → PAID callback) · day counter + calendar · checklist struck through ·
chat phone with live typing · "Seen / no reply" tag · logo intro · product screen + highlighter rings ·
cursor click → dialog → toast · struck bubbles → "Manual follow-ups: 0" · end card.

## Rules
- Safe frame: x 0–930, y 180–1500. Top 180 and right 150 = platform UI. Bottom 420 = captions.
- Paper scenes = 3 layers: `paper()` bg, a `subject()` cut-out, and `fg(top)` ledger band. The band
  overlaps the cut-out's bottom by ≥120px, which hides the ragged edge.
- Overlays (`alpha`) sit on the chest, **below the mouth** (y ≥ ~1060 at zoom 1.0).
- Elements `rise()`, never fade in. Stagger 0.1–0.3s. Stamps go on clear space, not over key text.
- Product screens: the **whole card in frame at all times** (≤880px wide). Emphasise with `ring()`,
  dimming and colour, **never a pan** that crops UI. UI state changes are near-cuts (≤0.06s). A slow
  crossfade reads as doubled, ghosted UI.
- Calendars, counters and numbers stay internally consistent (dates follow the day count).
- Text ≥ ~30px for body and ≥ ~40px for anything the viewer must read.
- Pattern: a hook overlay from frame 0 → a full-screen paper B-roll every 3–6s → no A-roll stretch over ~4s
  without an overlay → product scene(s) on the payoff words → a callback to the hook's prop → end card.
- Effects that fit Vox: `coverStory`, `paperCut`, `headlineWall`, `pullBack`, `chartGrow`, `doodleBoil`,
  `vertigo`, `digitalZoom`. Go light on glossy ones (`glassType`, `greenScreen`); they break the paper register.
- Cut-outs: eyes-open, expressive frames only (from `faces_NN.jpg`); look at each one full-size.
- Sound: every element arrival has paper foley (automatic via `cue`), plus room tone and the cached music bed.
