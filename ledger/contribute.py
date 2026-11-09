#!/usr/bin/env python3
"""Send generic improvements back to the shared repo as clean pull requests, without ever sending your data.
  contribute.py check [--base upstream/main]       the privacy and quality gate (also run by CI on fork PRs). Exit 1 + reasons.
  contribute.py propose <slug> "<title>" <file>... branch contrib/<slug> from upstream/main with ONLY those files, check, commit, push to your fork
        [--open --why "<evidence, anonymised>"]    then open a DRAFT pull request upstream (only if house.json contribute != off)
        [--yes]                                    required with --open when contribute is "ask": pass it ONLY after the user said yes
  contribute.py status                             contributions made from this data home
  contribute.py selftest
What may be contributed: skills, agents, workflow, engine, effects, styles, docs, adapters, hooks, scripts, brands/_template and brands/example-*.
What never leaves your machine: assets and media (any binary), brands/<yours>, workspaces, library, archive, ledger runs, house.json, .env,
keys, personal paths and emails. Workflow files under .github/ are maintainer-only.
Modes in house.json "contribute": "ask" (default: the agent prepares the PR and asks once), "auto" (opens a DRAFT PR itself after the check passes), "off".
"""
import json, os, re, subprocess, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import home as H

# CONTRIB_REPO lets CI run this TRUSTED script (from the base branch) against an untrusted PR checkout
ROOT = os.environ.get("CONTRIB_REPO") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPSTREAM_REPO = "rocker1166/video-production-house"
ALLOW = (".claude/skills/", ".claude/agents/", ".claude/commands/", "engine/", "effects/", "reels/", "carousel/", "styles/", "hooks/", "adapters/",
         "docs/", ".codex/", ".agents/", "brands/_template/", "brands/example-", "ledger/", ".gitignore")
ALLOW_FILES = ("README.md", "SETUP.md", "CLAUDE.md", "AGENTS.md", "CONTRIBUTING.md", "install.sh", "requirements.txt", "requirements-seg.txt", ".env.example")
FORBID_PATH = re.compile(r"^(workspaces|archive|library)/|^house\.json$|(^|/)\.env$|^ledger/(runs\.jsonl|observer\.json|clean\.log|\.unlogged|\.active-brand)$|^brands/(?!_template|example-)|^\.github/workflows/")
SECRET = re.compile(r"sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|xox[bpa]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY|(API_KEY|TOKEN|SECRET)\s*=\s*['\"]?[A-Za-z0-9_\-]{16,}")
PERSONAL = re.compile(r"/Users/(?!<|\$|you\b|name\b|me\b|x\b)[A-Za-z0-9._-]+|/home/(?!runner\b|<|\$|you\b|name\b|me\b|x\b)[A-Za-z0-9._-]+|[A-Za-z]:\\Users\\|[\w.+-]+@(?!example\.|noreply|users\.noreply)[\w-]+\.[\w.]+")
MAX_LINES, MAX_FILE = 1500, 300_000
TESTS = [["ledger/house.py", "selftest"], ["ledger/job.py", "selftest"], ["ledger/cap.py", "selftest"], ["ledger/home.py", "selftest"],
         ["ledger/clean.py", "selftest"], ["ledger/init.py", "selftest"], ["adapters/codex.py", "--check"]]


def git(*a, cwd=None, check=True):
    r = subprocess.run(["git", *a], cwd=cwd or ROOT, capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f"git {' '.join(a)}: {r.stderr.strip()}")
    return r.stdout


def mode():
    f = os.path.join(H.data(), "house.json")
    return (json.load(open(f)).get("contribute", "ask") if os.path.isfile(f) else "ask")


def problems(diffargs, cwd=None, run_tests=True):
    out = []
    names = git("diff", "--name-status", *diffargs, cwd=cwd).splitlines()
    files = [l.split("\t")[-1] for l in names if l]
    for f in files:
        if FORBID_PATH.search(f):
            out.append(f"{f}: never leaves your machine (user data, secrets or maintainer-only)")
        elif not (f.startswith(ALLOW) or f in ALLOW_FILES):
            out.append(f"{f}: outside the allowed areas (skills, agents, workflow, engine, effects, styles, docs, adapters, hooks, scripts, brand templates)")
    for l in git("diff", "--numstat", *diffargs, cwd=cwd).splitlines():
        a, d, f = l.split("\t", 2)
        if a == "-":
            out.append(f"{f}: binary or media file (assets are never contributed)")
        elif os.path.isfile(os.path.join(cwd or ROOT, f)) and os.path.getsize(os.path.join(cwd or ROOT, f)) > MAX_FILE:
            out.append(f"{f}: larger than {MAX_FILE // 1000} KB")
    added, cur = 0, ""
    for l in git("diff", "-U0", *diffargs, cwd=cwd).splitlines():
        if l.startswith("+++ "):
            cur = l[6:]
        elif l.startswith("+") and not l.startswith("+++"):
            added += 1
            if SECRET.search(l):
                out.append(f"{cur}: looks like a secret or key")
            m = PERSONAL.search(l)
            if m:
                out.append(f"{cur}: personal path or email ({m.group(0)[:30]})")
    if added > MAX_LINES:
        out.append(f"{added} added lines (limit {MAX_LINES}): split it into smaller PRs")
    if run_tests and not os.environ.get("CONTRIB_SKIP_TESTS"):
        for t in TESTS:
            if os.path.isfile(os.path.join(cwd or ROOT, t[0])):
                r = subprocess.run([sys.executable, *t], cwd=cwd or ROOT, capture_output=True, text=True, env={**os.environ, "HOUSE_HOME": tempfile.mkdtemp()})
                if r.returncode:
                    out.append(f"{' '.join(t)} fails: {(r.stdout + r.stderr).strip().splitlines()[-1][:120] if (r.stdout + r.stderr).strip() else ''}")
    return sorted(set(out))


SENSITIVE = ("ledger/contribute.py", "hooks/", ".github/", "ledger/cap.py", "ledger/home.py", "engine/build.py")


def check(base):
    changed = git("diff", "--name-only", f"{base}...HEAD").split()
    hot = [f for f in changed if f.startswith(SENSITIVE)]
    if hot:
        print("NOTE security-sensitive files changed (gate, guards, workflows, ship gates): a maintainer must read every line:\n  " + "\n  ".join(hot))
    p = problems([f"{base}...HEAD"])
    print("contribution check: OK" if not p else "contribution check: BLOCKED\n  - " + "\n  - ".join(p))
    return 1 if p else 0


def propose(slug, title, files, open_pr, why, yes):
    if mode() == "off":
        sys.exit("contribute is off in house.json")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,40}", slug):
        sys.exit("slug: lowercase kebab-case")
    start = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    git("fetch", "upstream")
    git("checkout", "-B", f"contrib/{slug}", "upstream/main")  # clean branch: none of your customisations ride along
    try:
        git("checkout", start, "--", *files)
        git("add", "--", *files)
        p = problems(["--cached", "upstream/main"])
        if p:
            git("checkout", start)
            print("BLOCKED, nothing pushed:\n  - " + "\n  - ".join(p))
            return 1
        git("commit", "-m", f"{title}\n\nAdded from a user's fork via contribute.py. No user data included.")
        git("push", "-u", "origin", f"contrib/{slug}", "--force-with-lease")
    finally:
        git("checkout", start, check=False)
    rec = {"ts": time.strftime("%F %T"), "slug": slug, "title": title, "files": files, "pr": None}
    if open_pr:
        if mode() == "ask" and not yes:
            sys.exit("contribute is 'ask': get the user's yes in chat, then re-run with --yes")
        fork = git("remote", "get-url", "origin").strip()
        owner = re.search(r"[:/]([^/:]+)/[^/]+?(?:\.git)?$", fork).group(1)
        body = f"## What and why\n{title}\n\n{why or '(no evidence given)'}\n\n## Checks\n- `contribute.py check`: passed (no assets, no user data, no secrets, tests green)\n- Opened from a fork by an agent; a maintainer reviews before merge.\n"
        r = subprocess.run(["gh", "pr", "create", "--repo", UPSTREAM_REPO, "--draft", "--head", f"{owner}:contrib/{slug}", "--base", "main", "--title", title, "--body", body],
                           capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip())
        rec["pr"] = r.stdout.strip() or None
    else:
        print(f"pushed contrib/{slug} to your fork. To open the draft PR: re-run with --open (--yes if mode is ask).")
    os.makedirs(os.path.join(H.data(), "ledger"), exist_ok=True)
    open(os.path.join(H.data(), "ledger", "contributions.jsonl"), "a").write(json.dumps(rec) + "\n")
    return 0


def status():
    f = os.path.join(H.data(), "ledger", "contributions.jsonl")
    for l in open(f) if os.path.isfile(f) else []:
        r = json.loads(l)
        print(f"{r['ts']}  {r['slug']:<28}{r['pr'] or 'branch pushed, no PR'}")
    print(f"contribute mode: {mode()}")


def selftest():
    tmp = tempfile.mkdtemp()
    sh = lambda *a, cwd=None: subprocess.run(a, cwd=cwd, check=True, capture_output=True, text=True).stdout
    sh("git", "init", "-q", "--bare", "-b", "main", f"{tmp}/up.git")
    sh("git", "init", "-q", "--bare", "-b", "main", f"{tmp}/fork.git")
    w = f"{tmp}/w"
    sh("git", "clone", "-q", f"{tmp}/up.git", w)
    for k, v in (("user.email", "t@example.com"), ("user.name", "t")):
        sh("git", "config", k, v, cwd=w)
    os.makedirs(f"{w}/engine")
    open(f"{w}/engine/a.py", "w").write("x = 1\n")
    sh("git", "-C", w, "add", "."), sh("git", "-C", w, "commit", "-qm", "base"), sh("git", "-C", w, "push", "-q", "origin", "HEAD:main")
    sh("git", "-C", w, "remote", "rename", "origin", "upstream"), sh("git", "-C", w, "remote", "add", "origin", f"{tmp}/fork.git")
    sh("git", "-C", w, "checkout", "-qb", "mine")
    open(f"{w}/engine/a.py", "w").write("x = 2  # a generic improvement\n")
    os.makedirs(f"{w}/brands/acme")
    open(f"{w}/brands/acme/BRAND.md", "w").write("private tone\n")
    # fixtures are assembled at runtime so this file itself never matches the rules it tests
    open(f"{w}/engine/leak.py", "w").write('KEY = "' + "sk" + "-" + "abcdefghijklmnopqrstuvwxyz123456" + '"\n# /' + "Users" + '/someone/Desktop/x\n')
    sh("git", "-C", w, "add", "."), sh("git", "-C", w, "commit", "-qm", "mine")
    # 1. a forbidden or leaking diff is caught
    bad = problems(["upstream/main...HEAD"], cwd=w, run_tests=False)
    assert any("brands/acme" in b for b in bad) and any("secret" in b for b in bad) and any("personal path" in b for b in bad), bad
    # 2. proposing only the clean file works, and leaves the rest behind
    global ROOT
    ROOT = w
    os.environ["CONTRIB_SKIP_TESTS"] = "1"
    os.environ["HOUSE_HOME"] = tempfile.mkdtemp()
    assert propose("better-a", "Improve a", ["engine/a.py"], False, "", False) == 0
    assert "contrib/better-a" in sh("git", "-C", f"{tmp}/fork.git", "branch")
    files = sh("git", "-C", w, "diff", "--name-only", "upstream/main", "origin/contrib/better-a").split()
    assert files == ["engine/a.py"], files
    # 3. proposing a leaking file is refused and nothing is pushed
    assert propose("leaky", "Leak", ["engine/leak.py"], False, "", False) == 1
    assert "contrib/leaky" not in sh("git", "-C", f"{tmp}/fork.git", "branch")
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:] or ["selftest"]
    if a[0] == "check":
        sys.exit(check(a[a.index("--base") + 1] if "--base" in a else "upstream/main"))
    elif a[0] == "propose":
        flags = {"--open", "--yes"}
        rest = [x for x in a[1:] if x not in flags]
        why = rest.pop(rest.index("--why") + 1) if "--why" in rest else ""
        rest = [x for x in rest if x != "--why"]
        sys.exit(propose(rest[0], rest[1], rest[2:], "--open" in a, why, "--yes" in a))
    elif a[0] == "status":
        status()
    else:
        selftest()
