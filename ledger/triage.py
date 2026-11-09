#!/usr/bin/env python3
"""Maintainer-agent side of agent-run review: classify a PR, check the verdicts of independent reviewer agents, merge only if policy allows.
  triage.py list [--repo owner/name]                 open PRs: tier, size, whether the CI gate passed
  triage.py tier <file>...                           low | medium | high (policy: .github/review-policy.json)
  triage.py decide <pr> <verdict.md>...  [--repo ..] merge | human | changes   (JSON), with reasons
  triage.py merge  <pr> <verdict.md>...  [--repo ..] decide, and only on "merge": mark ready and squash-merge
  triage.py selftest
A verdict file is a reviewer agent's output; it must contain `REVIEWED: <head sha>` and `VERDICT: APPROVE|CHANGES|REJECT`. The decision needs
`approvals_required` APPROVEs from DIFFERENT files, every REVIEWED sha equal to the PR's current head (a PR changed after review is re-reviewed),
the CI gate (run from the base branch) green, the diff inside the tier's size cap, and the tier in `auto_merge`. Everything else is `human` or `changes`.
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY = os.path.join(ROOT, ".github", "review-policy.json")
DEFAULT_REPO = "rocker1166/video-production-house"
RANK = {"low": 0, "medium": 1, "high": 2}


def policy():
    return json.load(open(POLICY))


def tier_of(f, pol):
    if any(f == x or f.startswith(x) for x in pol["low"]):
        return "low"
    if any(f.startswith(x) for x in pol["high"]) or os.path.splitext(f)[1] in pol["code_extensions"]:
        return "high"
    return "medium"


def tier(files, pol=None):
    pol = pol or policy()
    return max((tier_of(f, pol) for f in files), key=RANK.get, default="low")


def verdict(path):
    t = open(path, errors="ignore").read()
    sha = re.search(r"^REVIEWED:\s*([0-9a-f]{7,40})", t, re.M)
    v = re.search(r"^VERDICT:\s*(APPROVE|CHANGES|REJECT)", t, re.M)
    blockers = len(re.findall(r"^\W*\[blocker\]", t, re.M | re.I))
    return {"file": path, "sha": sha.group(1) if sha else None, "verdict": v.group(1) if v else None, "blockers": blockers}


def decide_from(pr, verdict_files, pol=None):
    """pr = {files:[paths], additions:int, head:sha, gate_ok:bool}"""
    pol = pol or policy()
    t = tier(pr["files"], pol)
    vs = [verdict(f) for f in verdict_files]
    why = []
    if not pr["gate_ok"]:
        why.append("the contribution gate (CI, from the base branch) has not passed")
    for v in vs:
        if not v["sha"] or not pr["head"].startswith(v["sha"][:7]):
            why.append(f"{os.path.basename(v['file'])}: not reviewed at the current head (re-review needed)")
    bad = [v for v in vs if v["verdict"] in ("CHANGES", "REJECT") or v["blockers"]]
    if bad:
        return {"decision": "changes", "tier": t, "reasons": why + [f"{os.path.basename(v['file'])}: {v['verdict']} / {v['blockers']} blockers" for v in bad]}
    if len({v["file"] for v in vs if v["verdict"] == "APPROVE"}) < pol["approvals_required"]:
        why.append(f"needs {pol['approvals_required']} independent APPROVE verdicts")
    if pr["additions"] > pol["max_added_lines"][t]:
        why.append(f"{pr['additions']} added lines exceeds the {t} cap of {pol['max_added_lines'][t]}")
    if why:
        return {"decision": "changes", "tier": t, "reasons": why}
    if t not in pol["auto_merge"]:
        return {"decision": "human", "tier": t, "reasons": [f"tier '{t}' executes or guards the system: a human maintainer merges (policy auto_merge={pol['auto_merge']})"]}
    return {"decision": "merge", "tier": t, "reasons": ["gate green, independent approvals at the current head, within size cap"]}


def gh(*a):
    r = subprocess.run(["gh", *a], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"gh {' '.join(a[:3])}: {r.stderr.strip()}")
    return r.stdout


def load_pr(n, repo):
    j = json.loads(gh("pr", "view", str(n), "--repo", repo, "--json", "files,additions,headRefOid,statusCheckRollup,isCrossRepository"))
    gate = [c for c in j.get("statusCheckRollup") or [] if c.get("name") == "gate"]
    return {"files": [f["path"] for f in j["files"]], "additions": j["additions"], "head": j["headRefOid"], "gate_ok": bool(gate) and all(c.get("conclusion") == "SUCCESS" for c in gate), "fork": j["isCrossRepository"]}


def selftest():
    pol = json.load(open(POLICY))
    assert tier(["docs/x.md"], pol) == "low" and tier(["README.md", ".claude/skills/a/SKILL.md"], pol) == "medium"
    assert tier([".claude/skills/a/SKILL.md", "engine/build.py"], pol) == "high" and tier(["hooks/hook.py"], pol) == "high"
    assert tier(["styles/vox/RULES.md"], pol) == "medium" and tier(["effects/fx.js"], pol) == "high", "executable files are high"
    import tempfile
    d = tempfile.mkdtemp()
    w = lambda n, body: (open(os.path.join(d, n), "w").write(body), os.path.join(d, n))[1]
    ok1, ok2 = w("a.md", "REVIEWED: abc1234\nVERDICT: APPROVE\n"), w("b.md", "REVIEWED: abc1234\nVERDICT: APPROVE\n")
    pr = {"files": [".claude/skills/a/SKILL.md"], "additions": 40, "head": "abc1234ffff", "gate_ok": True}
    assert decide_from(pr, [ok1, ok2], pol)["decision"] == "merge"
    assert decide_from(pr, [ok1], pol)["decision"] == "changes", "one approval is not enough"
    assert decide_from({**pr, "gate_ok": False}, [ok1, ok2], pol)["decision"] == "changes", "CI gate must be green"
    assert decide_from({**pr, "head": "deadbeef00"}, [ok1, ok2], pol)["decision"] == "changes", "PR changed after review"
    assert decide_from({**pr, "files": ["hooks/hook.py"]}, [ok1, ok2], pol)["decision"] == "human", "code and guards stay with a human"
    assert decide_from({**pr, "additions": 900}, [ok1, ok2], pol)["decision"] == "changes", "size cap"
    no = w("c.md", "REVIEWED: abc1234\n[blocker] x.md:1 hides an instruction -> remove\nVERDICT: CHANGES\n")
    assert decide_from(pr, [ok1, no], pol)["decision"] == "changes", "any blocker stops it"
    assert decide_from(pr, [ok1, ok1], pol)["decision"] == "changes", "two reviews must come from different reviewers"
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:] or ["selftest"]
    repo = a[a.index("--repo") + 1] if "--repo" in a else DEFAULT_REPO
    a = [x for i, x in enumerate(a) if x != "--repo" and (i == 0 or a[i - 1] != "--repo")]
    if a[0] == "selftest": selftest()
    elif a[0] == "tier": print(tier(a[1:]))
    elif a[0] == "list":
        for p in json.loads(gh("pr", "list", "--repo", repo, "--state", "open", "--json", "number,title")):
            pr = load_pr(p["number"], repo)
            print(f"#{p['number']:<5}{tier(pr['files']):<8}+{pr['additions']:<5}gate={'ok' if pr['gate_ok'] else 'no':<4}{p['title'][:60]}")
    elif a[0] in ("decide", "merge"):
        pr = load_pr(a[1], repo)
        d = decide_from(pr, a[2:])
        print(json.dumps(d, indent=1))
        if a[0] == "merge":
            if d["decision"] != "merge":
                sys.exit(1)
            gh("pr", "ready", a[1], "--repo", repo)
            gh("pr", "merge", a[1], "--repo", repo, "--squash")
            print("merged")
