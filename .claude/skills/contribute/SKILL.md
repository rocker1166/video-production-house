---
name: contribute
description: Send a generic improvement (a skill, workflow, engine fix, effect, style, doc) from the user's fork back to the shared house repo as a clean pull request, without any of their data or assets. Runs automatically after a post-mortem finds an upstreamable improvement, and on "/contribute". Respects the contribute mode in house.json (ask, auto, off).
---

# Contribute upstream

The shared repo gets better when everyone's agent sends back what it learned. Two rules keep it safe: **work in your own fork**, and **only generic improvements go upstream, never your data or assets.** The gate is mechanical (`ledger/contribute.py`), not a promise.

## When
- After the toolsmith's post-mortem lists items under `Upstream:` (`upstreamable: yes`), or the user says "send that upstream", or you fixed an engine bug or improved a skill while working.
- Never for: anything brand-specific, a tone or prompt for one product, clips, songs, renders, brands, workspaces, ledger runs, `house.json`, keys, personal paths. If in doubt it is not generic.

## Steps
1. **Mode:** read `contribute` in `house.json`. `off`: stop. `ask` (default): prepare everything, then ask the user ONE question with the diff summary. `auto`: after the checks pass, open a **draft** PR yourself.
2. **Make it generic and small.** One purpose per PR. Strip every example of the user's own product; use hypothetical ones. Add the check that proves it (a selftest line, a gate, an example). Edit `.claude/` (the source), then `python3 adapters/codex.py`.
3. **Self-review with fresh eyes:** dispatch the `pr-reviewer` agent on the branch; fix blockers.
4. **Propose:** `python3 ledger/contribute.py propose <slug> "<title>" <files...> --why "<anonymised evidence: the failing run, the measured number>"`. It branches from `upstream/main` with ONLY those files, runs the privacy and quality gate and the tests, commits and pushes to the user's fork. If it prints BLOCKED, fix and retry; never work around it.
5. **Open the draft PR:** add `--open` (and `--yes` only after the user said yes in `ask` mode). The PR is always a draft; maintainers review and merge.
6. `contribute.py status` shows what was sent. Mention it in one line at delivery.
Direct `git push upstream` and `gh pr create` are blocked by the guard hook on purpose.
