#!/usr/bin/env python3
"""Three house hooks, one file. Reads the hook JSON on stdin; exit 2 = block, stderr = the reason.
  guard  PreToolUse(Bash): no media into git (lean repos), no wiping assets/ ledger/ styles/
  mark   PostToolUse(Bash): a final compose/render ran -> ledger/.unlogged (cleared by house.py log)
  stop   Stop: a render happened and nothing was logged -> block once, say what to do
"""
import json, os, re, sys

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRTY = os.path.join(HOME, "ledger", ".unlogged")
MEDIA = r"\.(mp4|mov|m4v|wav|mp3|png|jpg|jpeg|webm)\b"
KEEP = ("assets/", "styles/", "effects/examples", "docs/")  # media that is meant to live in git


def guard(cmd):
    if re.search(r"\bgit\s+add\b", cmd) and re.search(MEDIA + r"|\s(-A|--all|\.)(\s|$)", cmd) \
            and not any(k in cmd for k in KEEP):
        return "Media stays out of git (lean repos). Stage code and docs by name; renders live in work/ and out/."
    if re.search(INSTALL, cmd):
        import subprocess
        if subprocess.run([sys.executable, os.path.join(HOME, "ledger", "cap.py"), "allowed", cmd]).returncode != 0:
            return ("Installing a skill, plugin or connector needs the user's yes. Propose it with `ledger/cap.py add`, vet it (`cap.py vet`), "
                    "ask the user, then record their words with `cap.py approve <name> \"<words>\"`. Third-party skills are a prompt-injection and supply-chain risk.")
    if re.search(r"\brm\s+-\w*[rf]\w*\s+.*\b(assets|ledger|styles|engine)\b", cmd):
        return "Refusing to delete assets/ ledger/ styles/ engine/. They are the house's memory; ask the user first."
    return None


INSTALL = r"claude\s+(mcp\s+add|plugin\s+(install|add|marketplace\s+add))|npx\s+\S*skills?\S*\s+add|\bgit\s+clone\b.*[/-]skills?\b"


def mark(cmd):
    if re.search(r"build\.py\s+\S+\s+compose|render\.cjs", cmd) and "stills" not in cmd:
        open(DIRTY, "w").close()


def stop(payload):
    if payload.get("stop_hook_active") or not os.path.exists(DIRTY):
        return None
    return ("A render finished but the run is not in the ledger. Run "
            "`python3 ledger/house.py log '<json>'` (style, video, effects, gates, minutes) "
            "and say in one line that the user's next message is its verdict.")


if __name__ == "__main__":
    p = json.load(sys.stdin)
    cmd = (p.get("tool_input") or {}).get("command", "")
    why = {"guard": lambda: guard(cmd), "mark": lambda: mark(cmd), "stop": lambda: stop(p)}[sys.argv[1]]()
    if why:
        print(why, file=sys.stderr)
        sys.exit(2)
