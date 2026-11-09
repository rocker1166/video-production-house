---
name: style-forge
description: Add a new editing style to the video house from a reference the user likes (a reel link, a video file, screenshots), or split a style that keeps getting corrected. Use on "/forge-style", "make a new style", "I want it to look like this", "add this look to the house".
---

# Style forge: a look becomes a reusable style

A style is `styles/<name>/` with: `STYLE.md` (the law), `examples/` (one real plan + scenes that passed the gates), `RULES.md` (earned later by the ledger).
Never ship a style that has no example. A style with no example is `seed`, and says so in `INDEX.md`.

1. **Read the reference properly.** Video: `yt-dlp` it, then 4 fps contact sheets (2 fps hides fast reels) and `earshot timeline` for audio. Note: palette (exact hex), type, motion/easing, cut rhythm (shot length histogram), transition vocabulary, caption zone, sound feel, what the hook does in 2 s.
2. **Write `STYLE.md`** in this shape (copy `styles/vox/STYLE.md`): when to use it · visual system · vocabulary · scene archetypes · rules (safe frame, text sizes, forbidden moves) · which `effects/` fit and which break the register · sound.
   Copy structure and craft, never their words, faces or client work.
3. **Build one real video in it** through `video-editing` or the matching pipeline. The example is the plan + scenes from that video, kept in `examples/<slug>/`.
4. **Register it** in `styles/INDEX.md` (name, when, pipeline, status). Status `seed` until it has an `approved` run.
5. **Log** the build with `house.py log`; the style gets its own row in `house.py score` from then on.
6. **Effects discovered on the way** go to `effects/fx.js` + a row in `effects/EFFECTS.md` (beat type, budget). An effect is only added if a style needs it twice.
