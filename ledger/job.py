#!/usr/bin/env python3
"""A job = one video made by the crew. This script makes the folder, checks the gates, caps the QC loop,
and lets the crew grow: roles live in ledger/roles.json, and the producer can add, invent and promote roles.

  job.py new <brand> <slug> [solo|standard|full | role,role,... | type:<content-type>]   scaffold workspaces/<brand>/jobs/<slug>/
                                                   type: takes crew + success metrics from brands/<brand>/workflow.json
  job.py status <job>                              phase, crew, artifacts present/missing, QC loops used
  job.py gate <job> <intake|develop|prep|build|qc|post>   exit 1 and list what is missing
  job.py qc-loop <job>                             count one QC round; exit 2 after 3: escalate to the human
  job.py faults <job>                              {role: n} from `owner:` tags in review-*.md
  -- adaptive crew --
  job.py roles                                     every known role: builtin, custom, and the unbuilt catalogue (docs/ROLES.md)
  job.py add-role <job> <role>                     put a registered role on this job's crew
  job.py adhoc <job> <name> <phase> <artifact> "<what it does>"   invent a one-off role for THIS job: writes <job>/roles/<name>.md
  job.py promote <job> <name>                      turn a job's ad-hoc role into a permanent agent (.claude/agents + registry)
  job.py selftest
Gates check FILES, not opinions: an artifact must exist, be non-empty and contain no TODO/<placeholder>.
"""
import json, os, re, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import home as _home

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = lambda: os.path.join(HOME, "ledger", "roles.json")
CREWS = {  # presets only; a job may list any roles. The producer is the main session; the toolsmith always runs after delivery.
    "solo": ["scriptwriter", "cinematographer", "editor", "qc-picture"],
    "standard": ["scriptwriter", "storyboarder", "asset-wrangler", "sound-designer", "cinematographer", "editor", "qc-picture", "qc-audio"],
    "full": ["researcher", "scriptwriter", "art-director", "storyboarder", "asset-wrangler", "sound-designer", "cinematographer", "editor", "qc-picture", "qc-audio"],
}
JOB_PHASES = ["develop", "prep", "build", "qc", "post"]
PHASE_LIST = JOB_PHASES + ["meta"]  # meta = observer and capability-scout: they work outside any single job
COMMON = ("You work inside one video job folder (path given in your brief). Read `brief.md` first: it is the shared vision and the success "
          "criteria. Write ONLY your own artifact file (named below); never edit another role's file or the repo. Keep it short and concrete. "
          "If something is missing from the brief, say so at the top of your file under `## Questions` instead of guessing. Mark anything "
          "unverified as `unverified`. Final reply to the producer: the file path plus at most 5 lines.")
BRIEF = """# Brief: {slug}
Brand: {brand} · Crew: {crew} · Created: {ts}

## Objective (one sentence: what should the viewer do or feel)
TODO

## Audience and platform
TODO (who, where it plays, length in seconds, caption zone)

## Message, hook idea, CTA allowed
TODO

## Claims that must NOT appear
TODO (copy from brands/{brand}/BRAND.md and add job-specific ones)

## Success criteria (QC judges against exactly these; 3-5, each checkable)
- TODO

## Constraints
Approver: the user · Human revision rounds: 2 · Internal QC loops: max 3 · Budget (money/time): TODO

## Inputs given (files, links, references)
TODO

## Decisions log (producer only; every role added or invented goes here with its one-line reason)
"""


def registry():
    return json.load(open(REG()))


def save_registry(r):
    json.dump(r, open(REG(), "w"), indent=1)


def jobdir(p):
    return p if os.path.isabs(p) else os.path.join(_home.data(), p)


def load(d):
    return json.load(open(os.path.join(d, "job.json")))


def save(d, j):
    json.dump(j, open(os.path.join(d, "job.json"), "w"), indent=1)


def roleinfo(j, role):
    """phase + artifact for a role: ad-hoc roles of this job first, then the registry."""
    return j.get("adhoc", {}).get(role) or registry().get(role)


def content_type(brand, name):
    """A content type (hook, story, proof, offer...) from brands/<brand>/workflow.json: crew, success metrics, notes."""
    f = os.path.join(_home.brand_dir(brand), "workflow.json")
    if not os.path.isfile(f):
        sys.exit(f"no {f}: run the observer's strategy mode, or copy brands/_template/workflow.json")
    t = json.load(open(f)).get("content_types", {})
    if name not in t:
        sys.exit(f"unknown content type {name}; this brand has: {sorted(t)}")
    return t[name]


def new(brand, slug, crew="standard"):
    ctype = None
    if crew.startswith("type:"):
        ctype = crew[5:]
        spec = content_type(brand, ctype)
        crew = spec.get("crew", "standard")
    roles = CREWS.get(crew) or [r.strip() for r in crew.split(",") if r.strip()]
    unknown = [r for r in roles if r not in registry()]
    if unknown:
        sys.exit(f"unknown role(s) {unknown}. Known: {sorted(registry())}. Invent one with `adhoc` after creating the job.")
    d = os.path.join(_home.data(), "workspaces", brand, "jobs", slug)
    os.makedirs(os.path.join(d, "out"), exist_ok=True)
    os.makedirs(os.path.join(d, "assets"), exist_ok=True)
    ts = time.strftime("%Y-%m-%d")
    brief = BRIEF.format(slug=slug, brand=brand, crew=crew if crew in CREWS else "custom", ts=ts)
    bd = _home.brand_dir(brand)
    files = [f for f in ("BRAND.md", "CONTEXT.md", "STRATEGY.md", "workflow.json") if os.path.isfile(os.path.join(bd, f))]
    brief += "\n## Brand files (read these; they are the ONLY brand material you may use)\n" + "".join(f"- {os.path.join(bd, f)}\n" for f in files)
    brief += f"- per-role additions: {os.path.join(bd, 'prompts')}/<your-role>.md (if it exists)\n"
    for r in _home.refs(brand):
        brief += f"- linked repo ({r.get('mode', 'read')}-only): {os.path.expanduser(r['path'])} : {r.get('purpose', '')}\n"
    if ctype:
        sp = content_type(brand, ctype)
        brief += f"\n## Content type: {ctype}\nFunnel role: {sp.get('funnel','?')} · Purpose: {sp.get('purpose','')}\nMeasure after posting: {', '.join(sp.get('metrics', []))}\nNotes: {sp.get('notes','')}\n"
    open(os.path.join(d, "brief.md"), "w").write(brief)
    open(os.path.join(_home.data(), ".active-brand"), "w").write(brand)  # isolation follows the job
    save(d, {"brand": brand, "slug": slug, "crew": crew if crew in CREWS else "custom", "type": ctype, "roles": roles, "adhoc": {}, "qc_loops": 0, "created": ts})
    print(d)


def real(path):
    if not os.path.isfile(path) or os.path.getsize(path) < 40:
        return False
    return not re.search(r"\bTODO\b|<[a-z][a-z -]*>", open(path, errors="ignore").read())


def crew(j):
    return [r for r in j["roles"] + list(j.get("adhoc", {})) + ["toolsmith"] if roleinfo(j, r)]


def missing(d, phase):
    j = load(d)
    if phase == "intake":
        b = os.path.join(d, "brief.md")
        return [] if real(b) and "- TODO" not in open(b).read() else ["brief.md (fill every TODO)"]
    roles = [r for r in dict.fromkeys(crew(j)) if roleinfo(j, r)["phase"] == phase]
    out = [roleinfo(j, r)["artifact"] for r in roles if not real(os.path.join(d, roleinfo(j, r)["artifact"]))]
    if phase == "build":
        if not (os.path.isdir(os.path.join(d, "out")) and os.listdir(os.path.join(d, "out"))):
            out.append("out/ (a render or slides)")
        log = os.path.join(d, "edit-log.md")
        if os.path.isfile(log) and "PASS" not in open(log, errors="ignore").read():
            out.append("edit-log.md must contain the gate output with PASS")
    if phase == "qc":  # any role in the qc phase (built-in or invented) is judged the same way
        for r in roles:
            f = os.path.join(d, roleinfo(j, r)["artifact"])
            if os.path.isfile(f):
                t = open(f, errors="ignore").read()
                if re.search(r"^\W*\[blocker\]", t, re.M | re.I):
                    out.append(f"{os.path.basename(f)} has blockers: fix and run qc-loop")
                if not re.search(r"\bPASS\b", t) or re.search(r"\bREVISE\b", t.split("PASS")[-1]):
                    out.append(f"{os.path.basename(f)} verdict is not PASS")
    return out


def gate(d, phase):
    m = missing(d, phase)
    print(("GATE " + phase + ": OK") if not m else "GATE " + phase + ": NOT READY\n  - " + "\n  - ".join(m))
    return 0 if not m else 1


def status(d):
    j = load(d)
    print(f"{j['brand']}/{j['slug']} crew={j['crew']} qc_loops={j['qc_loops']}/3")
    for r in dict.fromkeys(crew(j)):
        i = roleinfo(j, r)
        tag = " (ad-hoc)" if r in j.get("adhoc", {}) else ""
        print(f"  {'ok ' if real(os.path.join(d, i['artifact'])) else '-- '}{r:<16}{i['phase']:<8}{i['artifact']}{tag}")


def qc_loop(d):
    j = load(d)
    j["qc_loops"] += 1
    save(d, j)
    if j["qc_loops"] > 3:
        print("QC loop limit (3) reached: stop fixing, show the user what is left and ask.")
        return 2
    print(f"qc loop {j['qc_loops']}/3")
    return 0


def faults(d):
    c = {}
    j = load(d)
    for r in crew(j):
        i = roleinfo(j, r)
        p = os.path.join(d, i["artifact"])
        if i["phase"] == "qc" and os.path.isfile(p):
            for m in re.finditer(r"owner:\s*([a-z0-9-]+)", open(p, errors="ignore").read()):
                c[m.group(1)] = c.get(m.group(1), 0) + 1
    print(json.dumps(c))


def roles():
    reg = registry()
    for k, v in sorted(reg.items(), key=lambda kv: (PHASE_LIST.index(kv[1]["phase"]), kv[0])):
        print(f"{k:<18}{v['phase']:<8}{v['artifact']:<20}{v['kind']}" + (f"  ({v['why']})" if v.get("why") else ""))
    cat = os.path.join(HOME, "docs", "ROLES.md")
    if os.path.isfile(cat):
        names = re.findall(r"^\| `([a-z0-9-]+)` \|", open(cat).read(), re.M)
        print("catalogue, not built yet (create with `adhoc` then `promote`): " + ", ".join(n for n in names if n not in reg))


def add_role(d, role):
    j = load(d)
    if role not in registry():
        sys.exit(f"unknown role {role}; see `job.py roles`, or invent it with `adhoc`")
    if role not in j["roles"]:
        j["roles"].append(role)
        save(d, j)
    print(f"{role} added to {j['slug']}")


def adhoc(d, name, phase, artifact, what):
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,30}", name):
        sys.exit("role name: lowercase kebab-case, 3-31 chars")
    if phase not in JOB_PHASES or not artifact.endswith(".md"):
        sys.exit(f"phase must be one of {JOB_PHASES}; artifact must be a .md file")
    j = load(d)
    if name in registry():
        sys.exit(f"{name} already exists as a registered role: use add-role")
    j.setdefault("adhoc", {})[name] = {"phase": phase, "artifact": artifact, "kind": "adhoc", "why": what}
    save(d, j)
    os.makedirs(os.path.join(d, "roles"), exist_ok=True)
    open(os.path.join(d, "roles", name + ".md"), "w").write(
        f"# Role card: {name}\nWhy this job needs it: {what}\n\n{COMMON}\nArtifact: `{artifact}`.\n\n"
        f"Do: <the producer writes the specific duties here: inputs to read, what to produce, what 'done' means>\n"
        f"Rules: <what this role must never do; any measurable check it must run>\n")
    print(f"ad-hoc role {name}: edit {d}/roles/{name}.md, then dispatch a general-purpose agent (model haiku) told to follow that card.")


def promote(d, name):
    j = load(d)
    info = j.get("adhoc", {}).get(name)
    card = os.path.join(d, "roles", name + ".md")
    if not info or not os.path.isfile(card):
        sys.exit(f"no ad-hoc role {name} on this job")
    body = open(card).read()
    if re.search(r"<the producer writes|<what this role", body):
        sys.exit("fill in the role card before promoting it")
    agent = os.path.join(HOME, ".claude", "agents", name + ".md")
    if os.path.exists(agent):
        sys.exit(f"{agent} exists")
    tools = "Read, Write, Glob, Grep" + (", WebSearch, WebFetch" if info["phase"] == "develop" else "") + (", Bash, Edit" if info["phase"] in ("build", "post") else "")
    desc = f"{info['why']}. Added after use on a real job; writes {info['artifact']}."
    open(agent, "w").write(f"---\nname: {name}\ndescription: {desc}\ntools: {tools}\nmodel: haiku\n---\n" + body.split("\n", 2)[2].lstrip())
    reg = registry()
    reg[name] = {"phase": info["phase"], "artifact": info["artifact"], "kind": "custom", "why": info["why"], "added": time.strftime("%Y-%m-%d")}
    save_registry(reg)
    print(f"promoted {name}: {agent}  (restart Claude Code in the repo to load the new agent type; review the tools line)")


def selftest():
    global HOME
    real_reg = open(REG()).read()
    HOME = tempfile.mkdtemp()
    os.environ["HOUSE_HOME"] = HOME  # data home = temp too
    os.makedirs(os.path.join(HOME, "ledger"))
    open(REG(), "w").write(real_reg)
    os.makedirs(os.path.join(HOME, ".claude", "agents"))
    d = os.path.join(HOME, "workspaces", "b", "jobs", "s")
    new("b", "s", "solo")
    assert gate(d, "intake") == 1, "template brief must not pass"
    open(os.path.join(d, "brief.md"), "w").write("# Brief\n" + "real content line here\n" * 4)
    assert gate(d, "intake") == 0
    assert gate(d, "develop") == 1, "scriptwriter artifact missing"
    open(os.path.join(d, "script.md"), "w").write("hook and beats " * 10)
    assert gate(d, "develop") == 0
    open(os.path.join(d, "review-picture.md"), "w").write("[blocker] [t=1s] bad caption -> fix | owner: editor\nREVISE\n")
    assert gate(d, "qc") == 1, "blocker must stop QC"
    for _ in range(3):
        assert qc_loop(d) == 0
    assert qc_loop(d) == 2, "4th loop must escalate"
    open(os.path.join(d, "review-picture.md"), "w").write("[minor] [t=2s] nit -> fix | owner: scriptwriter\nPASS\n")
    assert gate(d, "qc") == 0
    # adaptive crew: add a registered role, invent one, gate on it, promote it
    add_role(d, "researcher")
    assert gate(d, "develop") == 1, "added role must be gated"
    open(os.path.join(d, "research.md"), "w").write("findings with sources " * 6)
    assert gate(d, "develop") == 0
    adhoc(d, "color-grader", "build", "grade.md", "the footage mixes three cameras and needs a matched look")
    assert gate(d, "build") == 1 and "grade.md" in "\n".join(missing(d, "build")), "ad-hoc role must be gated"
    try:
        promote(d, "color-grader"); raise AssertionError("unfilled card must not promote")
    except SystemExit:
        pass
    p = os.path.join(d, "roles", "color-grader.md")
    card = open(p).read().replace("<the producer writes the specific duties here: inputs to read, what to produce, what 'done' means>", "match shots A and B to the hero shot, log LUT choices").replace("<what this role must never do; any measurable check it must run>", "never crush blacks; report mean luma per shot")
    open(p, "w").write(card)
    promote(d, "color-grader")
    assert os.path.isfile(os.path.join(HOME, ".claude", "agents", "color-grader.md")) and "color-grader" in registry()
    new("b", "t", "scriptwriter,editor")
    os.makedirs(os.path.join(HOME, "brands", "b"), exist_ok=True)
    json.dump({"content_types": {"hook": {"crew": "solo", "funnel": "awareness", "purpose": "reach", "metrics": ["sends/1k", "3s hold"]}}}, open(os.path.join(HOME, "brands", "b", "workflow.json"), "w"))
    new("b", "u", "type:hook")
    assert load(os.path.join(HOME, "workspaces", "b", "jobs", "u"))["type"] == "hook" and "sends/1k" in open(os.path.join(HOME, "workspaces", "b", "jobs", "u", "brief.md")).read()
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    c = a[0] if a else "selftest"
    if c == "new":
        new(a[1], a[2], *(a[3:4]))
    elif c == "selftest":
        selftest()
    elif c == "roles":
        roles()
    elif c == "adhoc":
        adhoc(jobdir(a[1]), a[2], a[3], a[4], a[5])
    elif c == "add-role":
        add_role(jobdir(a[1]), a[2])
    elif c == "promote":
        promote(jobdir(a[1]), a[2])
    else:
        d = jobdir(a[1])
        sys.exit({"status": lambda: status(d), "gate": lambda: gate(d, a[2]), "qc-loop": lambda: qc_loop(d), "faults": lambda: faults(d)}[c]() or 0)
