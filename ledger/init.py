#!/usr/bin/env python3
"""Create or update the data home (the one folder that holds every product, project and run).
  init.py <path> [--runtime claude|codex|both]    make <path>/{brands,workspaces,library,ledger,archive} + house.json, remember the path
  init.py merge '<json>'                          merge answers into house.json (owner, goals, platforms, cleanup, limits, runtime...)
  init.py show                                    print house.json
  init.py selftest
The pointer ~/.config/video-house/home lets every script find the data home from any folder. HOUSE_HOME overrides it.
"""
import json, os, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import home as H

DEFAULT = {"owner": {}, "runtime": "claude", "goals": [], "platforms": [], "posts_per_week": None,
           "cleanup": {"regen_days": 14, "archive_days": 45, "max_gb": 20, "weekly_schedule": False},
           "limits": {"max_parallel_agents": 6, "image_budget_usd_per_job": 2}, "posting": "draft-only, the owner publishes",
           "contribute": "ask", "upstream": "rocker1166/video-production-house", "fork": None}


def cfg():
    return os.path.join(H.data(), "house.json")


def deep(a, b):
    for k, v in b.items():
        a[k] = deep(a.get(k, {}), v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return a


def init(path, runtime="claude"):
    path = os.path.abspath(os.path.expanduser(path))
    for d in ("brands", "workspaces", "library", "ledger", "archive"):
        os.makedirs(os.path.join(path, d), exist_ok=True)
    f = os.path.join(path, "house.json")
    if not os.path.isfile(f):
        json.dump({**DEFAULT, "runtime": runtime, "created": time.strftime("%Y-%m-%d")}, open(f, "w"), indent=2)
    if not os.environ.get("HOUSE_HOME"):
        os.makedirs(os.path.dirname(H.POINTER), exist_ok=True)
        open(H.POINTER, "w").write(path)
    open(os.path.join(path, ".gitignore"), "a").write("") if not os.path.exists(os.path.join(path, ".gitignore")) else None
    print("data home:", path)


def merge(raw):
    j = json.load(open(cfg())) if os.path.isfile(cfg()) else dict(DEFAULT)
    json.dump(deep(j, json.loads(raw)), open(cfg(), "w"), indent=2)
    print(open(cfg()).read())


def selftest():
    os.environ["HOUSE_HOME"] = tempfile.mkdtemp()
    init(os.environ["HOUSE_HOME"], "codex")
    merge('{"goals":["grow my agency"],"cleanup":{"archive_days":30}}')
    j = json.load(open(cfg()))
    assert j["runtime"] == "codex" and j["goals"] == ["grow my agency"] and j["cleanup"]["archive_days"] == 30 and j["cleanup"]["regen_days"] == 14
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:] or ["selftest"]
    if a[0] == "merge": merge(a[1])
    elif a[0] == "show": print(open(cfg()).read())
    elif a[0] == "selftest": selftest()
    else: init(a[0], a[a.index("--runtime") + 1] if "--runtime" in a else "claude")
