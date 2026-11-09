#!/usr/bin/env python3
"""Generate the Codex CLI version of this repo from the single source in .claude/ (Claude Code is the source of truth).
  codex.py            write AGENTS.md, .codex/agents/*.toml, .codex/hooks.json, .codex/config.toml, .agents/skills/*
  codex.py --check    exit 1 if the generated files are stale (CI uses this)
  codex.py --all      also copy the vendored third-party skills (vox-skill, earshot, real-sound, ...)
Formats follow OpenAI's Codex docs (checked 2026-11-09): AGENTS.md; skills in .agents/skills/<name>/SKILL.md (name + description);
custom agents in .codex/agents/<name>.toml (name, description, developer_instructions); hooks in .codex/hooks.json with the same
event names and exit-2 blocking. There is no `tools` field in a Codex agent file, so each role's tool limit is written into its
instructions instead of being enforced. Hooks must be trusted once with /hooks. shortcut: the hook JSON field names Codex sends are
assumed to match Claude's (tool_input.command / file_path); hooks/hook.py also accepts `cmd`. Change this file, not the outputs.
"""
import glob, json, os, re, shutil, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWN = ("house", "production", "observe", "brand-onboard", "reel-factory", "carousel-factory", "video-editing", "style-forge", "debrief", "setup")
PREAMBLE = """# AGENTS.md (generated for Codex from CLAUDE.md; edit `.claude/` and run `python3 adapters/codex.py`)

**Codex notes.** Slash commands are Claude Code's; here invoke skills with `$name` (for example `$production`, `$observe`, `$setup`, `$reel-factory`). The role agents live in `.codex/agents/*.toml`: to use one, ask Codex to spawn the named agent with a short brief (cap parallel agents with `max_concurrent_threads_per_session` in `.codex/config.toml`; set `default_subagent_model` there to a cheaper model for the craft roles). Codex agent files cannot restrict tools, so each role's allowed tools are written into its instructions: obey them. Project hooks (`.codex/hooks.json`) must be reviewed and trusted once with `/hooks`. `HOUSE_ROOT` below means the repo root (`git rev-parse --show-toplevel`); run scripts from there. Command map: /make=$house, /produce=$production, /observe=$observe, /brand=$brand-onboard, /reel=$reel-factory, /carousel=$carousel-factory, /video-edit=$video-editing, /setup=$setup, /debrief=$debrief, /forge-style=$style-forge.

"""


def fm(path):
    t = open(path).read()
    _, head, body = t.split("---", 2)
    d = {}
    for line in head.strip().splitlines():
        k, _, v = line.partition(":")
        d[k.strip()] = v.strip()
    return d, body.strip()


def toml_agent(path):
    d, body = fm(path)
    tools = d.get("tools", "")
    instr = (f"You are the `{d['name']}` role on the video house crew. Claude's version of this role is limited to these tools: {tools}. "
             f"Codex cannot enforce that, so stay within it: roles that only review must not edit files; every role writes only its own artifact file.\n\n" + body)
    assert "'''" not in instr, path
    return f"name = {json.dumps(d['name'])}\ndescription = {json.dumps(d['description'])}\ndeveloper_instructions = '''\n{instr}\n'''\n"


HOOKS = {"hooks": {
    "SessionStart": [{"matcher": "startup|resume", "hooks": [{"type": "command", "command": 'python3 "$(git rev-parse --show-toplevel)/ledger/house.py" brief'}]}],
    "PreToolUse": [{"matcher": "Bash|apply_patch|Edit|Write", "hooks": [{"type": "command", "command": 'python3 "$(git rev-parse --show-toplevel)/hooks/hook.py" guard'}]}],
    "PostToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": 'python3 "$(git rev-parse --show-toplevel)/hooks/hook.py" mark'}]}],
    "Stop": [{"hooks": [{"type": "command", "command": 'python3 "$(git rev-parse --show-toplevel)/hooks/hook.py" stop'}]}]}}


def build(out, everything):
    os.makedirs(f"{out}/.codex/agents", exist_ok=True)
    for f in sorted(glob.glob(f"{ROOT}/.claude/agents/*.md")):
        open(f"{out}/.codex/agents/{os.path.basename(f)[:-3]}.toml", "w").write(toml_agent(f))
    open(f"{out}/.codex/hooks.json", "w").write(json.dumps(HOOKS, indent=2) + "\n")
    open(f"{out}/.codex/config.toml", "w").write("[agents]\nmax_concurrent_threads_per_session = 6\n")
    for d in sorted(glob.glob(f"{ROOT}/.claude/skills/*/")):
        n = os.path.basename(d.rstrip("/"))
        if n in OWN or everything:
            shutil.copytree(d, f"{out}/.agents/skills/{n}", dirs_exist_ok=True)
            p = f"{out}/.agents/skills/{n}/SKILL.md"
            open(p, "w").write(open(p).read().replace("$CLAUDE_PROJECT_DIR", "$HOUSE_ROOT"))
    open(f"{out}/AGENTS.md", "w").write(PREAMBLE + open(f"{ROOT}/CLAUDE.md").read().replace("$CLAUDE_PROJECT_DIR", "$HOUSE_ROOT"))


def tree(p):
    return {os.path.relpath(os.path.join(r, f), p): open(os.path.join(r, f), "rb").read() for r, _, fs in os.walk(p) for f in fs}


if __name__ == "__main__":
    everything = "--all" in sys.argv
    if "--check" in sys.argv:
        tmp = tempfile.mkdtemp()
        build(tmp, everything)
        want, stale = tree(tmp), []
        for k, v in want.items():
            f = os.path.join(ROOT, k)
            if not os.path.isfile(f) or open(f, "rb").read() != v:
                stale.append(k)
        print("codex files in sync" if not stale else "STALE (run python3 adapters/codex.py): " + ", ".join(stale[:8]))
        sys.exit(1 if stale else 0)
    build(ROOT, everything)
    print("wrote AGENTS.md, .codex/ and .agents/skills/ for Codex")
