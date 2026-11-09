# SETUP: guided first run (for the agent, and for you)

Works in **Claude Code** (`/setup`) and **Codex** (`$setup`, or "follow SETUP.md"). The agent runs these steps, asks you the questions with choices, and writes the answers to files. You can also follow it by hand. Ask in batches; never ask what you can read from the folder, repo or site.

## 0. Preflight (no questions)
- OS (`uname`), runtime (Claude Code or Codex), is there already a data home (`python3 ledger/home.py data`; if it prints the repo path, none is set yet), tools present (`ffmpeg`, `node`, `python3`, `yt-dlp`, `aubio`, a browser).
- Tell the user in 3 lines what you found and what is missing.

## 1. Install the requirements
`bash install.sh` (macOS Homebrew, Linux apt/dnf/pacman, Windows via WSL2). It installs tools, creates `.env`, runs the doctor. Explain before running: it installs packages on this machine. Missing keys are optional (ElevenLabs for voice/sfx, Gemini for carousel pictures).

## 2. Choose where everything lives (ONE folder for all products)
Ask, with choices:
1. `~/VideoHouse` **(recommended)**: private, local, easy to back up.
2. A folder you name (for example an external or large drive: clips and renders are big).
3. Inside a cloud-synced folder: warn that large renders will sync and cost quota.
Then `python3 ledger/init.py <path> --runtime <claude|codex|both>`. The engine repo stays clean; **your brands, runs and outputs never go into it**.

## 3. Who you are and what you want (one batched question)
- Your name or studio, and the **goal in your own words** (grow an agency, sell an app, build authority, launch something...).
- **Which products or projects** will live here (names; you can add more any time with `/brand`).
- Platforms and rough posting time per week.
- Choices: how autonomous should it be? (a) **ask before each build** (recommended at first), (b) ask only at greenlight and delivery, (c) run the whole crew and show me only the result. Maps to the `propose`/`auto` levels; it still never posts.
- Budget guard for AI pictures per job (default $2) and whether voiceover (ElevenLabs) is wanted.
Save with `python3 ledger/init.py merge '<json>'`.

## 3b. Per product (repeat for each; this is the isolation unit)
For each product ask or derive: what it is and does, who it is for, the **tone** (ask for 2 example lines they like and 2 they hate), claims that must never appear, branding (colours, fonts, logo), and **linked repos or folders** (the product's code, docs, site, design files: read-only by default).
Then: `python3 ledger/home.py new-brand <name>`; fill `BRAND.md` and `brand.json`; write `refs.json` (paths, purpose, `read`); read the linked repos **read-only** (README, package manifest, UI strings) and write a one-page `CONTEXT.md`; optional per-role prompt additions in `prompts/<role>.md`.
Nothing from one product may be used for another: this is enforced by `python3 ledger/home.py use <brand>` plus the guard hook.

## 4. Strategy and first pilot
Offer to run `observe` strategy mode for each product (content types, metrics, first experiments), then make **one pilot** (one reel or carousel) through `/produce` and take the reaction as the first verdict.

## 5. Keep it small: cleanup
Explain in one line: finished jobs are archived (restorable) and rebuildable scratch data deleted; clips, songs, finals, brands and the ledger are never touched automatically. Ask: (a) **weekly automatic cleanup, safe classes only (recommended)**, (b) report only, I decide, (c) off. For (a): `python3 ledger/clean.py schedule --install` (this edits your crontab; say so first). Defaults: scratch after 14 days, archive after 45, warn at 20 GB.

## 6. Runtime adapters
Claude Code: nothing more (it reads `.claude/`). Codex: `python3 adapters/codex.py` generates `AGENTS.md`, `.codex/agents/*.toml`, `.codex/hooks.json`, `.agents/skills/` from the single source in `.claude/`; open `/hooks` in Codex and trust the project hooks.

## 7. Verify and finish
`bash engine/doctor.sh`, `python3 ledger/house.py selftest`, `python3 ledger/job.py selftest`, `python3 ledger/clean.py report`. Print a summary: data home path, products and their linked repos, autonomy level, cleanup choice, the next command to run. Save no secrets in chat or files other than `.env`.
