# How a production crew works, and how the house copies it

The house runs as a **crew of role agents** under one producer (the main Claude session). This page is the spec: what the research found, the phases, who owns what, and the two loops that make it improve.

## 1. What the research says

**Real-world production** splits into pre-production, production and post-production, and each phase hands a named artifact to the next: brief, script, storyboard/shot list, asset library, footage, edit, graded and mixed master, delivery files ([ImageKit](https://imagekit.io/blog/video-production-workflow/), [Moon B](https://www.moonb.io/blog/video-production-team)). Pre-production staff (producer, director, scriptwriter, production designer) plan so that filming and editing hit fewer problems; the cinematographer and production designer own the look together; post is editor, sound designer, VFX artist and colorist.

**Agencies keep the creative brief as the foundation of review.** Put approval criteria in the brief so reviewers judge against agreed goals, not taste; name the approver; limit revisions to 1-2 rounds, because more rounds usually means the brief was unclear; a creative director reviews against the brief, then brand/compliance and technical checks follow ([Girard Media](https://girardmedia.com/blog/agency-creative-feedback-revision-process), [Dropbox](https://www.dropbox.com/resources/review-ad-creative-before-launch), [StudioBinder](https://www.studiobinder.com/blog/client-feedback-improve-video/)). Feedback pinned to the exact moment beats vague comments.

**AI pipelines converge on the same crew.** A coordinating producer holds the shared vision while specialists (casting, production designer, storyboard artist, director's assistant, one DOP per scene, editor) each hand to the next; the most-skipped step is the rough-cut review, which is the gate that catches pacing, sound and emotion errors; expect over-generation (about 3 tries per usable shot) and context drift if work is not chunked ([invideo multi-agent pipeline](https://invideo.io/faq/what-is-a-multi-agent-ai-film-production-pipeline/)). Research frames it as a closed loop of **plan, generate, verify, refine**: CoAgent's storyboard planner, generator and verifier agent re-plan any shot that scores below threshold, capped at 3 iterations, where about 72% of shots pass first time and 98% converge within the cap ([CoAgent](https://arxiv.org/html/2512.22536v1)); other papers use the same pattern with director, plan critic and video critic roles ([DATAREEL](https://arxiv.org/pdf/2604.25220), [Preacher](https://arxiv.org/pdf/2508.09632), [MovieAgent](https://arxiv.org/html/2503.07314v1)). The consistent human role is a creative director on top, with agents building the skeleton ([IEEE SMC CAI 2026 tutorial](https://www.ieeesmc.org/cai-2026/tutorial-10-a-human-ai-collaborative-framework/)).

**Broadcast QC** checks audio sync, unclear sound, duration against metadata and visual focus by eye, and measures loudness (EBU R128: -23 LUFS broadcast, a short-form supplement allows a bit more for programmes of 60 s or less; -1 dBTP peak) ([EBU R128 s1](https://tech.ebu.ch/publications/r128s1), [Clearcast QC](https://help.clearcast.co.uk/en/article/qc-steps-failures-templates)). Social platforms publish their own specs and change them, so check the platform page, not this one.

**Caveats, stated plainly:** most AI-pipeline sources are vendor pages without independent benchmarks. Reliable quality gates between agent handoffs are described as an unsolved problem ([Metavert](https://metavert.io/industry/ai-agents-for-film-video-production)). The house answers that with measurable gates plus independent QC, not trust. I found no solid data on short-form retention or typical round counts, so those numbers here are defaults, not facts.

## 2. Design decisions taken from it

1. **One producer holds the brief; specialists never talk to each other.** Subagents cannot spawn subagents, and the research shows drift when agents interpret the film separately. All context flows through files in one job folder; the producer reads every handoff.
2. **Every role owns one file** (`brief.md` by the producer, `research.md` by the researcher...). An agent edits only its own file. This is the "own project page per agent" rule that stops corrections spreading to other roles.
3. **Gates are files plus measurements,** checked by `ledger/job.py gate`, not by an agent's say-so.
4. **QC is independent:** fresh context, sees the brief and the output, never the maker's reasoning. It reviews against the brief's success criteria, then the technical gates.
5. **Fix loop capped at 3 iterations** (the CoAgent number); a failure after 3 goes to the human, not a fourth try. Human revision rounds default to 2.
6. **Over-generate shots, select ruthlessly** where footage is generated or stocked; budget about 3x.
7. **The crew is adaptive, not fixed.** Presets (`solo`, `standard`, `full`) are only starting points: the producer drops roles that have no work and adds roles the job needs (a colorist, a localizer, a compliance reviewer...), inventing one on the spot when none exists, and promotes it to a permanent agent once a second job needs it. Every change is logged in the brief with its reason. See `docs/ROLES.md`. This matches how real productions hire per project rather than keeping one fixed crew.

## 3. Phases, owners, artifacts, gates

| # | Phase | Owner (agent) | Artifact | Gate to leave the phase |
|---|---|---|---|---|
| 0 | Intake | **producer** (main session) | `brief.md`: objective, audience, platform, length, CTA, claims, approver, revision rounds, budget, **success criteria**, crew size | brief complete; open questions asked once, batched |
| 1a | Research | `researcher` | `research.md`: trend/format scan, music candidates with licence, VFX/SFX/art references, tools worth using, each with a source | every claim has a link or is marked unverified |
| 1b | Script | `scriptwriter` | `script.md`: hook (first 2 s), beats, captions/VO in brand voice | hook + payoff present, claims pass `BRAND.md` |
| 1c | Look | `art-director` | `look.md`: style from `styles/INDEX.md`, palette, fonts, effect budget, forbidden moves | style exists or `style-forge` requested |
| 1d | Shot plan | `storyboarder` | `shotlist.md`: one row per shot/scene: time, picture, camera, effect, caption, source | every beat from the script has a shot |
| 1e | **Greenlight** | producer | decision recorded in `brief.md` | `propose` style: show the user; `auto` style: proceed |
| 2a | Assets | `asset-wrangler` | `assets.md` manifest + files: clips, songs, SFX, logos, screens, each with licence and path | every shot has a source file; licences recorded |
| 2b | Sound plan | `sound-designer` | `sound.md`: music pick and hit points, SFX cue list, VO plan | cues map to shots |
| 3 | Build | `cinematographer` (camera and shot craft) then `editor` (assembly) | `plan.json` / spec, `out/*.mp4` draft | engine builds without error |
| 4 | Mix and gates | `sound-designer`, `editor` | master + `gates.txt` from `build.py check` | all mechanical gates PASS |
| 5 | **QC** | `qc-picture`, `qc-audio` in parallel | `review.md`: ranked issues, timestamp, owner role, fix, scorecard vs success criteria | no `blocker`; max 3 loops, then escalate |
| 6 | Delivery | producer | mp4 + thumbnail + caption + table, run logged | user sees only what passed QC; user's reply = verdict |
| 7 | **Post-mortem** | `toolsmith` | `postmortem.md` + patches | see section 5 |

## 4. Loop one: make the video better (QC)
`build -> qc-picture + qc-audio (fresh eyes) -> review.md -> owner roles fix their own artifact -> rebuild only what changed -> QC again`, at most 3 times (`job.py qc-loop`). Issues carry an `owner:` so the fix goes to the role that caused it, and the ledger counts faults per role.

## 5. Loop two: make the tool better (toolsmith)
After every delivered job the `toolsmith` reads `review.md`, the gate log and the user's verdict, and classifies each fault:

| Class | Example | Fix lands in |
|---|---|---|
| one-off | a bad crop on one shot | nothing |
| rule | "never put text over the face" | `styles/<style>/RULES.md` via `house.py promote` |
| engine | a gate missed a freeze; a script crashed | patch in `engine/` or `reels/bin/` **plus a regression check** |
| library gap | no effect fits this beat | `effects/` entry or a `style-forge` request |
| role gap | researcher cited no sources | edit that agent's prompt in `.claude/agents/` |
| brief gap | success criteria were vague | edit the intake questions in `production` skill |

Guardrails: patches are small, each carries a check (selftest, gate or example), `python3 ledger/house.py selftest` and syntax checks must pass, and changes to `engine/` or agent prompts are listed for the user's OK unless the style is on `auto` and the change is a doc or rule. The toolsmith never edits the ledger's recorded runs and never lowers a gate to make a video pass.
Roles with repeated faults show up in `house.py score`; that is the signal to rewrite their prompt.

## 6. Limits
Agents cannot hear or see on their own: sound claims need `earshot` numbers, picture claims need frames read at full size. Cost grows with context length times steps, so briefs to agents are short, outputs are failures-only, and the default is at most 6-8 agents in parallel.
