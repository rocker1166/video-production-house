# Contributing

The house grows three ways. Open a PR for any of them.
- **A style**: run the `style-forge` skill. Needs `STYLE.md` and one example plan+scenes that passed the gates (`engine/build.py <work> check`). No example = label it `seed` in `styles/INDEX.md`.
- **An effect**: add the scene to `effects/fx.js` and a row to `effects/EFFECTS.md` (beat type, budget). Only if a style needs it twice.
- **A lesson**: a rule that cost someone a render goes in `ledger/LEARNINGS.md` or a style's `RULES.md`.

Rules for everything: no personal paths, client names, faces, people's words or secrets; no renders or media in git (`assets/` aside); `python3 ledger/house.py selftest` must pass.
Your own `ledger/runs.jsonl` is private and git-ignored: it is your taste, not the project's.
