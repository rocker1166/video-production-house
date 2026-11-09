# Contributing

This project improves when everyone's agent sends back what it learned. There are two rules, and a mechanical gate that enforces them.

## The two rules
1. **Work in your own fork.** Fork the repo, clone your fork (`origin`), add this repo as `upstream`. Customise freely in your fork. Your products, clips, songs, brands and runs live in your data home outside the repo, so they are never in git at all.
2. **Contribute only what helps everyone.** Skills, workflow, engine fixes, effects, styles, docs, templates. **Never** assets or media (any binary), brand or product-specific text, workspaces, ledger runs, `house.json`, keys, personal paths or emails.

## How it works (usually automatic)
- Your agent's post-mortem lists generic improvements under `Upstream:`; the `contribute` skill turns them into a branch with ONLY those files, based on `upstream/main`.
- `python3 ledger/contribute.py check` blocks forbidden paths, binaries, secrets, personal paths, files over 300 KB, diffs over 1500 lines, failing tests and a stale Codex adapter. The same script runs in CI on every fork PR, taken from the base branch so a PR cannot weaken its own gate.
- `python3 ledger/contribute.py propose <slug> "<title>" <files...> --open` pushes the branch to your fork and opens a **draft** PR upstream. Mode `contribute` in `house.json`: `ask` (default: the agent asks you once), `auto` (draft PRs without asking), `off`.
- A maintainer reviews with the `pr-reviewer` agent plus a human read, and merges. `.github/`, hooks, the install guard, the isolation check and ship gates get a line-by-line read.

## By hand
```bash
git fetch upstream && git checkout -b contrib/my-change upstream/main
# edit .claude/ (the source), then:  python3 adapters/codex.py
python3 ledger/contribute.py check
git push -u origin contrib/my-change   # then open a draft PR against upstream
```

## What makes a good contribution
One purpose, small diff, a check that fails without it (a selftest line, a gate or an example), anonymised evidence in the PR (the failing run, the measured number), and edits to `.claude/` rather than the generated `.codex/` and `.agents/`. New styles need a worked example (`style-forge`); effects need a second user (`docs/ROLES.md` and `effects/EFFECTS.md` explain the bar).

Licence: MIT. By contributing you agree your change can be shared under it, and that you own or are free to share what you send.
