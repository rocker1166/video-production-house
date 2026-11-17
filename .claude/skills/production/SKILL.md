---
name: production
description: The producer playbook. Run any video, reel or carousel job with a crew of role subagents (researcher, scriptwriter, art director, storyboarder, asset wrangler, sound designer, cinematographer, editor, picture QC, audio QC, toolsmith) through intake, development, pre-production, build, QC loop, delivery and post-mortem. Use on "/produce", "make this with the crew", "full production", or any non-trivial video job. Defers to `house` for routing and the ledger.
---

# Production: you are the producer

You are the main session: executive producer + creative director. You hold the brief, make every decision, talk to the user and dispatch the crew. Subagents do the craft work and cannot talk to each other or spawn agents, so **everything flows through the job folder and through you**. Spec and research behind this: `docs/WORKFLOW.md`.

## 0. Intake (you, not an agent)
1. Close the last run (`house` skill, step 0).
2. Restate the ask in one line. `python3 ledger/home.py use <brand>` (isolation). Read the brand's `BRAND.md`, `CONTEXT.md` and `prompts/` (none yet -> `brand-onboard` first).
3. Scaffold: `python3 ledger/job.py new <brand> <slug> <solo|standard|full>` and fill `brief.md` yourself. Crew size: `solo` simple carousel or one-off edit (4 roles) · `standard` a normal reel or batch · `full` a hero piece or a new niche (adds researcher and art director). Say which and why.
4. Derive everything you can from the folder, brand and references. Ask the user **once, batched**, only for what you cannot derive and cannot decide with a sensible default: objective, audience/platform/length, hard claims, success criteria, approver. A decision that is a coin-flip is yours; a decision about the user's taste or money is theirs.
5. Gate: `python3 ledger/job.py gate <job> intake`.

## 0a. Know the purpose before the format
If `brands/<brand>/STRATEGY.md` and `workflow.json` do not exist, or the user's goal has changed, run the `observe` skill in strategy mode first: a video for "grow my agency" is a different job from one for "launch my app". Pick the **content type** for this job from `workflow.json` (reach-hook, story-proof, offer-cta...) and create it with `job.py new <brand> <slug> type:<content-type>`: the crew, the metrics and the funnel role come with it. Success criteria in the brief must tie to the type's metrics. After the user posts, ask for the numbers and attach them: `house.py metrics <id> '<json>'`. If the brief says OBSERVER DUE, offer `/observe` before starting.

## 0b. Fit the crew to the job (adaptive, not a fixed template)
Presets are only a start. After the brief is filled, read it and ask for each role: **does this job have work that this role owns?** Drop roles with nothing to do (a talking-head edit needs no asset-wrangler; a carousel needs no sound-designer). Then ask the reverse: **is there work no role owns?** Examples: three cameras to match (colorist), a multi-language cut (localizer), regulated claims (compliance-reviewer), a cover that decides the click (thumbnail-designer). See `docs/ROLES.md`.
- Pick the crew: `job.py new <brand> <slug> <solo|standard|full | role,role,...>`.
- Add a registered role later: `job.py add-role <job> <role>`.
- Invent a role: `job.py adhoc <job> <name> <phase> <artifact.md> "<why>"`, fill the card in `<job>/roles/<name>.md`, dispatch a general-purpose agent (haiku) to follow it. Same rules as any role: one artifact, no editing others' files, gated.
- If you invent the same role on a second job, `job.py promote <job> <name>`. Log every addition with its reason in the brief's Decisions.
Do not add a role for taste or tidiness: each one adds cost (context x steps). One-line need, or no role.

## 1. Development (parallel where independent)
Dispatch with the Agent tool: `subagent_type` = the role name, `model: "haiku"`, and a brief of 5 lines max:
`Job folder: <absolute path>. Role: <role>. Read brief.md. Write <artifact>. Focus: <one line only you know>.`
Order: **researcher** and **art-director** in parallel -> **scriptwriter** (needs research) -> **storyboarder** (needs script + look). Then read every artifact yourself and fix contradictions before moving on (agents interpret separately; you are the one vision).
Gate: `job.py gate <job> develop`.

## 2. Greenlight (you)
Write the decision in `brief.md` under Decisions. Check `python3 ledger/house.py score`: style on `propose` -> show the user the hook, the shot list and the sound idea (short) and wait; style on `auto` -> continue and report at delivery. A new niche or a style with fewer than 3 verdicts is always `propose`.

## 3. Pre-production
**asset-wrangler** and **sound-designer** in parallel (sound plan needs only the shot list). On a **page film** (section 4) the cinematographer(s) and the lead editor's framework step go out in that same message, on one condition: the film's clock exists. A voiced film takes its clock from the voice, so have the voice and its timing file made first (from `script.md`); every act time and camera cue is read from it. A film cut to music takes its clock from the hit points in `sound.md`, so there camera and framework wait for the sound plan. Gate: `job.py gate <job> prep`. Anything marked `unverified` licence or missing source -> change the shot or ask; never ship it.

## 4. Build
**Footage edits, reels, carousels:** **cinematographer** then **editor** (one pair per scene group on a large job, max 6-8 agents at once). The editor runs the engine and pastes the gate output (`build.py check`) into `edit-log.md`. **sound-designer** mixes and measures.

**Page films** (one HTML page with a clock, for example style `html-teaser`) are built by act, in parallel, with the shared renderer `engine/film.cjs`. Nobody writes a renderer, an encode script or a gate script. The commands are in the header of that file.
1. **Framework** (lead editor; 30 minute box). Copy `engine/film-template/` to `<job>/film/`. Write the act table (id, from, to) from the storyboard's act table and the film's clock. Everything two acts share (palette, fonts, a character rig, captions) goes in `film/lib/`. Done when `film.cjs info` and `film.cjs pure` pass. Shared files are settled here: a later change to one re-renders the whole film.
2. **Camera** (one cinematographer per act group, alongside step 1). The first group's cinematographer owns `camera.md`: its own group's spec, then one line per sibling file. The others write `camera-<group>.md`. Each delivers its whole group in one pass.
3. **Acts** (one editor per act group: about one per minute of film, at most 3; a film under 45 s is built by the lead alone). Dispatch them together, as soon as the framework passes and their group's camera spec exists. Each writes only `film/acts/<id>.js` for its own acts and its own `edit-log-<group>.md`, and asks you for a shared-file change instead of making it. One check = ONE `film.cjs stills --at t1,t2,... --sheet` call.
4. **Assembly** (lead editor). `film.cjs draft` makes the QC cut (after a fix it renders only the changed acts). After QC passes, `film.cjs final ... --audio <mix>` makes the master and its full gate output goes into `edit-log.md`. QC saw the draft cut, not the master: look at the master itself before delivery (frames taken from the mp4 at the hook, the climax, the end and every time QC flagged).
The tool runs one render at a time per user and makes the others wait, so parallel editors cannot overload the machine. Give a Bash call that renders a whole film a 10 minute timeout.

Gate: `job.py gate <job> build` (needs a render and PASS in the edit log).

## 5. QC loop (the part most crews skip)
A QC review costs about 15 minutes plus the fixes, and the fix rounds are capped. Before the first one, check the cut yourself against the brief's success criteria on a frame sheet (hook, each act's key beat, climax, end card) and send obvious faults back: do not spend a review on them.
Run `qc-picture` and `qc-audio` in parallel, each given only the job path and its role: **no maker reasoning, fresh eyes**. Then:
1. Read `review-*.md`. **Verify the top 3 claims on the frames or measurements yourself** before acting; a reviewer is sometimes wrong (it misjudged font sizes off a small sheet once).
2. `python3 ledger/job.py gate <job> qc`. If REVISE: `job.py qc-loop <job>`, send every issue to its `owner:` role in one message (owners fix in parallel, each **its own artifact**), the editor re-renders only what changed, then QC again. Do not send "fix everything" to one agent.
3. Exit code 2 from `qc-loop` (the fix rounds are used up: 3 by default, `limits.qc_fix_rounds` in `house.json`): stop. Show the user the best version, the open issues, and ask. Never take another silent try.
Mechanical gates and measured numbers beat reviewer opinion; reviewer opinion beats yours on taste you cannot see.

## 6. Delivery
Only a build that passed QC is shown. Send the mp4 or PNGs + thumbnail + caption + one table (what was built, effects, gate numbers, QC scorecard, what is unverified or not done). Never post. Then `python3 ledger/job.py faults <job>` and `house.py log` with `{"style","video","effects","gates","minutes","faults":{...},"job":"<path>"}`. Say that the user's next message is the verdict.

## 7. Post-mortem (after the verdict)
Record the verdict (`house.py verdict`). Dispatch **toolsmith**: `Job folder: <path>. Verdict: "<their words>". Write postmortem.md and propose patches.` It classifies faults and improves the tool.
**Give back:** if `postmortem.md` has `Upstream:` items (generic, no brand data), run the `contribute` skill per the `contribute` mode in `house.json` (ask: prepare and ask once; auto: open a draft PR; off: skip). Never send anything brand-specific.
You then: apply rule promotions (`house.py promote`), approve or reject its engine and agent-prompt proposals with the user (engine and `.claude/agents/` changes are never silent), run `house.py selftest`, and append one line to `ledger/LEARNINGS.md`.

## Cost and hygiene
Cost grows with context length x steps: short briefs, artifact paths not pasted content, failures-only outputs, max 6-8 agents in parallel, haiku by default (a role that keeps missing may be raised to sonnet in its `.claude/agents/<role>.md` after the toolsmith shows the fault count). Skip roles the crew excludes. The toolsmith also watches for the same need recurring and proposes promoting an ad-hoc role. A job that stalls on one role for 2 attempts goes to the user, not a loop.
