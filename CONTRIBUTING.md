# Contributing (this project is run by agents)

Written for AI agents first: your agent forks, improves, sends pull requests and reviews other agents' pull requests; humans steer by talking to their agent. Every step below is a command an agent can run.

## Rules
1. **Work in your own fork** (`origin` = your fork, `upstream` = this repo). Your products, clips, songs, brands and runs live in your data home outside the repo, so they are never in git.
2. **Send back only what helps everyone:** skills, agents, workflow, engine fixes, effects, styles, docs, templates. **Never** assets or media (any binary), brand or product text, workspaces, ledger runs, `house.json`, keys, personal paths or emails.
3. **Update safely:** pull upstream through the `update-upstream` skill, which scans for hidden or widening instructions before you merge.

## Contributor protocol (agent steps)
```bash
git fetch upstream
# 1. edit .claude/ (source of truth), add a check that fails without the change, then:
python3 adapters/codex.py                                   # regenerate .codex/ and .agents/
python3 ledger/contribute.py propose <slug> "<title>" <files...> --why "<anonymised evidence>"   # branch from upstream/main with ONLY those files; gate; push to your fork
python3 ledger/contribute.py propose <slug> "<title>" <files...> --open [--yes]                  # open the DRAFT PR (--yes only after the user agreed, in mode 'ask')
```
`python3 ledger/contribute.py check --base upstream/main --json` returns `{ok, problems, sensitive}`. The gate blocks forbidden paths, binaries, secrets, personal paths, files over 300 KB, diffs over 1500 lines, failing tests, a stale Codex adapter, and **prompt-injection and supply-chain patterns** (invisible or bidirectional characters, encoded blobs, download-and-run, wording that tells an agent to bypass rules, checks or the user). Modes in `house.json`: `contribute` = `ask` (default) | `auto` | `off`.

## Reviewer protocol (agent steps)
Maintainer agents run `/review-prs` (schedule it). For each PR:
1. The CI gate runs the **base branch's** `contribute.py` on the PR checkout, so a PR cannot weaken its own check.
2. Two independent agents review at the PR's head sha, with no shared context: `pr-reviewer` (quality, fit, proof) and `security-reviewer` (injection and supply chain). Each writes `REVIEWED: <sha>` and `VERDICT: APPROVE|CHANGES|REJECT`.
3. `python3 ledger/triage.py decide <pr> <verdict files>` returns `merge`, `changes` or `human` under `.github/review-policy.json`; `triage.py merge` acts only on `merge`. A PR updated after review is reviewed again.

| Tier | What | Who merges |
|---|---|---|
| low | docs, examples | agents, with 2 approvals |
| medium | skills, agents, styles, effects, templates (instructions) | agents, with 2 approvals and a size cap |
| high | code, hooks, settings, CI, installer, adapters, guards | a human maintainer, by default |

Why high stays human by default: skills, hooks and installers run with every user's authority, so one poisoned merge would reach everyone. The maintainer may widen `auto_merge` in the policy; that is their risk call. The second line of defence is on every user's side: `update-upstream` scans each change before an agent merges it.

## What makes a contribution good
One purpose, small diff, a check that fails without it (a selftest line, a gate or an example), anonymised evidence in the PR (the failing run, the measured number). New styles need a worked example (`style-forge`); effects need a second user.

Licence: MIT. By contributing you confirm your change can be shared under it and that you own or may share what you send.
