# Role catalogue: the crew grows

Built-in roles live in `.claude/agents/` and `ledger/roles.json` (`python3 ledger/job.py roles`). The table below is roles a real production has that the house does **not** build until a job needs them. They are starting points, not agents yet.

## How a role gets added (the producer decides, per job)
1. **Need first.** In intake the producer reads the brief and asks: is there a job here that no existing role owns? Name the gap in one line. No gap, no new role.
2. **Registered role** that fits -> `job.py add-role <job> <role>`.
3. **No role fits** -> `job.py adhoc <job> <name> <phase> <artifact.md> "<why this job needs it>"`. This writes a role card in the job folder; the producer fills in Do and Rules (use a catalogue row below as the seed), then dispatches a general-purpose agent on haiku told to follow the card. It is gated like any role.
4. **Seen twice** (two jobs invented the same role) -> `job.py promote <job> <name>` makes it a permanent agent and registers it. The `toolsmith` also proposes promotion when it sees the same gap in a postmortem.
5. Every added or invented role is logged in the brief's Decisions with its reason, so the crew never grows without a trail.

A role is valid only if it has: one artifact file, a phase (`develop`, `prep`, `build`, `qc`, `post`), minimal tools, a measurable "done", and no right to edit anyone else's file. A `qc` role must output `[blocker]/[major]/[minor]` lines with `owner:` and a PASS or REVISE verdict, so the gate and the fault counter work on it unchanged.

## Catalogue (not built yet)
| Role | Phase | Artifact | Add it when |
|---|---|---|---|
| `colorist` | build | `grade.md` | footage from several cameras or a look that must match a brand or a reference |
| `motion-designer` | build | `motion.md` | kinetic type, logo reveals, UI animation or any VFX the stock effects do not cover |
| `voice-director` | prep | `voice.md` | narrated work: voice choice, pacing, pronunciation, retakes, a pickup list |
| `localizer` | develop | `localization.md` | the same video in more than one language: captions, idiom, script-direction, font coverage |
| `thumbnail-designer` | build | `thumbnail.md` | the cover frame decides the click: YouTube, Reels covers, carousel first slide |
| `copy-strategist` | develop | `copy.md` | post caption, title, hashtags and search terms are part of the deliverable |
| `compliance-reviewer` | qc | `review-compliance.md` | regulated claims (health, finance, kids), sponsored content, music or footage licences, client-banned words |
| `accessibility-reviewer` | qc | `review-accessibility.md` | captions, contrast, flashing (photosensitivity), alt text, reading speed |
| `music-supervisor` | prep | `music.md` | licensed or commissioned music: clearance, edits to picture, stems |
| `platform-strategist` | develop | `platform.md` | multi-platform cut-downs: ratios, lengths, first-frame and cover rules per platform |
| `animator-3d` | build | `animation3d.md` | generated or rendered 3D, product turntables |

Check platform and licence rules on their own current pages; the role's file must cite them.
