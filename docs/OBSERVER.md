# The observer: a node that watches the whole system

The crew in `WORKFLOW.md` makes one video well. Nobody in it asks **whether this is the right video, or whether the system is getting better at serving the goal.** That is the observer's job. It works at two altitudes, and it only proposes.

## Why it exists
A real studio has a head of strategy and a pipeline lead above the production crew: strategy decides what to make and why, the pipeline lead fixes the way work flows. Without them a crew becomes efficient at the wrong thing. "Grow my agency" is not a brief; it implies which content types, what proof, which metrics, and which tools, and those differ completely from "sell my app".

## Mode 1: Strategy (understand the need)
Input: the user's goal in their words, the offer, their stage. Output: `brands/<brand>/STRATEGY.md` and `workflow.json`, which `job.py new ... type:<content-type>` then uses to set the crew, brief metrics and success criteria. Method (what the research supports):
- **Funnel mapping.** Content types map to awareness, consideration and conversion; guidance is 3-5 pillars tied to the value proposition and validated before committing; a 60/30/10 split is a starting heuristic, not a benchmark; metrics follow the stage (reach and engagement for awareness, depth and sign-ups for consideration, attributable leads for conversion) and vanity metrics are named and ignored ([Brandwatch](https://www.brandwatch.com/blog/content-pillars/), [Tenspeed](https://www.tenspeed.io/blog/content-marketing-funnel), [Blueprint, agency pipeline content](https://ai.theblueprint.training/content-marketing-for-agencies/)). That short-form video is awareness and proof content is trust is an inference, not a sourced finding, and the observer labels it so.
- **Reach mechanics.** Instagram's head named watch time, likes per reach and sends per reach as the top Reels signals, per secondary sources; newer signals (replay rate, two-way conversation, saves and shares) are disputed and unverified ([Hootsuite](https://blog.hootsuite.com/instagram-algorithm/), [Virlo](https://virlo.ai/blog/instagram-reels-algorithm-2026-decoded), [CreatorFlow](https://creatorflow.so/blog/instagram-algorithm-2026)). Consequence for building: openings that hold 3 seconds and content worth sending to one specific person.
- **Hooks and story.** Design the first 1-3 seconds around an open loop, close it at the end, and stack 2-3 loops under 30 seconds; the usual structure is hook, setup, escalation, payoff ([Hook engineering](https://dev.to/bulkdl/hook-engineering-the-science-of-the-first-3-seconds-in-short-form-video-2026-2jp9), [Open loops](https://www.socialync.io/blog/open-loops-in-content-2026)). The numbers in these sources are vendor claims; treat as defaults to test.
- **The agency twist.** Trust is usually the bottleneck, so missing proof (cases, numbers, permission) is the first thing to produce. None of the sources addressed agency founders directly; this is the observer's inference to test in the first experiments.

## Mode 2: Systems (improve the workflow)
Every ~5 runs the session brief says **OBSERVER DUE**. The observer reads the ledger, job postmortems, QC faults per role, the user's corrections and, crucially, **audience metrics** attached with `house.py metrics`. It reports: evidence per style and content type with `n`, where time and QC loops went, whether the mix still matches the goal, ranked proposals, an automation map and capability requests. Under 5 posts per cell is anecdote and is reported as such.
Why metrics matter: the user's "looks good" measures taste; reach measures the audience. Without `metrics` the house can become excellent at pleasing one reviewer.

## Capabilities (the scout)
The `capability-scout` looks for skills, plugins, connectors and tools for each named gap and vets them. First scan (2026-11-09, registry search; **none vetted or installed**) is in `ledger/capabilities.json`: `metricool` (analytics, best time to post, scheduled posts), `vidiq` (trending videos and outliers, keyword research), `elevenlabs-mcp` (voice and sound), `supermetrics` (cross-platform analytics, social scheduling), `analytics-skills` (reading funnels without causal mistakes). Posting connectors exist (Metricool, Typefully, Windsor.ai, Supermetrics, Orshot); the house will use them **draft-only**.

### Install policy (a hard rule)
Third-party skills are instructions that run with the agent's authority, so a poisoned one can steer the agent while looking legitimate; plugins can also bundle hooks, subagents and MCP servers, and many pass untrusted web and social content into the model ([SKILL-INJECT, arXiv](https://arxiv.org/pdf/2602.20156v3), [Claude Code threat model](https://articles.firstaimovers.com/articles/claude-code-threat-model-hooks-mcp-skills-untrusted-repos/); secondary sources, no single authoritative checklist exists). So:
1. **Propose** (`cap.py add`), **vet** (read the SKILL.md and every script, list tools and which can write, post, delete or spend, what data leaves, runtime fetching, publisher, update date; record with `cap.py vet`), **ask the user**, **record their words** (`cap.py approve`), only then install, pinned to a version.
2. The guard hook **blocks** `claude mcp add`, `claude plugin install` and similar unless the capability is approved.
3. Anything that can publish stays **draft-only**; the user clicks publish. The house never posts.
4. Capabilities earn their keep: the observer reviews each one's use at the next review and proposes removing the ones that did not help.

## What the observer may not do
Edit the engine, agent prompts, `workflow.json` or the ledger itself; install anything; post anything; recommend loosening a gate; or conclude from fewer than 5 posts. It proposes with evidence and the user decides.
