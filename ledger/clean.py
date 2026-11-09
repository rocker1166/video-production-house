#!/usr/bin/env python3
"""Keep the data home small without losing anything that matters. Dry-run unless you say otherwise.
  clean.py report                    disk use per brand and job, and what a run would do
  clean.py run [--apply-safe]        DRY RUN by default. --apply-safe does ONLY the reversible, regenerable classes below
  clean.py restore <brand> <slug>    unpack an archived job
  clean.py harvest                   copy the reusable parts of APPROVED jobs into <data>/library/ (scripts, hooks, plans, lessons)
  clean.py schedule [--install]      print the weekly cron line (or add it: persistent config, so only when the user asked)
  clean.py selftest
Classes (policy in <data>/house.json "cleanup", defaults below):
  regenerable  directories the engine rebuilds: plates/, frames/, tmp/, qc_zoom/, *-stills/, __pycache__/  -> deleted after `regen_days`
  archive      a finished job folder untouched for `archive_days` -> <data>/archive/<brand>/<slug>.tar.gz, original removed ONLY after the
               archive is verified; briefs, scripts, reviews and postmortems are kept inside it. Restorable.
  report-only  everything else (clips, songs, finals, brands, library, ledger). Never touched here; a human decides.
Never follows symlinks, never leaves the data home, never touches brands/, library/, ledger/ or a linked repo.
"""
import json, os, shutil, sys, tarfile, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import home as H

DEFAULT = {"regen_days": 14, "archive_days": 45, "max_gb": 20}
REGEN = ("plates", "frames", "tmp", "qc_zoom", "__pycache__")
DAY = 86400


def policy():
    f = os.path.join(H.data(), "house.json")
    return {**DEFAULT, **(json.load(open(f)).get("cleanup", {}) if os.path.isfile(f) else {})}


def size(p):
    t = 0
    for r, ds, fs in os.walk(p, followlinks=False):
        t += sum(os.lstat(os.path.join(r, f)).st_size for f in fs if not os.path.islink(os.path.join(r, f)))
    return t


def age(p):
    m = 0
    for r, ds, fs in os.walk(p, followlinks=False):
        for f in fs + ds:
            try:
                m = max(m, os.lstat(os.path.join(r, f)).st_mtime)
            except OSError:
                pass
    return (time.time() - (m or os.path.getmtime(p))) / DAY


def safe(p):
    rp = os.path.realpath(p)
    root = os.path.realpath(H.data())
    return rp.startswith(root + os.sep) and not os.path.islink(p)  # a symlink anywhere in the path resolves outside root and fails


def plan():
    pol, acts, d = policy(), [], H.data()
    ws = os.path.join(d, "workspaces")
    for b in sorted(os.listdir(ws)) if os.path.isdir(ws) else []:
        bdir = os.path.join(ws, b)
        for r, ds, _ in os.walk(bdir, followlinks=False):
            for x in list(ds):
                p = os.path.join(r, x)
                if os.path.islink(p):
                    ds.remove(x)
                elif (x in REGEN or x.endswith("-stills")) and age(p) >= pol["regen_days"]:
                    acts.append(("delete", p, size(p)))
                    ds.remove(x)
        jobs = os.path.join(bdir, "jobs")
        for j in sorted(os.listdir(jobs)) if os.path.isdir(jobs) else []:
            p = os.path.join(jobs, j)
            if os.path.isdir(p) and not os.path.islink(p) and age(p) >= pol["archive_days"]:
                acts.append(("archive", p, size(p)))
    return acts


def mb(n):
    return f"{n / 1e6:.1f} MB"


def report():
    d = H.data()
    ws = os.path.join(d, "workspaces")
    print(f"data home: {d}  total {mb(size(d))} (limit {policy()['max_gb']} GB)")
    for b in sorted(os.listdir(ws)) if os.path.isdir(ws) else []:
        print(f"  {b:<24}{mb(size(os.path.join(ws, b))):>12}")
    acts = plan()
    print(f"would {('clean ' + mb(sum(a[2] for a in acts)) + ' in ' + str(len(acts)) + ' items') if acts else 'do nothing'}:")
    for k, p, n in acts:
        print(f"  {k:<8}{mb(n):>10}  {os.path.relpath(p, d)}")


def archive(p):
    d = H.data()
    rel = os.path.relpath(p, os.path.join(d, "workspaces"))
    b, _, slug = rel.split(os.sep, 2)[0], None, os.path.basename(p)
    out = os.path.join(d, "archive", b, slug + ".tar.gz")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with tarfile.open(out, "w:gz") as t:
        t.add(p, arcname=slug, filter=lambda ti: None if ti.issym() or ti.islnk() else ti)
    with tarfile.open(out) as t:  # verify BEFORE deleting the original
        names = t.getnames()
    if not names or not os.path.getsize(out):
        os.remove(out)
        sys.exit(f"archive of {p} failed verification; original kept")
    shutil.rmtree(p)
    return out


def run(apply):
    acts, freed = plan(), 0
    for k, p, n in acts:
        if not safe(p):
            print("skip (unsafe path):", p)
            continue
        if apply:
            if k == "delete":
                shutil.rmtree(p)
            else:
                archive(p)
            freed += n
        print(f"{'done ' if apply else 'would'} {k:<8}{mb(n):>10}  {os.path.relpath(p, H.data())}")
    print((f"freed about {mb(freed)}" if apply else "dry run: nothing changed. Add --apply-safe to do the reversible classes."))
    if apply:
        open(os.path.join(H.data(), "ledger", "clean.log"), "a").write(f"{time.strftime('%F %T')} cleaned {len(acts)} items, {mb(freed)}\n") if os.path.isdir(os.path.join(H.data(), "ledger")) else None


def restore(b, slug):
    a = os.path.join(H.data(), "archive", b, slug + ".tar.gz")
    dest = os.path.join(H.data(), "workspaces", b, "jobs")
    if not os.path.isfile(a) or os.path.exists(os.path.join(dest, slug)):
        sys.exit("no such archive, or the job folder already exists")
    os.makedirs(dest, exist_ok=True)
    with tarfile.open(a) as t:
        t.extractall(dest, filter="data")
    print("restored", os.path.join(dest, slug))


def harvest():
    """Reusable text from APPROVED runs: hooks and scripts, shot lists, plans. Small, searchable, brand-labelled."""
    d, n = H.data(), 0
    led = os.path.join(d, "ledger", "runs.jsonl")
    rows = [json.loads(l) for l in open(led)] if os.path.isfile(led) else []
    idx = []
    for r in rows:
        job = r.get("job")
        if r.get("outcome") != "approved" or not job or not os.path.isdir(job):
            continue
        brand = job.split(os.sep + "workspaces" + os.sep)[-1].split(os.sep)[0]
        dest = os.path.join(d, "library", "approved", brand, os.path.basename(job))
        os.makedirs(dest, exist_ok=True)
        for f in ("brief.md", "script.md", "shotlist.md", "look.md", "plan.json"):
            if os.path.isfile(os.path.join(job, f)):
                shutil.copy2(os.path.join(job, f), dest)
                n += 1
        idx.append(f"- {brand}/{os.path.basename(job)} · style {r.get('style')} · type {r.get('type', '-')}")
    if idx:
        open(os.path.join(d, "library", "INDEX.md"), "w").write("# Reusable, from approved jobs\n" + "\n".join(idx) + "\n")
    print(f"harvested {n} files from {len(idx)} approved jobs into library/")


def schedule(install):
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    line = f"0 3 * * 0 cd '{repo}' && HOUSE_HOME='{H.data()}' python3 ledger/clean.py run --apply-safe >> '{H.data()}/ledger/clean.log' 2>&1  # video-house weekly cleanup"
    print(line)
    if install:
        import subprocess
        cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
        if "video-house weekly cleanup" in cur:
            return print("already installed")
        subprocess.run(["crontab", "-"], input=cur + line + "\n", text=True, check=True)
        print("installed in your crontab (remove with `crontab -e`). Windows: run inside WSL; macOS may ask for permission the first time.")


def selftest():
    os.environ["HOUSE_HOME"] = tempfile.mkdtemp()
    d = H.data()
    job = os.path.join(d, "workspaces", "b", "jobs", "old")
    os.makedirs(os.path.join(job, "plates"))
    open(os.path.join(job, "brief.md"), "w").write("keep me")
    open(os.path.join(job, "plates", "x.png"), "w").write("x" * 100)
    os.makedirs(os.path.join(d, "brands", "b"))
    open(os.path.join(d, "brands", "b", "BRAND.md"), "w").write("never touched")
    os.symlink("/etc", os.path.join(d, "workspaces", "b", "bin"))  # a symlink must never be followed
    old = time.time() - 200 * DAY
    for r, ds, fs in os.walk(job):
        for x in ds + fs:
            os.utime(os.path.join(r, x), (old, old))
    os.utime(job, (old, old))
    assert [a[0] for a in plan()] == ["delete", "archive"] or {a[0] for a in plan()} == {"delete", "archive"}
    run(False)
    assert os.path.isdir(job), "dry run must change nothing"
    run(True)
    assert not os.path.exists(job) and os.path.isfile(os.path.join(d, "archive", "b", "old.tar.gz"))
    assert open(os.path.join(d, "brands", "b", "BRAND.md")).read() == "never touched" and os.path.islink(os.path.join(d, "workspaces", "b", "bin"))
    restore("b", "old")
    assert open(os.path.join(job, "brief.md")).read() == "keep me"
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:] or ["selftest"]
    {"report": report, "run": lambda: run("--apply-safe" in a), "restore": lambda: restore(a[1], a[2]), "harvest": harvest,
     "schedule": lambda: schedule("--install" in a), "selftest": selftest}[a[0]]()
