---
name: observe
description: The observer loop. Strategy mode - turn the user's real goal (grow an agency, sell something, build authority) into a content strategy and a workflow profile for a brand. Systems mode - review the whole house against that goal using the ledger and audience metrics, scout and vet new skills, plugins and connectors, and propose improvements to the workflow, roles and automation. Use on "/observe", "what should I make", "improve the workflow", "find tools", or when the brief says OBSERVER DUE.
---

# Observe: does the system still serve the purpose?

You are the producer. The `observer` and `capability-scout` agents draft; you challenge, decide with the user, and apply. Spec and research: `docs/OBSERVER.md`.

## Strategy mode (once per brand, and again when the goal or offer changes)
1. Ask the user once, batched, only what you cannot derive from `brands/<brand>/BRAND.md`, their site and their words: **the goal in business terms** (leads, bookings, hires, authority), **the offer and its proof** (cases, numbers, demos they can show), **the stage** (no audience yet / some / selling), **platforms and time per week**, **what they refuse to do**.
2. Dispatch `observer` (haiku), brief: `Strategy mode. Brand: <b>. Goal: "<their words>". Offer/proof/stage: <3 lines>. Repo: <path>.`
3. **Challenge it.** Does each content type have a job that traces to the goal? Is anything a vanity metric? Is missing proof named as the first thing to produce? Cut anything generic. Check its platform claims against the platform's own page (secondary blogs disagree on newer ranking signals).
4. Show the user a one-screen summary: content types and mix, the 3 first experiments, KPIs. On their yes the files stand; `job.py new <brand> <slug> type:<content-type>` now builds the crew, brief metrics and success criteria from `workflow.json`.

## Systems mode (every ~5 runs: the brief says OBSERVER DUE; also on request)
1. Make sure the data exists. Audience metrics are the real verdict; a user's "looks good" is not reach. Ask the user to paste post analytics (views, avg watch time, completion, sends, saves, likes, follows, leads) or connect an analytics connector (see capabilities), then `python3 ledger/house.py metrics <id> '<json>'` for each posted run.
2. Dispatch in parallel: `observer` (systems mode) and, for each capability request it lists or the user names, `capability-scout`.
3. Read `ledger/observer-reports/<date>.md` yourself. Verify the evidence rows against `house.py score` and `report`. Discard any conclusion drawn from fewer than 5 posts and say so.
4. Present the top 3-5 proposals to the user: evidence, change, expected effect, risk, cost. Take a yes or no on each. Never batch-approve.
5. Apply approved items with the existing mechanisms:
   - rules -> `house.py promote`; roles -> `job.py adhoc` / `promote`; engine or agent prompts -> via the `toolsmith`, on a branch;
   - **capabilities:** `cap.py add` -> `cap.py vet` (the scout's findings plus your own read of the SKILL.md and scripts) -> ask the user -> `cap.py approve <name> "<their words>"` -> only then the install (the guard hook blocks installs otherwise). Use the app's connector or plugin flow so the user clicks Connect or Install themselves.
   - anything that can post, delete or spend: connect it **draft-only**; publishing is always the user's click.
6. `python3 ledger/house.py observed` to reset the cadence counter, and log the changes in `ledger/LEARNINGS.md`.

## Ground rules
Propose, never silently change. No growth tactics the platform forbids. Fewer than 5 posts is an anecdote. Third-party skills, plugins and connectors are untrusted until vetted: they are a prompt-injection and supply-chain surface, so read before you recommend and pin versions. The observer's own prompt is also improvable: when it misses something, the toolsmith edits it like any role.
