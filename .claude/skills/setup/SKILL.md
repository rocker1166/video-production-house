---
name: setup
description: Guided first-run setup for the video house - install requirements, choose the one data folder for all products, ask the user their goals and products with choices, link each product's repos and folders (read-only), write per-product tone, context and prompts, set autonomy and the cleanup schedule, and optionally generate the Codex adapter. Use on "/setup", "set this up", "first run", "add another product", or when no data home exists.
---

# Setup

Follow `SETUP.md` at the repo root, step by step; it is the single source. In Claude Code use AskUserQuestion for the choices (2-4 options, recommended first); in Codex ask in chat with numbered options. Batch questions, derive what you can from the folder, repos and sites, and explain before anything that installs software or edits persistent config (install.sh, crontab, hooks trust).

Hard rules: the engine repo never receives user data; each product gets its own brand folder and nothing from one product is used for another (`home.py use <brand>`); linked repos are read-only; no secrets in chat; never post. When done, print the summary from step 7 and the single next command.
