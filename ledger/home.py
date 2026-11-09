#!/usr/bin/env python3
"""Where the house keeps YOUR data, separate from the engine repo.
  home.py data                  the data home: $HOUSE_HOME, else the path in ~/.config/video-house/home, else this repo (legacy)
  home.py new-brand <name>      scaffold <data>/brands/<name>/ from brands/_template (BRAND, STRATEGY, CONTEXT, workflow, refs, prompts/)
  home.py refs <brand>          the other repos/folders linked to this brand (read-only unless marked write)
  home.py use <brand>|--clear   set the ACTIVE brand: the guard hook then blocks reading or writing any other brand's files
  home.py active
  home.py selftest
Layout of the data home:  house.json · brands/<b>/ · workspaces/<b>/ · library/ (shared, reusable) · ledger/ (runs, capabilities) · archive/
Isolation: one product's tone, context, prompts, repos and files are never visible while another brand is active.
"""
import json, os, re, shutil, sys, tempfile

ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POINTER = os.path.expanduser("~/.config/video-house/home")
SHARED = ("_template",)  # engine-shipped brand folders (_template, example-*) are readable from any brand


def data():
    p = os.environ.get("HOUSE_HOME")
    if not p and os.path.isfile(POINTER):
        p = open(POINTER).read().strip()
    return os.path.expanduser(p) if p else ENGINE


def brand_dir(b):
    """The user's brand in the data home first, then an engine-shipped example/template."""
    for root in (data(), ENGINE):
        d = os.path.join(root, "brands", b)
        if os.path.isdir(d):
            return d
    return os.path.join(data(), "brands", b)


def refs(b):
    f = os.path.join(brand_dir(b), "refs.json")
    return json.load(open(f)).get("refs", []) if os.path.isfile(f) else []


def new_brand(b):
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,30}", b):
        sys.exit("brand name: lowercase kebab-case")
    d = os.path.join(data(), "brands", b)
    if os.path.exists(d):
        sys.exit(f"{d} exists")
    shutil.copytree(os.path.join(ENGINE, "brands", "_template"), d)
    bj = os.path.join(d, "brand.json")
    j = json.load(open(bj))
    j["name"] = b
    json.dump(j, open(bj, "w"), indent=2)
    print(d)


def _active():
    return os.path.join(data(), ".active-brand")


def use(b):
    if b == "--clear":
        if os.path.exists(_active()):
            os.remove(_active())
        return print("active brand cleared")
    if not os.path.isdir(brand_dir(b)):
        sys.exit(f"no brand {b}")
    open(_active(), "w").write(b)
    print("active brand:", b)


def active():
    return open(_active()).read().strip() if os.path.isfile(_active()) else None


def other_brand_paths(me):
    """Paths that belong to brands other than `me`: their folders, workspaces and linked repos."""
    out = []
    root = os.path.join(data(), "brands")
    for b in (os.listdir(root) if os.path.isdir(root) else []):
        if b == me or b in SHARED or b.startswith("example-"):
            continue
        out += [os.path.join(root, b), os.path.join(data(), "workspaces", b)]
        out += [os.path.realpath(os.path.expanduser(r["path"])) for r in refs(b)]
    mine = [os.path.realpath(os.path.expanduser(r["path"])) for r in refs(me)] if me else []
    return [p for p in out if p not in mine]


def selftest():
    os.environ["HOUSE_HOME"] = tempfile.mkdtemp()
    for b in ("alpha", "beta"):
        new_brand(b)
    json.dump({"refs": [{"path": "/tmp/beta-repo", "purpose": "app", "mode": "read"}]}, open(os.path.join(brand_dir("beta"), "refs.json"), "w"))
    use("alpha")
    assert active() == "alpha"
    bad = other_brand_paths("alpha")
    assert os.path.join(data(), "brands", "beta") in bad and os.path.realpath("/tmp/beta-repo") in bad
    assert os.path.join(data(), "brands", "alpha") not in bad, "own brand must stay open"
    assert brand_dir("example-travel").startswith(ENGINE), "engine examples are shared"
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:] or ["selftest"]
    {"data": lambda: print(data()), "new-brand": lambda: new_brand(a[1]), "refs": lambda: print(json.dumps(refs(a[1]), indent=1)),
     "use": lambda: use(a[1]), "active": lambda: print(active() or ""), "selftest": selftest}[a[0]]()
