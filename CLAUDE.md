# Video Production House

One director (the `house` skill), many styles, one memory (`ledger/`). Every video request goes through `/make`.

## The loop (enforced by hooks, not by good intentions)
1. SessionStart prints the scoreboard, open runs and repeated mistakes.
2. The user's first message is the verdict on the open run: `house.py verdict last approved|corrected|rejected "<words>" --tags ...`.
3. Route to a style (`styles/INDEX.md`), read its `STYLE.md` and `RULES.md`, build, pass the gates, show.
4. A final render sets `ledger/.unlogged`; the Stop hook blocks until `house.py log` records the run.
5. Repeated correction tags become rules: `house.py promote <style> "<rule>"`. 3 approvals in a row = the style goes `auto`; one correction = back to `propose`.

## Layout
`engine/` render+cut pipeline · `effects/` 17 named effects + selection table · `styles/` the looks · `assets/` cached sfx+music (never regenerate) ·
`reels/` + `carousel/` brand-agnostic factories · `brands/` example and template products (yours live in the data home) · `ledger/` runs.jsonl (the reinforcement signal) + LEARNINGS.md · `hooks/` guard, mark, stop · `.claude/skills/` house, video-editing, style-forge, debrief.

## The crew (role subagents)
For any non-trivial job the main session is the producer (`production` skill, `/produce`) and dispatches role agents from `.claude/agents/`: researcher, scriptwriter, art-director, storyboarder, asset-wrangler, sound-designer, cinematographer, editor, qc-picture, qc-audio, toolsmith. Files in a job folder are the only handoff; each role writes only its own file; `ledger/job.py` checks the gates; QC is independent and capped at 3 loops; the toolsmith improves the tool after every verdict. Spec: `docs/WORKFLOW.md`. Subagents default to haiku; engine and agent-prompt changes are proposals the user approves.

## The observer (purpose and self-improvement)
`observer` understands the user's goal and turns it into a content strategy and workflow profile per brand (`brands/<b>/STRATEGY.md`, `workflow.json`), then every ~5 runs reviews the whole system against audience metrics and proposes improvements; `capability-scout` finds and vets skills, plugins and connectors. Run it with `/observe`. It only proposes. **Installs need the user's yes** (`ledger/cap.py`; the guard hook blocks `claude mcp add` / `plugin install` otherwise) and posting is always draft-only. Spec: `docs/OBSERVER.md`.

## The data home and brand isolation (one folder, many products)
The engine repo holds no user data. Everything of the user's lives in ONE data home (`python3 ledger/home.py data`; set by `/setup`, default `~/VideoHouse`): `house.json` (goals, autonomy, cleanup policy) · `brands/<product>/` (BRAND, CONTEXT, STRATEGY, workflow.json, refs.json, prompts/) · `workspaces/<product>/` (clips, songs, art, jobs, outputs) · `library/` (reusable, harvested) · `ledger/` (runs, capabilities) · `archive/`.
**Each product is isolated.** Its tone, prompts, context, strategy and linked repos/folders (`refs.json`, read-only unless marked write) are used only for that product. `python3 ledger/home.py use <brand>` sets the active brand (`job.py new` does it too) and the guard hook blocks any read or write of another product's files or repos. Role briefs list only the active brand's files. New product: `/setup add-product <name>` or `/brand`. Never post anything: the owner posts.

## Keeping it small
`python3 ledger/clean.py report|run|harvest|schedule`: dry-run by default; `--apply-safe` deletes only rebuildable scratch (plates, frames, tmp) and archives old finished jobs (verified tar, restorable). Clips, songs, finals, brands, library, ledger and linked repos are never touched automatically. Reusable parts of approved jobs go to `library/` (`harvest`).

## Setup and runtimes
`SETUP.md` / `/setup` (Claude Code) / `$setup` (Codex): installs requirements, asks goals and products with choices, links repos, sets autonomy and cleanup. Claude Code is the source of truth (`.claude/`); `python3 adapters/codex.py` generates `AGENTS.md`, `.codex/` and `.agents/skills/` for Codex (CI checks they are in sync).

## Standing rules
- Nothing is shown before the ship gates pass (A/V sync, no still hold >= 0.4 s, no black frames, -16..-13 LUFS, peak <= -1 dB). Gates do not see a wrong climax: read the frame sheet after every render.
- Never say how audio sounds without an `earshot` number behind it. Sound comes from real recordings (`real-sound`), not synthesis.
- Media never goes into git except `assets/`, `styles/`, `docs/`. Renders live in `work/` and `out/` (ignored).
- Time budget 30 min per reel; sample-check (3 s freeze test, stills) before any full render.
- Subagent reviewers are fresh-eyed and problems-only; verify their top claims on the frames before fixing.
- Copy structure and craft from references, never words, faces or client work. Check third-party screens for banned names and phone numbers.
- Secrets live in `.env` (see `.env.example`), never in the repo.

## Outside the repo (linked, not copied)
`earshot` and `real-sound` ship in `.claude/skills/` (earshot also needs its Python package + optional MCP, see its SKILL.md) · `vidcap` MCP for captions (optional).
