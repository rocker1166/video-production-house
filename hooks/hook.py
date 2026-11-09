#!/usr/bin/env python3
"""House hooks for Claude Code and Codex (same JSON on stdin; exit 2 = block, stderr = the reason).
  guard  PreToolUse: no media into git, no wiping engine memory, no unapproved installs, BRAND ISOLATION
  mark   PostToolUse(Bash): a final compose/render ran -> <data>/ledger/.unlogged (cleared by house.py log)
  stop   Stop: a render happened and nothing was logged -> block once, say what to do
Isolation: when a brand is active (`ledger/home.py use <brand>`), any tool call that touches another brand's folder, workspace or
linked repo is blocked, and Edit/Write into this brand's read-only linked repos is blocked. shortcut: Bash is checked by path
substring only, so a determined `cd` trick gets through; the briefs also give each role only its own brand's paths.
"""
import json, os, re, subprocess, sys

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HOME, "ledger"))
import home as H

DIRTY = lambda: os.path.join(H.data(), "ledger", ".unlogged")
MEDIA = r"\.(mp4|mov|m4v|wav|mp3|png|jpg|jpeg|webm)\b"
KEEP = ("assets/", "styles/", "effects/examples", "docs/")  # media that is meant to live in git
INSTALL = r"claude\s+(mcp\s+add|plugin\s+(install|add|marketplace\s+add))|npx\s+\S*skills?\S*\s+add|\bgit\s+clone\b.*[/-]skills?\b"
WRITERS = {"Edit", "Write", "apply_patch", "NotebookEdit", "MultiEdit"}


def inside(path, root):
    path, root = os.path.realpath(os.path.expanduser(path)), os.path.realpath(os.path.expanduser(root))
    return path == root or path.startswith(root + os.sep)


def isolation(tool, ti):
    me = H.active()
    if not me:
        return None
    others = H.other_brand_paths(me)
    paths = [ti.get(k) for k in ("file_path", "path", "notebook_path") if ti.get(k)]
    for p in paths:
        if any(inside(p, o) for o in others):
            return f"Brand isolation: the active brand is '{me}'. {p} belongs to another product. Switch with `python3 ledger/home.py use <brand>` if the user asked for that."
        if tool in WRITERS:
            for r in H.refs(me):
                if r.get("mode", "read") != "write" and inside(p, r["path"]):
                    return f"{r['path']} is linked to '{me}' read-only. Ask the user before changing their repo."
    cmd = ti.get("command") or ti.get("cmd") or ""
    for o in others:
        if o in cmd or o.replace(os.path.expanduser("~"), "~") in cmd:
            return f"Brand isolation: that command touches another product's files ({o}); the active brand is '{me}'."
    return None


def guard(p):
    ti = p.get("tool_input") or {}
    cmd = ti.get("command") or ti.get("cmd") or ""
    why = isolation(p.get("tool_name", ""), ti)
    if why:
        return why
    if re.search(r"\bgit\s+add\b", cmd) and re.search(MEDIA + r"|\s(-A|--all|\.)(\s|$)", cmd) and not any(k in cmd for k in KEEP):
        return "Media stays out of git (lean repos). Stage code and docs by name; renders live in work/ and out/."
    if re.search(INSTALL, cmd) and subprocess.run([sys.executable, os.path.join(HOME, "ledger", "cap.py"), "allowed", cmd]).returncode != 0:
        return ("Installing a skill, plugin or connector needs the user's yes. Propose it with `ledger/cap.py add`, vet it (`cap.py vet`), "
                "ask the user, then record their words with `cap.py approve <name> \"<words>\"`. Third-party skills are a prompt-injection and supply-chain risk.")
    if re.search(r"\brm\s+-\w*[rf]\w*\s+.*\b(assets|ledger|styles|engine|brands|archive|library)\b", cmd):
        return "Refusing to delete the house's memory (assets, ledger, styles, engine, brands, library, archive). Use `ledger/clean.py`, or ask the user first."
    return None


def mark(p):
    cmd = (p.get("tool_input") or {}).get("command", "")
    if re.search(r"build\.py\s+\S+\s+compose|render\.cjs", cmd) and "stills" not in cmd:
        os.makedirs(os.path.dirname(DIRTY()), exist_ok=True)
        open(DIRTY(), "w").close()


def stop(p):
    if p.get("stop_hook_active") or not os.path.exists(DIRTY()):
        return None
    return ("A render finished but the run is not in the ledger. Run "
            "`python3 ledger/house.py log '<json>'` (style, video, effects, gates, minutes) "
            "and say in one line that the user's next message is its verdict.")


if __name__ == "__main__":
    p = json.load(sys.stdin)
    why = {"guard": guard, "mark": mark, "stop": stop}[sys.argv[1]](p)
    if why:
        print(why, file=sys.stderr)
        sys.exit(2)
