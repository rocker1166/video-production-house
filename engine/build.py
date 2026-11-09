"""Vox-style reel builder, driven by <work>/plan.json.

  python3 build.py <work> jobs      # scene windows -> jobs.json (for render.cjs); prints the timeline
  python3 build.py <work> aroll     # frame-exact jump-cut A-roll with punch-ins -> aroll.mov
  python3 build.py <work> plates    # person matte + frame plates for effect scenes ("plate": true)
  python3 build.py <work> compose   # graphics track + foley + music + room tone -> plan.output
  python3 build.py <work> check     # ship gates: A/V length, frozen frames, black frames, loudness
  python3 build.py <work> all       # aroll + compose + check

Every time in plan.json is a SOURCE second (where the word is spoken in the raw clip) unless the
key says otherwise, so re-trimming never desyncs a beat.
"""
import json, re, shutil, subprocess, sys, pathlib

SKILL = pathlib.Path(__file__).resolve().parent.parent
WORK = pathlib.Path(sys.argv[1]).resolve()
PLAN = json.loads((WORK / "plan.json").read_text())
FPS = PLAN.get("fps", 30)
END_CARD = PLAN.get("end_card", 2.6)

# ---- cut list: dead air out, every cut snapped to the frame grid ----
words = [w for w in json.loads((WORK / "stt.json").read_text())["words"]
         if w["type"] == "word" and not w["text"].startswith("[")]
PAD, MAX_GAP = PLAN.get("cut", {}).get("pad", .09), PLAN.get("cut", {}).get("max_gap", .28)
keep, start = [], words[0]["start"] - PAD
for a, b in zip(words, words[1:]):
    if b["start"] - a["end"] > MAX_GAP:
        keep.append((start, a["end"] + PAD))
        start = b["start"] - PAD
keep.append((start, words[-1]["end"] + .25))
# Unsnapped cuts round the video per segment while audio cuts exactly: lips drift cut by cut.
keep = [(round(max(0, s) * FPS) / FPS, round(e * FPS) / FPS) for s, e in keep]


def out(t):
    """Source second -> output second (a time inside a cut snaps to the next kept range)."""
    acc = 0.0
    for s, e in keep:
        if t < s:
            return acc
        if t <= e:
            return acc + t - s
        acc += e - s
    return acc


SPEECH_END = out(keep[-1][1])
TOTAL = SPEECH_END + END_CARD


def scene_windows():
    sc = PLAN["scenes"]
    wins = [(s["name"], out(s["from"]), out(s["to"]), s.get("alpha", False), s.get("cues", {}), s.get("props", {})) for s in sc]
    for i, (name, a, b, alpha, cues, props) in enumerate(wins):
        # Close sub-0.35s gaps to the next scene on the same layer: a few frames of face in between reads as a glitch.
        nxt = next((w for w, s in zip(wins[i + 1:], sc[i + 1:]) if s.get("layer", 1) == sc[i].get("layer", 1)), None)
        if nxt and 0 < nxt[1] - b < .35:
            b = nxt[1]
        props = dict(props)
        if sc[i].get("plate"):
            props["plateDir"] = str(WORK / "plates" / name)
        if sc[i].get("captions"):
            hl = {h.lower() for h in sc[i].get("highlight", [])}
            props["words"] = [{"w": w["text"], "t": round(out(w["start"]) - a, 3), "hl": w["text"].strip(".,!?।").lower() in hl}
                              for w in words if a <= out(w["start"]) < b]
        yield name, a, b, alpha, {k: round(out(v) - a, 3) for k, v in cues.items()} | {"end": round(b - a, 3)}, props
    if PLAN.get("end_scene"):
        yield PLAN["end_scene"], SPEECH_END, TOTAL, False, {"end": END_CARD}, PLAN.get("end_props", {})


def run(cmd):
    print("$", " ".join(map(str, cmd))[:160], "...")
    subprocess.run(cmd, check=True)


def jobs():
    js = [{"name": n, "alpha": al, "cues": c, "props": p} for n, a, b, al, c, p in scene_windows()]
    (WORK / "jobs.json").write_text(json.dumps(js, indent=1))
    for n, a, b, al, c, p in scene_windows():
        print(f"{n:14s} {a:6.2f}-{b:6.2f} {'alpha' if al else 'full '} {c}")
    print(f"speech {SPEECH_END:.2f}s + end card {END_CARD}s = {TOTAL:.2f}s  ({len(keep)} cuts)")


def aroll():
    cfr = WORK / "src30.mov"   # made by ingest.py
    punch = {float(k): v for k, v in PLAN.get("punch", {}).items()}
    parts, labels = [], []
    for i, (s, e) in enumerate(keep):
        z = next((v for k, v in punch.items() if abs(k - s) < .08), 1.0 if i % 2 == 0 else 1.12)
        w, h = round(1080 * z / 2) * 2, round(1920 * z / 2) * 2
        # Static punch-in per cut: a slow zoompan push snaps to whole pixels and judders.
        parts.append(
            f"[0:v]trim=start_frame={round(s * FPS)}:end_frame={round(e * FPS)},setpts=PTS-STARTPTS,"
            f"scale={w}:{h}:flags=lanczos,crop=1080:1920:{(w - 1080) // 2}:{int((h - 1920) * 0.30)},"
            f"unsharp=5:5:0.5,eq=contrast=1.04:saturation=1.05,setsar=1[v{i}];"
            f"[0:a]atrim={s:.4f}:{e:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={e - s - 0.015:.3f}:d=0.015[a{i}];")
        labels.append(f"[v{i}][a{i}]")
    fc = "".join(parts) + "".join(labels) + f"concat=n={len(keep)}:v=1:a=1[v][a]"
    run(["ffmpeg", "-y", "-v", "error", "-i", cfr, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-c:a", "pcm_s16le", WORK / "aroll.mov"])


# Foley level per cue kind (scenes log their own cues into frames/<scene>.sfx.json).
FOLEY = {"slide": .32, "rustle": .30, "typewriter": .38, "pen": .30, "stamp": .95, "marker": .6,
         "send": .55, "typing": .5, "click": 1.0, "ding": .85, "pop": .5, "paper_slap": .5, "thump": .6,
         "whoosh": .4, "whoosh2": .4, "riser": .35, "shutter": .5}
ALT = {"slide": ["slide", "slide2"]}   # alternate takes so repeated arrivals don't machine-gun


def sfx_events():
    ev = []
    for x in PLAN.get("sfx", []):   # transitions / accents placed by hand in plan.json
        t = SPEECH_END + x.get("plus", 0) if x.get("at") == "end" else x["out"] if "out" in x else out(x["t"])
        ev.append((x["k"], t, x.get("v", .5)))
    count = {}
    for n, a, b, *_ in scene_windows():
        f = WORK / "frames" / f"{n}.sfx.json"
        last = {}
        for c in json.loads(f.read_text()) if f.exists() else []:
            k, t = c["kind"], a + c["t"]
            if t - last.get(k, -9) < .12 or t > b:   # thin out stacked cues
                continue
            last[k] = t
            takes = ALT.get(k, [k]); count[k] = count.get(k, 0) + 1
            ev.append((takes[count[k] % len(takes)], t, FOLEY[k]))
    return [e for e in ev if e[2] > 0]


def layer_of(name):
    return next((x.get("layer", 1) for x in PLAN["scenes"] if x["name"] == name), 1)


def track(layer=1):
    """One continuous RGBA graphics track per layer (blank frames between scenes): a single overlay input
    stays frame-locked, where a dozen time-offset inputs drifted in ffmpeg's framesync. Layer 2+ (captions,
    list trackers) sit above layer 1 (scenes and effects)."""
    d = WORK / "frames" / f"_track{layer}"
    d.mkdir(parents=True, exist_ok=True)
    for f in d.iterdir(): f.unlink()
    blank = WORK / "frames" / "blank.png"
    if not blank.exists():
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black@0.0:s=1080x1920,format=rgba", "-frames:v", "1", blank])
    total = int(round(TOTAL * FPS))
    slots = [blank] * total
    for n, a, *_ in scene_windows():
        if layer_of(n) != layer: continue
        start = int(round(a * FPS))
        for i, f in enumerate(sorted((WORK / "frames" / n).glob("*.png"))):
            if start + i < total: slots[start + i] = f
    for i, f in enumerate(slots):
        (d / f"{i:05d}.png").symlink_to(f)
    return d


def plates():
    """Effect scenes composite the creator's own frames: per plate scene, export its A-roll window as
    JPGs and the person matte as alpha PNGs (white, alpha = matte) into plates/<scene>/."""
    matte = WORK / "matte.mov"
    if not matte.exists() or matte.stat().st_mtime < (WORK / "aroll.mov").stat().st_mtime:
        here = pathlib.Path(__file__).parent
        tool = here / "matte"
        if sys.platform == "darwin" and (tool.exists() or shutil.which("swiftc")):  # Apple Vision: fast, no extra deps
            if not tool.exists():
                run(["swiftc", "-O", here / "matte.swift", "-o", tool])
            cmd = [str(tool), str(WORK / "aroll.mov"), "accurate"]
        else:  # everywhere else: rembg (pip install -r requirements-seg.txt), slower on CPU
            cmd = [sys.executable, str(here / "matte.py"), str(WORK / "aroll.mov"), "accurate"]
        p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", "540x960", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(matte)], stdin=p1.stdout, check=True)
        p1.wait()
    for s, (n, a, b, *_) in zip(PLAN["scenes"], scene_windows()):
        if not s.get("plate"): continue
        d = WORK / "plates" / n
        d.mkdir(parents=True, exist_ok=True)
        for f in d.iterdir(): f.unlink()
        fa, fb = round(a * FPS), round(b * FPS)
        cut, n_fr = f"trim=start_frame={fa}:end_frame={fb},setpts=PTS-STARTPTS", str(fb - fa)
        run(["ffmpeg", "-y", "-v", "error", "-i", WORK / "aroll.mov", "-vf", cut, "-frames:v", n_fr, "-q:v", "3",
             "-start_number", "0", d / "v_%05d.jpg"])
        # White RGB + alpha = matte, from one finite stream (an infinite lavfi colour source never ends the merge).
        run(["ffmpeg", "-y", "-v", "error", "-i", WORK / "matte.mov", "-filter_complex",
             f"[0:v]{cut},format=gray,split[a][b];[a]lutyuv=y=255[w];[w][b]alphamerge,format=rgba", "-frames:v", n_fr,
             "-start_number", "0", d / "m_%05d.png"])
        print(f"plate {n}: {fb - fa} frames")


def music():
    m = WORK / "music.wav"
    if m.exists(): return m
    a, b = SKILL / "assets/music/loop1.mp3", SKILL / "assets/music/loop2.mp3"
    # Generated loops end in ~1.5s of silence: trim the tails before crossfading or the bed drops out.
    run(["ffmpeg", "-y", "-v", "error", "-i", a, "-i", b, "-filter_complex",
         "[0:a]atrim=0:20.6[a];[1:a]atrim=0:20.3[b];[a][b]acrossfade=d=1.2[ab];[ab]asplit[x][y];[x][y]acrossfade=d=1.2[m];"
         "[m]aloop=loop=2:size=2e9,atrim=0:150,afade=t=in:d=0.3[o]", "-map", "[o]", "-ar", "48000", "-ac", "2", m])
    return m


def sfx_file(name):
    local = WORK / "sfx" / f"{name}.mp3"   # a project may override or add a sound
    return local if local.exists() else SKILL / "assets/sfx" / f"{name}.mp3"


def compose():
    layers = sorted({x.get("layer", 1) for x in PLAN["scenes"]} | {1})
    ev = sfx_events()
    inputs = ["-i", WORK / "aroll.mov"]
    for L in layers:
        # -reinit_filter 0: tracks mix rgb24/rgba PNGs; a mid-stream graph rebuild drops frames and can deadlock the mix.
        inputs += ["-reinit_filter", "0", "-framerate", str(FPS), "-i", track(L) / "%05d.png"]
    for name, *_ in ev:
        inputs += ["-i", sfx_file(name)]
    inputs += ["-i", music(), "-stream_loop", "-1", "-i", sfx_file("room")]
    fc = [f"[0:v]tpad=stop_mode=clone:stop_duration={END_CARD}[v0]"]
    for i, _ in enumerate(layers):
        fc.append(f"[{i + 1}:v]format=rgba[g{i}]")
        fc.append(f"[v{i}][g{i}]overlay=eof_action=pass[v{i + 1}]")
    fc += [f"[v{len(layers)}]format=yuv420p[vout]",
          f"[0:a]apad=pad_dur={END_CARD},highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=3,"
          f"equalizer=f=3500:t=q:w=1:g=2,asplit=2[voice][key]"]
    mix = ["[voice]"]
    for j, (name, t, vol) in enumerate(ev):
        fc.append(f"[{1 + len(layers) + j}:a]volume={vol},adelay={int(t * 1000)}:all=1[s{j}]")
        mix.append(f"[s{j}]")
    m = 1 + len(layers) + len(ev)
    vol = PLAN.get("music", {}).get("volume", .75)
    fc.append(f"[{m}:a]atrim=0:{TOTAL:.2f},volume={vol},afade=t=out:st={TOTAL - 0.6:.2f}:d=0.6[mus]")
    fc.append(f"[{m + 1}:a]atrim=0:{TOTAL:.2f},volume=0.22,afade=t=in:d=0.4[room]")
    fc.append("[mus][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[duck]")
    mix += ["[room]", "[duck]"]
    fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first,"
              f"loudnorm=I=-14:TP=-1.5:LRA=9,atrim=0:{TOTAL:.2f}[aout]")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc),
         "-map", "[vout]", "-map", "[aout]", "-t", f"{TOTAL:.2f}",
         "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", PLAN["output"]])


def check():
    """Ship gates. Each one is a correction the owner made on a past reel."""
    f, ok = PLAN["output"], True
    probe = lambda a: subprocess.run(["ffprobe", "-v", "error", "-select_streams", a, "-show_entries", "stream=duration",
                                      "-of", "csv=p=0", str(WORK / "aroll.mov")], capture_output=True, text=True).stdout.strip()
    vd, ad = float(probe("v")), float(probe("a"))
    print(f"[{'PASS' if abs(vd - ad) < 0.05 else 'FAIL'}] A/V sync: video {vd:.3f}s vs audio {ad:.3f}s"); ok &= abs(vd - ad) < .05
    log = subprocess.run(["ffmpeg", "-v", "info", "-i", str(f), "-vf", "freezedetect=n=-60dB:d=0.4,blackdetect=d=0.1:pix_th=0.05",
                          "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    freezes = re.findall(r"freeze_start: ([\d.]+)", log)
    blacks = re.findall(r"black_start:([\d.]+)", log)
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", log)[-1]); peak = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", log)[-1])
    print(f"[{'PASS' if not freezes else 'FAIL'}] no still hold ≥0.4s {freezes or ''}"); ok &= not freezes
    print(f"[{'PASS' if not blacks else 'FAIL'}] no black frames {blacks or ''}"); ok &= not blacks
    good = -16 <= lufs <= -13 and peak <= -1
    print(f"[{'PASS' if good else 'FAIL'}] loudness {lufs} LUFS, peak {peak} dBFS (want -16..-13, ≤ -1)"); ok &= good
    print("SHIP GATES:", "ALL PASS" if ok else "FIX BEFORE SHOWING")
    return ok


if __name__ == "__main__":
    for step in sys.argv[2:]:
        if step == "jobs": jobs()
        if step in ("aroll", "all"): aroll()
        if step in ("plates", "all"): plates()
        if step in ("compose", "all"): compose()
        if step in ("check", "all"): sys.exit(0 if check() else 1)
