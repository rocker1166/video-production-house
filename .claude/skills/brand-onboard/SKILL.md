---
name: brand-onboard
description: Onboard any product or niche into the factories - interview once, write brands/<name>/BRAND.md + brand.json, set up the reel and carousel workspaces, pick the formats that fit the niche. Use on "/brand", "add a brand", "set this up for <product>", "adapt the reels/carousels to <niche>", or before the first reel-factory / carousel-factory run for a new product.
---

# Brand onboard: one product in, both factories ready

The factories are niche-blind. Everything niche-specific lives in `brands/<name>/`. Do this once per product.

1. **Derive first, ask once.** Read the product's site, README, app store page or the folder the user points at. Draft every field of `brands/_template/BRAND.md`.
   Ask only what you cannot derive, batched in one question: audience pain in their words, voice/never-say list, claims that must never appear, posting rule, a post they love.
2. **Create** the brand in the data home: `python3 ledger/home.py new-brand <name>` (copies `brands/_template/`: BRAND, CONTEXT, STRATEGY, workflow.json, refs.json, prompts/). Fill `BRAND.md` and `brand.json` (model on `brands/example-travel/` and `example-agency/`).
   **Link the product's repos and folders** in `refs.json` (read-only), read them (README, manifest, real UI strings) and write a one-page `CONTEXT.md`. Per-role prompt additions go in `prompts/<role>.md`. Then `python3 ledger/home.py use <name>` so nothing from other products leaks in.
3. **Pick the niche playbook** in `brands/NICHES.md`. If the niche is not there, add a row: subject, hook archetypes, the 3 formats to try first, the claims trap. Mark it `untested`.
4. **Set up the workspaces:** `reels/rf <name> new` and `carousel/cf <name> new`. Put the brand's fonts in `workspaces/<name>/style.json` (reels) and its colours in `brand.json` (carousel).
5. **Look before building:** make ONE reel and ONE 5-slide carousel as the pilot, show them, and take the owner's reaction as the first verdict (`house.py verdict`). Fonts and the look are what get corrected first, so lock them before any batch.
6. **Log** with `house.py log` (style `beatcut` for reels; add a `carousel` style row to `styles/INDEX.md` on first use).
