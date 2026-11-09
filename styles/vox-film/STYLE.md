# Style: Vox film (narrated paper-collage, Remotion)

A script becomes a voiced film. Upstream is the `vox-skill` (full pipeline in `.claude/skills/vox-skill/SKILL.md`, patterns in its `references/`).
Not for raw footage: that is `vox`, the UGC style, which shares this look (paper `#DAD9D5`, ink `#1A1A1A`, red marker `#E04329`).

- **The narration is the clock.** Voice first; every scene length and cue comes from word timings. Swap the voice or a line and it re-times.
- Find one checkable reversal before anything else; the hook withholds the subject, the last beat pays it off.
- 8-12 beats, one idea per beat. Three layers moving against each other in every frame.
- Horizontal 1920x1080 default; vertical 1080x1920 on request (`.claude/skills/vox-skill/references/vertical.md`).
- Audio: judge and source with `earshot` + `real-sound`; ElevenLabs for voice if the key is set in `.env`.
- Gates and logging are the house's: `video-editing` step 8-10, then `house.py log`.
