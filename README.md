# Video Production House

An open-source video studio that runs inside [Claude Code](https://claude.com/claude-code). You give it raw footage, a topic or a product; it picks a style, builds the video or carousel through fixed quality gates, logs the run, and learns from your reaction. The more you use it, the stricter and faster it gets.

- **Edit raw footage** (talking head / UGC) into a retention-edited Reel with 17 named effects.
- **Make reels for any product or niche** from stock footage cut on a song's beats, or a voiceover.
- **Make carousels for any product or niche**: 1080x1350 art-led slides, brand colours, PNG + PDF.
- **Narrated explainer films** in a paper-collage style (Remotion).
- **Runs as a production crew**: a producer plus 11 role subagents (researcher, scriptwriter, art director, storyboarder, asset wrangler, sound designer, cinematographer, editor, two QC reviewers, toolsmith) that adapts its crew per job and can invent new roles.
- **Understands your goal**: an observer turns "I'm growing my agency" into a content strategy, reviews the whole system against audience metrics, and vets new skills and tools (nothing is installed or posted without your yes).
- **Learns**: every video gets a verdict; repeated corrections become rules; styles that keep getting approved earn autonomy.

> Platforms: **macOS** (the one it was built and tested on), **Linux** and **Windows via WSL2**. Linux and WSL2 support was written without a Linux machine to test on: CI (`.github/workflows/ci.yml`) smoke-tests Ubuntu and macOS, but treat a full Linux render as unproven until you have run one. Travel is the proven niche; other niches are playbooks you will prove.

---

## 1. Quick start (10 minutes)

```bash
git clone <this repo> video-house && cd video-house
bash install.sh        # macOS (Homebrew) · Linux (apt, dnf, pacman) · Windows: run it inside WSL2, see below
claude                 # open Claude Code in this folder (or `codex`, see section 4.9), then run /setup
```
Prefer to do it by hand? Install ffmpeg, aubio, yt-dlp, node and python 3.10-3.12 with your package manager, `cp .env.example .env`, `bash engine/doctor.sh` (wait for `READY`).
Claude Code asks you to trust the folder the first time; say yes, or the hooks will not run.

`/setup` is the guided first run: it asks your goals, creates **one data folder for all your products**, links each product's repos, and sets autonomy and cleanup (`SETUP.md` has the same steps if you prefer to follow them by hand).

Then, inside Claude Code:

| You want | Type |
|---|---|
| First run: install, goals, products, cleanup | `/setup` |
| Add another product later | `/setup add-product <name>` |
| Edit a raw clip | `/video-edit ~/Downloads/clip.mp4` |
| Set up a product (once) | `/brand MyProduct https://myproduct.com` |
| Make reels | `/reel myproduct "burnt-out office workers"` |
| Make a carousel | `/carousel myproduct "how it works"` |
| Anything video, let it route | `/make <video, topic, script or reel link>` |
| Understand my goal, adapt the workflow, find tools | `/observe <brand> strategy "I'm growing my agency"` |
| A bigger job with the full crew | `/produce <brand> <what to make> [solo\|standard\|full]` |

The first message you send after a video is its verdict ("looks good", "fonts are off"). Say what you think; the house records it.

---

## 2. Requirements and platforms

| Platform | How | Person cut-outs |
|---|---|---|
| **macOS 13+** | `bash install.sh` (Homebrew) | Apple Vision, fast (about 1 min for 45 s of video) |
| **Linux** (Ubuntu/Debian, Fedora, Arch) | `bash install.sh` (apt, dnf or pacman; asks for sudo) | `rembg` on CPU, slower (minutes) |
| **Windows** | use **WSL2**: in PowerShell `wsl --install -d Ubuntu`, open Ubuntu, clone the repo *inside* the Linux filesystem (`~/video-house`, not `/mnt/c`), run `bash install.sh` | `rembg` on CPU |

Native Windows (PowerShell/cmd) is not supported: the engine is bash, Python and Node, and WSL2 runs all of it.

| Needs | Why |
|---|---|
| [Claude Code](https://claude.com/claude-code) | runs the skills, commands and hooks |
| ffmpeg | every cut, grade, mix and gate |
| Edge, Chrome or Chromium | headless renderer for scenes, captions and slides (auto-detected; or `npx playwright install chromium`; override with `BROWSER=/path`) |
| Node 20+ | scene rendering, carousel engine |
| Python 3.10-3.13 | engine, ledger, hooks. Use 3.12 if you can: `onnxruntime` (person cut-outs off macOS) has no wheels for the newest Pythons |
| aubio, yt-dlp | beat detection, reference-reel download (reels only) |
| macOS only: Xcode Command Line Tools | compiles the Vision cut-out helper (`xcode-select --install`) |
| Linux/WSL only: `requirements-seg.txt` | `rembg` + `onnxruntime`; the first run downloads a ~170 MB model, so it needs internet once |

`engine/doctor.sh` checks all of this, installs the Python packages (`requirements.txt`) and Playwright, compiles the cut-out helper, and prints `READY` or what is missing. Run it again any time something misbehaves.

---

### Reference reels and downloads
`yt-dlp` (installed above) is what downloads reference reels and songs: `reels/rf <brand> ref.py <instagram-or-youtube-url>` downloads the reel, finds its cuts, song and lyrics. Public links work without a login; private or removed ones will not. Only download what you have the right to analyse, and copy structure, never someone's footage or words.

## 3. Configuration

Everything secret lives in `.env` (git-ignored; copy from `.env.example`). All keys are optional; without them the matching feature is simply unavailable.

| Variable | Used for | Without it |
|---|---|---|
| `ELEVENLABS_API_KEY` | AI voiceover, sound effects, speech-to-text on reference audio | free `edge-tts` voices still work; use the cached sfx in `assets/` |
| `GEMINI_API_KEY` | carousel picture generation (about $0.13 per image) | use your own photos with `"photo"` in the slide spec |
| `BROWSER` | path to Edge/Chrome/Chromium if auto-detection misses it | detected automatically |
| `BROWSER_CHANNEL` | Playwright channel to try first (`msedge`, `chrome`) | tries msedge, chrome, then bundled chromium |

Optional extras: the `earshot` skill needs its Python package (see `.claude/skills/earshot/SKILL.md`) to *listen* to audio; the `vidcap` MCP adds captions.

---

## 4. Guides

### 4.1 Edit raw footage: `/video-edit`
Raw talking-head or UGC clip in, a retention-edited vertical Reel out, target 30 minutes.
1. `/video-edit path/to/clip.mp4` (no path = the newest video in `~/Downloads`).
2. It ingests (transcript, face frames), derives the product, audience and CTA from your folder, and asks once for what is missing.
3. It picks a style (`vox` paper-editorial by default) and writes `plan.json`: cuts, punch-ins and effects chosen per beat from `effects/EFFECTS.md` (at most one heavy effect per ~5 s).
4. It renders, runs the **ship gates** (A/V sync, no still hold of 0.4 s or more, no black frames, loudness -16 to -13 LUFS, peak at or under -1 dB), shows frame sheets, and gets one independent review.
5. You get the mp4 and a thumbnail. Reply with your verdict.

Work files go in a `work/` folder next to the video (git-ignored).

### 4.2 Onboard a product: `/brand`
Do this once per product or niche, before the first reel or carousel.
1. `/brand MyProduct <site, folder or one-line description>`.
2. It reads what you point at, drafts `brands/myproduct/BRAND.md` (audience pains, voice, claims that must never appear) and `brand.json` (colours, fonts, libraries, music policy), and asks one batched question for the rest.
3. It creates the workspaces `workspaces/myproduct/` (reels) and `workspaces/myproduct/carousel/`.
4. It makes **one pilot reel and one pilot carousel** and takes your reaction as the first verdict. Fonts and look are what get corrected first, so lock them here.

Not sure what to put? Open `brands/example-travel/` (a complete worked example) and `brands/_template/`.

### 4.3 Make reels: `/reel`
Topic, subject or a reference reel link in, numbered reels out (`out/001-name.mp4`, song included, no silent copy).
1. `/reel myproduct "monday burnout"`, or `/reel myproduct https://instagram.com/reel/...` to copy a structure.
2. Pick formats by what the line does: `solution` (pain words then the product), `flip` (contrast), `story` (setup, punchline), `drone`/`audio` (one stunning thing), `voice` (narrated), `itinerary`/`listicle` (steps), teasers and intros. All 16 are in `reels/FORMATS.md`.
3. Give it clips: `workspaces/myproduct/library/clips/<subject>/`. Best is your own footage; Pexels and Mixkit are free for commercial use (recipe in `reels/pexels.md`). Plan on about 3x the shots of your longest reel.
4. It prepares a song (`song.py` finds the hook and the beat grid) or a voiceover, writes original captions in your brand voice, renders, and checks full-size caption frames.
5. Every reel is a numbered file you can name in feedback. It never posts.

Run engine scripts by hand with `reels/rf <brand> <script> ...`, for example `reels/rf myproduct make.py --help`.

### 4.4 Make carousels: `/carousel`
1. `/carousel myproduct "how it works in 6 slides"`.
2. It writes a spec (hook slide, 3 to 5 content slides, end slide), prints the image cost and asks before spending over your budget (`image_budget_usd`), generates pictures, shows a contact sheet for you to pick from, then renders `out/<slug>/slide-NN.png` and `pdf/<slug>.pdf`.
3. Six art looks (`illustrated`, `realistic`, `watercolour`, `retro`, `collage`, `clay`); switch with `--variant`. Instagram takes the PNGs in order, LinkedIn takes the PDF.
4. Real product screens go in a tilted phone frame via `"phone"` in a slide.

By hand: `carousel/cf <brand> jobs|gen|sheet|render|pdf <slug>`.

### 4.5 Narrated explainer films: `/vox-edit` and the `vox-skill`
A script becomes a voiced Remotion film, paper-collage look, 16:9 or 9:16. The narration is the clock; every cut is timed to a spoken word. See `.claude/skills/vox-skill/SKILL.md`.

### 4.6 Add a new look: `/forge-style`
Give it a reference reel, link or screenshots. It measures palette, type, cut rhythm and sound, writes `styles/<name>/STYLE.md`, builds one real video in it, and registers it in `styles/INDEX.md`. A style with no example video stays marked `seed`.

---

### 4.7 The crew: `/produce`
For anything beyond a quick single-skill task, Claude acts as the **producer** and runs a crew of role subagents, the way a real production does (the research behind it is in [`docs/WORKFLOW.md`](docs/WORKFLOW.md)).

```
brief -> research + art direction -> script -> shot list -> GREENLIGHT -> assets + sound plan
      -> camera + edit -> mechanical gates -> independent QC (picture + audio) -> fix loop (max 3)
      -> delivery -> your verdict -> toolsmith post-mortem (improves the tool itself)
```

| Role | Does | Writes |
|---|---|---|
| producer (main Claude) | asks you once, decides, dispatches, verifies, delivers | `brief.md` |
| `researcher` | trends, music, VFX/SFX, art styles, new tools, with sources | `research.md` |
| `scriptwriter` | hook, beats, captions, VO in your brand voice | `script.md` |
| `art-director` | picks the style, palette, effect budget | `look.md` |
| `storyboarder` | one row per shot | `shotlist.md` |
| `asset-wrangler` | clips, songs, SFX, screens with licences | `assets.md` |
| `sound-designer` | music hits, SFX cues, mix, measured loudness | `sound.md` |
| `cinematographer` | framing, punch-ins, effect timing | `camera.md` + plan |
| `editor` | builds, runs the ship gates, applies fixes | `edit-log.md` |
| `qc-picture`, `qc-audio` | independent review against your success criteria, with numbers | `review-*.md` |
| `observer`, `capability-scout` | the meta layer: strategy, systems review, vetted tools | `STRATEGY.md`, `workflow.json`, `capabilities.md` |
| `toolsmith` | after your verdict: turns faults into rules, engine patches, prompt fixes | `postmortem.md` |

The crew is **adaptive**: `solo` (4 roles), `standard` (8) and `full` (10) are only presets. The producer drops roles with no work, adds registered ones, or invents a new role when the job needs one (`job.py adhoc`), and promotes it to a permanent agent once a second job needs it (`job.py promote`). `python3 ledger/job.py roles` lists what exists and the catalogue of roles not built yet (`docs/ROLES.md`: colorist, localizer, compliance reviewer, thumbnail designer and more). Each job lives in `workspaces/<brand>/jobs/<slug>/`; `python3 ledger/job.py status <job>` shows what is done and `gate` blocks a phase until its files are real. The QC loop is capped at 3 rounds, then it asks you. Subagents run on haiku by default (change `model:` in `.claude/agents/<role>.md`); engine and agent-prompt changes the toolsmith proposes are never applied without your yes.

### 4.8 The observer: understands your goal, improves the system
Tell it the goal in your own words ("I'm growing my agency") and `/observe` turns it into a strategy: which content types you need (reach hooks, trust-building proof, authority explainers, offers, conversation), the metrics that prove each worked, the first experiments, and a workflow profile (`brands/<brand>/workflow.json`) so `/produce <brand> type:story-proof` builds the right crew for that job. Every ~5 videos the session reminds you (**OBSERVER DUE**) and it reviews the whole system: where time and QC loops went, which styles actually earned reach (needs your post analytics: `python3 ledger/house.py metrics <id> '{"views":..,"sends":..,"saves":..}'`, then `house.py report`), and what to change.
It also scouts skills, plugins and connectors (analytics, trend research, voice, draft-only scheduling) and vets them. **Nothing is installed or posted without your yes**: the registry `ledger/capabilities.json` holds proposals; a hook blocks `claude mcp add` and `plugin install` until you approve. See `docs/OBSERVER.md` for the research and the install policy, and `brands/example-agency/` for a worked agency-growth strategy.

### 4.9 One folder, many products (the data home and isolation)
The repo is the **engine**; your data lives in **one data home** (default `~/VideoHouse`, chosen in `/setup`, found by every script via `~/.config/video-house/home` or `HOUSE_HOME`):

```
VideoHouse/
  house.json            your goals, autonomy level, cleanup policy, limits
  brands/<product>/     BRAND.md (voice) · CONTEXT.md (what the product is) · STRATEGY.md · workflow.json
                        refs.json (this product's repos and folders, read-only) · prompts/<role>.md (per-role additions)
  workspaces/<product>/ clips, songs, art, jobs, outputs
  library/              reusable things harvested from approved jobs
  ledger/               runs, verdicts, metrics, capabilities
  archive/              old finished jobs, compressed and restorable
```
**Each product is isolated:** its tone, prompts, context, strategy and linked code are used only for that product. `python3 ledger/home.py use <product>` (also done by `job.py new`) sets the active product, and the guard hook blocks any read or write of another product's folders, workspaces or linked repos, and any edit of a read-only linked repo. Role briefs list only the active product's files. The hook checks shell commands by path text, so a deliberate `cd` trick can get past it; treat it as a seatbelt, not a vault.

### 4.10 Keeping it small (cleanup)
`python3 ledger/clean.py report` shows disk use per product and what a cleanup would do. `run` is a dry run; `run --apply-safe` does only the reversible classes: it deletes rebuildable scratch (plates, frames, tmp, stills) older than 14 days and archives finished jobs untouched for 45 days (the archive is verified before the original is removed; `restore <brand> <slug>` brings it back). Clips, songs, finals, brands, library, ledger and your linked repos are never touched automatically, and symlinks are never followed. `harvest` copies the scripts, hooks, shot lists and plans of **approved** jobs into `library/` so the good parts survive the archive. `schedule --install` adds a weekly cron entry (WSL on Windows). Thresholds live in `house.json`.

### 4.11 Codex
Claude Code is the source of truth; Codex gets generated files: `python3 adapters/codex.py` writes `AGENTS.md`, `.codex/agents/*.toml` (the 13 roles), `.codex/hooks.json`, `.codex/config.toml` and `.agents/skills/` (the 10 house skills). Open the repo in Codex, trust the project hooks once with `/hooks`, and invoke skills with `$setup`, `$production`, `$observe`, `$reel-factory`... (`AGENTS.md` has the command map). The format follows OpenAI's current Codex docs; I found no product called "Codex 2", so if you mean something newer, `adapters/codex.py` is the one file to adjust. Differences: Codex agent files have no tool restrictions (each role's limits are written into its instructions instead of enforced), and the exact hook payload fields Codex sends are assumed to match Claude's. CI fails if the generated files go stale.

## 5. How it learns

```
you ask  ->  house picks a style  ->  build + gates  ->  run logged  ->  your next message = the verdict
                  ^                                                              |
                  +---- rules promoted from repeated corrections  <--------------+
```

- **Ledger** (`ledger/runs.jsonl`, private and git-ignored): one record per video with style, effects, gate results, minutes and your verdict (`approved`, `corrected`, `rejected`).
- **Score**: `python3 ledger/house.py score` shows approval per style and per effect. Effects are only blamed when a correction names them (`--tags fx:vertigo`).
- **Autonomy per style**: a style starts at `propose` (it shows you the plan before building). After 3 approvals in a row and at least 3 verdicts in the last 10, it goes `auto` and builds straight through. One correction drops it back.
- **Rules**: a correction tag that appears twice is flagged; promote it with `python3 ledger/house.py promote <style> "<rule>"`. It lands in `styles/<style>/RULES.md` and is read as law next time.
- **Lessons**: free-text learnings go to `ledger/LEARNINGS.md` (house) and each workspace's `LEARNINGS.md` (per brand).

Record a verdict by hand: `python3 ledger/house.py verdict last corrected "fonts are off" --tags font`.

### Hooks (`.claude/settings.json`)
| Hook | What it does |
|---|---|
| SessionStart | prints the scoreboard, the open run and repeated mistakes |
| PreToolUse (Bash) | blocks `git add` of renders/media and `rm` on `assets/ ledger/ styles/ engine/` |
| PostToolUse (Bash) | flags a finished render as unlogged |
| Stop | blocks ending the turn until the render is logged |

---

## 6. Repository map

```
.claude/skills/   house (director) · video-editing · reel-factory · carousel-factory · brand-onboard
                  style-forge · debrief · vox-skill · vox-editing · earshot · real-sound · youtube-transcript
.claude/commands/ /make /video-edit /reel /carousel /brand /debrief /forge-style /vox-edit /omni-reel
brands/           one folder per product (BRAND.md, brand.json, STRATEGY.md, workflow.json) · NICHES.md · _template · example-travel · example-agency
engine/           footage pipeline: ingest, cut, matte, render, gates, QC, doctor
effects/          17 named effects + the beat-type selection table (EFFECTS.md)
styles/           looks: vox, vox-film, beatcut, carousel, html-teaser, trend-recreate (+ INDEX.md)
reels/            reel engine (make/render/song/voice), FORMATS.md, `rf` runner, teaser template
carousel/         carousel engine (kc.mjs, gen.mjs), template, fonts, `cf` runner
assets/           cached sound effects and music loops
ledger/           house.py (ledger, metrics, report), job.py (jobs, gates, QC cap), home.py (data home, isolation), init.py, clean.py (cleanup), cap.py (capabilities), runs.example.jsonl, LEARNINGS.md
hooks/            guard, mark, stop
adapters/         codex.py: generates the Codex version from .claude/
SETUP.md          the guided first run (also `/setup`)
(your data lives outside the repo, in the data home: brands/, workspaces/, library/, ledger/, archive/)
```

---

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `doctor.sh` says NOT READY | read the FAIL line; most are `brew install ...` or `xcode-select --install` |
| Playwright Chromium download stalls | expected; the house prefers an installed Edge or Chrome and only falls back to the bundled Chromium |
| Render hangs at the end | Edge can hang on close after long runs; the scripts exit explicitly, rerun only the failed scene |
| Carousel render writes nothing | no browser found or sandboxed: set `BROWSER=/path/to/chrome-or-edge`; run `node engine/browser.cjs` to see what is detected |
| `onnxruntime` will not install | your Python is too new; recreate the venv with 3.12: `rm -rf .venv && PYTHON=python3.12 bash engine/doctor.sh` |
| Plate effects / cut-outs fail on Linux or WSL | `.venv/bin/pip install -r requirements-seg.txt`; the model downloads from GitHub on first use |
| Chromium fails in WSL/Docker | `npx playwright install --with-deps chromium` |
| Captions show boxes for non-Latin text | pick a font with the script's glyphs (Noto, Hind Siliguri); never letter-space Hindi or Bengali |
| ffmpeg `adelay` ignored on mp4 audio | decode to WAV first |
| `drawtext` missing | this ffmpeg has no freetype; all text goes through the HTML render |
| Stop hook keeps blocking | log the run: `python3 ledger/house.py log '{"style":"vox","video":"name"}'` |
| More traps | `docs/ENV.md` and `ledger/LEARNINGS.md` |

---

## 8. Docs
[`docs/WORKFLOW.md`](docs/WORKFLOW.md) the crew and its research · [`docs/ROLES.md`](docs/ROLES.md) adding and inventing roles · [`docs/OBSERVER.md`](docs/OBSERVER.md) strategy, metrics and the install policy · [`docs/ENV.md`](docs/ENV.md) render traps · [`reels/FORMATS.md`](reels/FORMATS.md) the 16 reel formats.

## 9. Open source

MIT, see `LICENSE`. Third-party material and its licences: `NOTICE.md`. **Before you publish a fork**, read `assets/README.md`: the bundled sounds were generated with ElevenLabs and their redistribution rights are unconfirmed.
Your data home (runs, brands, workspaces) is yours and lives outside the repo, so the same repo trains differently for everyone.
Contributing: `CONTRIBUTING.md` (a style, an effect, or a lesson).
