#!/usr/bin/env python3
"""Capability registry: skills, plugins, MCP connectors and tools the house might add. Nothing is installed without the user's yes.
  cap.py add <name> <kind> <source> "<the gap it fills>"     status=proposed  (kind: skill|plugin|mcp|tool)
  cap.py vet <name> "<finding>" [--risk low|medium|high]     record what you read (SKILL.md, scripts, permissions, publisher, update date)
  cap.py approve <name> "<the user's words>"                 ONLY after the user said yes in chat; unlocks the install command
  cap.py installed <name> | reject <name> "<why>"
  cap.py list [status]
  cap.py allowed <command>                                   exit 0 if an install command is covered by an approved capability (the hook uses this)
Vet checklist before proposing: publisher and update date · read every SKILL.md and bundled script · hooks and commands it adds ·
network calls and what data leaves the machine · does it fetch content at runtime (prompt-injection surface) · can it post, delete or spend ·
pin a version, never track a moving branch. Anything that can publish, delete or spend stays draft-only until the user clicks.
"""
import json, os, re, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import home as _home

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = lambda: os.path.join(_home.data(), "ledger", "capabilities.json")
SEED = lambda: os.path.join(HOME, "ledger", "capabilities.json")  # engine-shipped proposals, copied to the data home on first use
STATUS = ["proposed", "approved", "installed", "rejected"]


def load():
    f = F() if os.path.exists(F()) else SEED()
    return json.load(open(f)) if os.path.exists(f) else {}


def save(d):
    os.makedirs(os.path.dirname(F()), exist_ok=True)
    json.dump(d, open(F(), "w"), indent=1)


def need(d, n):
    if n not in d:
        sys.exit(f"unknown capability {n}")
    return d[n]


def add(n, kind, src, gap):
    d = load()
    if kind not in ("skill", "plugin", "mcp", "tool"):
        sys.exit("kind: skill|plugin|mcp|tool")
    d[n] = {"kind": kind, "source": src, "gap": gap, "status": "proposed", "risk": "unvetted", "vet": [], "added": time.strftime("%Y-%m-%d")}
    save(d)
    print("proposed", n)


def vet(n, finding, risk=None):
    d = load()
    c = need(d, n)
    c["vet"].append(finding)
    if risk:
        c["risk"] = risk
    save(d)
    print(n, "risk:", c["risk"])


def approve(n, words):
    d = load()
    c = need(d, n)
    if c["risk"] == "unvetted":
        sys.exit("vet it first: read the skill and its scripts, record findings with `vet`")
    if len(words.strip()) < 2:
        sys.exit("pass the user's actual words")
    c.update(status="approved", approved_by_user=words, approved=time.strftime("%Y-%m-%d"))
    save(d)
    print("approved", n)


def setstatus(n, st, why=""):
    d = load()
    c = need(d, n)
    if st == "installed" and c["status"] != "approved":
        sys.exit("not approved")
    c["status"] = st
    if why:
        c["why"] = why
    save(d)


def allowed(cmd):
    return any(c["status"] == "approved" and re.search(re.escape(n), cmd) for n, c in load().items())


def lst(st=None):
    for n, c in load().items():
        if not st or c["status"] == st:
            print(f"{n:<26}{c['kind']:<8}{c['status']:<10}risk={c['risk']:<9}{c['gap']}")


def selftest():
    global HOME
    HOME = tempfile.mkdtemp()
    os.environ["HOUSE_HOME"] = HOME
    os.makedirs(os.path.join(HOME, "ledger"))
    add("demo-mcp", "mcp", "https://example.com", "scheduling")
    assert not allowed("claude mcp add demo-mcp https://example.com"), "unapproved must not be allowed"
    try:
        approve("demo-mcp", "yes"); raise AssertionError("must vet before approval")
    except SystemExit:
        pass
    vet("demo-mcp", "read manifest: 7 tools, can schedule and delete posts, OAuth only", "medium")
    approve("demo-mcp", "yes install it")
    assert allowed("claude mcp add demo-mcp https://example.com") and not allowed("claude mcp add other https://x")
    setstatus("demo-mcp", "installed")
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    c = a[0] if a else "selftest"
    if c == "add": add(*a[1:5])
    elif c == "vet": vet(a[1], a[2], a[a.index("--risk") + 1] if "--risk" in a else None)
    elif c == "approve": approve(a[1], a[2])
    elif c == "installed": setstatus(a[1], "installed")
    elif c == "reject": setstatus(a[1], "rejected", a[2] if len(a) > 2 else "")
    elif c == "list": lst(*(a[1:2]))
    elif c == "allowed": sys.exit(0 if allowed(" ".join(a[1:])) else 1)
    else: selftest()
