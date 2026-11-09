---
description: Edit a raw talking-head/UGC video into a high-retention Reel — picks the style and the right effects (latest Downloads video if none given)
argument-hint: "[video path] [style: vox] [context: product, audience, CTA, captions?]"
---

Load and follow the `video-editing` skill (`.claude/skills/video-editing/SKILL.md`). Read `ledger/LEARNINGS.md` first, and close the open run per the `house` skill (step 0). Log the run with `ledger/house.py` at the end.

Input: $ARGUMENTS
- If a video path is given, use it. Otherwise use the newest video in ~/Downloads and say which one, in one line.
- If a style is named, use it. Otherwise pick it with the skill's style table and say which, in one line.
- Choose effects per beat with `effects/EFFECTS.md`, within its budget rules.
- Use any context given (product, audience, pain, CTA, captions). Derive the rest. Ask only for what's still
  missing, in one batched question.

Run the whole flow to the 30-minute budget and don't show anything that hasn't passed the ship gates.
