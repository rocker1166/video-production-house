#!/usr/bin/env python3
"""The house ledger: one record per video, a verdict per record, rules earned from repeats.

  house.py log '<json>'                      new run  {style, video, effects[], gates{}, minutes, faults{role:n}, job, note}
  house.py verdict <id|last> approved|corrected|rejected ["note"] [--tags a,b,fx:vertigo]
  house.py score                             approval per style and per effect, autonomy level per style
  house.py rules                             tags that repeat in corrections -> candidate rules
  house.py promote <style> "<rule>"          append an earned rule to styles/<style>/RULES.md
  house.py metrics <id|last> '<json>'        attach what the AUDIENCE did: {views, avg_watch_s, completion, sends, saves, likes, follows, leads}
  house.py report                            per style and content type: sends/1k, saves/1k, completion (the observer reads this)
  house.py observed                          mark the observer's report as done (resets its cadence counter)
  house.py brief                             what SessionStart shows (scoreboard, open runs, rules)
  house.py selftest

Autonomy per style (a graduated-autonomy rule): `propose` until 3 approvals in a row AND
>=3 verdicts in the last 10 runs, then `auto` (go straight to the build, show only at the ship gate).
Any correction/rejection drops it back to `propose`.
Tags: `fx:<effect>` blames an effect; any other tag names a repeatable mistake (e.g. `font`, `sync`).
"""
import json, os, sys, time, collections, tempfile

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.environ.get("HOUSE_LEDGER", os.path.join(HOME, "ledger", "runs.jsonl"))
DIRTY = os.path.join(HOME, "ledger", ".unlogged")  # set by the render hook, cleared by `log`


def load():
    if not os.path.exists(LEDGER):
        return []
    return [json.loads(l) for l in open(LEDGER) if l.strip()]


def save(rows):
    with open(LEDGER, "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)


def log(raw):
    r = json.loads(raw)
    if not r.get("style"):
        sys.exit("log needs a style")
    rows = load()
    r.setdefault("id", "r%03d" % (len(rows) + 1))
    r.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
    r.setdefault("effects", [])
    r["outcome"] = r.get("outcome", "pending")
    rows.append(r)
    save(rows)
    if os.path.exists(DIRTY):
        os.remove(DIRTY)
    print("logged", r["id"])


def verdict(args):
    tags = []
    if "--tags" in args:
        i = args.index("--tags")
        tags = [t for t in args[i + 1].split(",") if t]
        args = args[:i] + args[i + 2:]
    rid, out = args[0], args[1]
    note = args[2] if len(args) > 2 else ""
    if out not in ("approved", "corrected", "rejected"):
        sys.exit("verdict must be approved|corrected|rejected")
    rows = load()
    row = rows[-1] if rid == "last" else next((r for r in rows if r["id"] == rid), None)
    if not row:
        sys.exit("no such run")
    row.update(outcome=out, feedback=note, tags=tags)
    save(rows)
    print(row["id"], "->", out)


def level(rows):
    done = [r for r in rows if r["outcome"] in ("approved", "corrected", "rejected")]
    streak = 0
    for r in reversed(done):
        if r["outcome"] != "approved":
            break
        streak += 1
    verdicts_in_last10 = sum(1 for r in rows[-10:] if r["outcome"] != "pending")
    return "auto" if streak >= 3 and verdicts_in_last10 >= 3 else "propose"


def stats():
    rows = load()
    by_style = collections.defaultdict(list)
    for r in rows:
        by_style[r["style"]].append(r)
    fx = collections.defaultdict(lambda: [0, 0])  # [credit, blame]
    for r in rows:
        blamed = {t[3:] for t in r.get("tags", []) if t.startswith("fx:")}
        for e in r["effects"]:
            if r["outcome"] == "approved":
                fx[e][0] += 1
            if e in blamed:
                fx[e][1] += 1
    return rows, by_style, fx


def score():
    rows, by_style, fx = stats()
    print("STYLE            runs  appr  corr  rej  pend  level")
    for s, rs in sorted(by_style.items()):
        c = collections.Counter(r["outcome"] for r in rs)
        print(f"{s:<16} {len(rs):>4}  {c['approved']:>4}  {c['corrected']:>4}  {c['rejected']:>3}  {c['pending']:>4}  {level(rs)}")
    ff = collections.Counter()
    for r in rows:
        ff.update(r.get("faults", {}))
    if ff:
        print("ROLE             faults   (rewrite the prompt of a role that keeps topping this list)")
        for role, n in ff.most_common():
            print(f"{role:<16} {n:>6}")
    if fx:
        print("EFFECT           credit  blame")
        for e, (a, b) in sorted(fx.items(), key=lambda kv: -kv[1][0]):
            print(f"{e:<16} {a:>6}  {b:>5}")


def repeated():
    seen = collections.defaultdict(list)
    for r in load():
        if r["outcome"] in ("corrected", "rejected"):
            for t in r.get("tags", []):
                seen[t].append((r["id"], r["style"], r.get("feedback", "")))
    return {t: v for t, v in seen.items() if len(v) >= 2}


def rules():
    hits = repeated()
    if not hits:
        print("no tag has repeated yet")
    for t, v in hits.items():
        print(f"[{t}] x{len(v)}: " + " | ".join(f"{i} {s}: {n}" for i, s, n in v))
    return hits


def metrics(rid, raw):
    rows = load()
    row = rows[-1] if rid == "last" else next((r for r in rows if r["id"] == rid), None)
    if not row:
        sys.exit("no such run")
    row["metrics"] = {**row.get("metrics", {}), **json.loads(raw)}
    save(rows)
    print(row["id"], "metrics", row["metrics"])


def report():
    rows = [r for r in load() if r.get("metrics", {}).get("views")]
    if not rows:
        print("no run has audience metrics yet: house.py metrics <id> '{\"views\":..,\"sends\":..,\"saves\":..}'")
        return
    g = collections.defaultdict(list)
    for r in rows:
        g[(r["style"], r.get("type") or "-")].append(r["metrics"])
    print("STYLE / TYPE                    n  sends/1k  saves/1k  likes/1k  completion  (n<5 is anecdote, not evidence)")
    for (st, ty), ms in sorted(g.items()):
        per = lambda k: sum(m.get(k, 0) / m["views"] * 1000 for m in ms) / len(ms)
        comp = [m["completion"] for m in ms if "completion" in m]
        print(f"{st + ' / ' + ty:<30}{len(ms):>3}  {per('sends'):>8.1f}  {per('saves'):>8.1f}  {per('likes'):>8.1f}  {(sum(comp) / len(comp) if comp else float('nan')):>9.2f}")


OBS = os.path.join(HOME, "ledger", "observer.json")


def observer_due(n_runs):
    last = json.load(open(OBS))["runs_at_last"] if os.path.exists(OBS) else 0
    return n_runs - last >= 5


def observed():
    json.dump({"runs_at_last": len(load()), "ts": time.strftime("%Y-%m-%d")}, open(OBS, "w"))
    print("observer cadence reset at", len(load()), "runs")


def promote(style, rule):
    d = os.path.join(HOME, "styles", style)
    if not os.path.isdir(d):
        sys.exit("no such style: " + style)
    with open(os.path.join(d, "RULES.md"), "a") as f:
        f.write(f"- {rule}  _(earned {time.strftime('%Y-%m-%d')})_\n")
    print("promoted into styles/%s/RULES.md" % style)


def brief():
    rows, by_style, _ = stats()
    out = ["VIDEO HOUSE. Read CLAUDE.md. Route every video request through the `house` skill."]
    if by_style:
        out.append("Styles: " + ", ".join(f"{s} [{level(rs)}, {len(rs)} runs]" for s, rs in sorted(by_style.items())))
    pend = [r for r in rows if r["outcome"] == "pending"]
    if pend:
        out.append("Open (needs a verdict; the user's next message is it): " + ", ".join(f"{r['id']} {r['style']}" for r in pend[-5:]))
    if os.path.exists(DIRTY):
        out.append("WARNING: a render ran last session and was never logged. Run `house.py log` before anything new.")
    if rows and observer_due(len(rows)):
        out.append("OBSERVER DUE: 5+ runs since the last systems review. Run `/observe` (needs audience metrics on recent runs for it to be worth it).")
    for t, v in repeated().items():
        out.append(f"Repeated correction [{t}] x{len(v)}: promote it to a rule (`house.py promote <style> \"...\"`).")
    print("\n".join(out))


def selftest():
    global LEDGER
    LEDGER = os.path.join(tempfile.mkdtemp(), "runs.jsonl")
    for i in range(3):
        log(json.dumps({"style": "t", "effects": ["vertigo"]}))
        verdict(["last", "approved"])
    assert level(load()) == "auto", "3 approvals should graduate"
    log(json.dumps({"style": "t", "effects": ["orbit"]}))
    verdict(["last", "corrected", "too busy", "--tags", "fx:orbit,busy"])
    assert level(load()) == "propose", "a correction must demote"
    log(json.dumps({"style": "t", "effects": ["orbit"]}))
    verdict(["last", "corrected", "again", "--tags", "busy"])
    assert "busy" in repeated(), "a repeated tag must surface"
    log(json.dumps({"style": "t", "faults": {"editor": 2}}))
    assert load()[-1]["faults"]["editor"] == 2
    metrics("last", '{"views": 1000, "sends": 30, "saves": 20, "completion": 0.4}')
    assert load()[-1]["metrics"]["sends"] == 30
    assert observer_due(5) and not observer_due(4), "cadence is every 5 runs"
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    cmd = a[0] if a else "score"
    {"log": lambda: log(a[1]), "verdict": lambda: verdict(a[1:]), "score": score, "rules": rules,
     "promote": lambda: promote(a[1], a[2]), "brief": brief, "selftest": selftest,
     "metrics": lambda: metrics(a[1], a[2]), "report": report, "observed": observed}[cmd]()
