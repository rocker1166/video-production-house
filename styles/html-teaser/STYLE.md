# Style: HTML teaser (no footage; type, shapes, logo)

Built for the Studio teaser (20.5 s vertical). A film is one HTML page whose clock you seek per frame; Playwright+Edge renders PNGs, ffmpeg encodes.
Lessons that are already law (from `ledger/LEARNINGS.md`, 2026-11-07):

- Build the **logo motion first** as one animated SVG (CSS keyframes, seeked via `document.getAnimations()`); the climax is that same file on its own clock. One source gives every ratio and a transparent export.
- Retime to a voice with one piecewise map (new time -> film's old clock). Anything that must keep real speed reads the new clock.
- CSS: put `animation-fill-mode:both` inside each `animation:` shorthand. GSAP scale on nested SVG circles drifts: set `r` in seek(). Use opacity, not `visibility`, across scenes.
- Film grain: opacity ~.026, new grain every 3 frames, crf 18 + maxrate 18M (35 MB, not 164 MB).
- Never add a trailing `//` comment to a replaced fragment. Read a frame sheet of the climax after EVERY render; gates do not see it.
- Check third-party screens for words the client bans and for personal phone numbers in footers before they appear in frame.
- Run the freeze gate on a 3 s sample before a full render. Stills go to a separate dir so they cannot wipe a render.
- Sound: ElevenLabs Music ignores section directions (carve silence with an envelope, measure the key); verify the voice survives the score with speech-to-text on the final mix.
