---
name: debrief
description: Close a run and learn from it - record the verdict, turn repeated corrections into rules, tidy the ledger. Use on "/debrief", after any delivered video, or when the SessionStart brief shows an open run.
---

# Debrief

1. `python3 ledger/house.py verdict <id|last> approved|corrected|rejected "<his words>" --tags ...` (rules in the `house` skill, step 0).
2. `python3 ledger/house.py score` - say the style's new level in one line (`propose` / `auto`).
3. `python3 ledger/house.py rules` - for every tag that repeated: write the rule (what to do, and why he corrected it) and
   `python3 ledger/house.py promote <style> "<rule>"`. A rule that is really a bug goes into the engine instead.
4. Append the human lesson to `ledger/LEARNINGS.md` (date, video, style, wall-clock vs budget, what the reviewer caught that the gates did not).
5. If the style was `rejected` twice, stop building in it and run `style-forge` to rework it.
