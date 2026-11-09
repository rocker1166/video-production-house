#!/usr/bin/env python3
"""Render one reel spec to out/<NNN>-<name>.mp4 (1080x1920, 30fps) plus a review sheet in qc/.
Usage: render.py spec/<name>.json
Spec: see spec/example.json. Clip `dur` is the seconds used from each clip; crossfades overlap, so
total = sum(dur) - (n-1)*xfade. Caption times are in output seconds."""
import json, subprocess, sys, tempfile, time
from pathlib import Path
import os

os.dup2(os.open(os.devnull, os.O_RDONLY), 0)  # ffmpeg reads stdin: in a shell `while read` loop it would eat the remaining commands

import os as _os
ROOT = Path(_os.environ.get("REEL_HOME") or Path(__file__).resolve().parent.parent)  # data dir (per brand)
ENGINE = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"FAILED: {' '.join(map(str, cmd))[:400]}\n{r.stderr[-1500:]}")
    return r.stdout


def probe(p, entry):
    return run(["ffprobe", "-v", "error", "-show_entries", entry, "-of", "csv=p=0", p]).strip()


def need(spec_clips, music):
    for c in spec_clips:
        if "color" in c:
            continue
        f = ROOT / c["file"]
        if not f.exists():
            sys.exit(f"missing clip {f}")
        have = float(probe(f, "format=duration"))
        if c.get("start", 0) + c["dur"] > have + 0.05:
            sys.exit(f"{c['file']}: needs {c.get('start', 0) + c['dur']:.1f}s but is only {have:.1f}s")
    if music and not (ROOT / music["file"]).exists():
        sys.exit(f"missing music {ROOT / music['file']}")


def main(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    name, clips, caps = spec["name"], spec["clips"], spec.get("captions", [])
    x, trans, music = spec.get("xfade", 0.4), spec.get("transition", "fade"), spec.get("music")
    need(clips, music)
    if any(c["dur"] <= max(2 * x, 0.2) for c in clips):
        sys.exit(f"every clip dur must exceed {max(2 * x, 0.2)}s")
    total = sum(c["dur"] for c in clips) - (len(clips) - 1) * x
    t0 = time.time()
    tmp = Path(tempfile.mkdtemp(prefix=f"reel-{name}-"))

    # 1. Normalise every clip to 1080x1920 30fps (crop-fill, no audio) so xfade gets identical inputs.
    norm = []
    for i, c in enumerate(clips):
        o = tmp / f"c{i}.mp4"
        # Exact frame count per shot, so 30 beat cuts don't drift off the music from per-shot rounding.
        src = ["-f", "lavfi", "-i", f"color=c={c['color']}:s={W}x{H}:r={FPS}"] if "color" in c else \
            ["-ss", c.get("start", 0), "-t", c["dur"] + 0.5, "-i", ROOT / c["file"]]
        # letterbox: a 16:9 clip sits full-width on black (the cinematic refs); otherwise crop-fill the 9:16 frame.
        fit = f"scale={W}:-2,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black" if c.get("fit") == "letterbox" else \
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
        run(["ffmpeg", "-v", "error", "-y", *src, "-an",
             "-vf", f"{fit},fps={FPS},setsar=1,format=yuv420p",
             "-frames:v", round(c["dur"] * FPS), "-c:v", "libx264", "-preset", "fast", "-crf", "16", o])
        norm.append(o)

    # 2. Captions → transparent PNGs (Edge shapes the Devanagari).
    if caps:
        run(["node", ENGINE / "bin/caption.cjs", spec_path, tmp / "caps"])

    # 3. One filter graph: xfade chain, caption overlays with fades, music with fades + loudness.
    ins, fg = [], []
    for o in norm:
        ins += ["-i", o]
    n = len(clips)
    if x == 0:  # hard cuts (the reference style): plain concat
        fg.append("".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0[cut]")
        v = "[cut]"
    else:
        v, length = "[0:v]", clips[0]["dur"]
        for i in range(1, n):
            fg.append(f"{v}[{i}:v]xfade=transition={trans}:duration={x}:offset={length - x:.3f}[x{i}]")
            v, length = f"[x{i}]", length + clips[i]["dur"] - x
    grade = spec.get("grade")
    if grade:
        grades = json.loads((ROOT / "style.json").read_text())["_grades"]
        fg.append(f"{v}{grades[grade]}[g]")
        v = "[g]"
    for j, c in enumerate(caps):
        at, end = c["at"], c["at"] + c["dur"]
        if end > total + 0.01:
            sys.exit(f"caption {j} ends at {end}s but the video is {total:.1f}s")
        ins += ["-loop", "1", "-framerate", FPS, "-t", f"{total:.3f}", "-i", tmp / "caps" / f"cap{j}.png"]
        fd = c.get("fade", 0.3)  # word-by-word lyrics use ~0.06 so they don't flicker
        fg.append(f"[{n + j}:v]format=rgba,fade=t=in:st={at}:d={fd}:alpha=1,fade=t=out:st={end - fd}:d={fd}:alpha=1[c{j}]")
        fg.append(f"{v}[c{j}]overlay=enable='between(t,{at},{end})'[o{j}]")
        v = f"[o{j}]"
    fg.append(f"{v}format=yuv420p[vout]")
    maps = ["-map", "[vout]"]
    if music:
        m = music.get("start", 0)
        fo = music.get("fadeOut", 1.5)
        ins += ["-ss", m, "-i", ROOT / music["file"]]
        fg.append(f"[{n + len(caps)}:a]atrim=0:{total:.3f},afade=t=in:d=0.5,afade=t=out:st={total - fo:.3f}:d={fo},"
                  f"volume={music.get('volume', 1)}[bgm]")
        voice = spec.get("voice")
        if voice:  # narration over a quiet song bed (music.volume ~0.18)
            ins += ["-i", ROOT / voice["file"]]
            ms = int(voice.get("at", 0) * 1000)
            fg.append(f"[{n + len(caps) + 1}:a]adelay={ms}|{ms},apad[vo]")
            fg.append("[bgm][vo]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
        else:
            fg.append("[bgm]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
        maps += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]

    # Every reel gets a permanent number (numbers.json), so files read 001-…, 002-… and re-renders keep theirs.
    reg_path = ROOT / "numbers.json"
    reg = json.loads(reg_path.read_text()) if reg_path.exists() else {}
    if name not in reg:
        reg[name] = max(reg.values(), default=0) + 1
        reg_path.write_text(json.dumps(reg, indent=1))
    out = ROOT / "out" / f"{reg[name]:03d}-{name}.mp4"
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fg), *maps, "-t", f"{total:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", FPS, "-pix_fmt", "yuv420p", "-movflags", "+faststart", out])

    # 4. Ship gates: size, length, audio. Contact sheet for the review step.
    dims = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0", out]).strip().strip("x")  # ffprobe can add a trailing separator: "1080x1920x"
    dur = float(probe(out, "format=duration"))
    has_audio = bool(run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", out]).strip())
    problems = []
    if dims != f"{W}x{H}":
        problems.append(f"size {dims}")
    if not 8 <= dur <= 62:
        problems.append(f"length {dur:.1f}s outside 8-62s")
    if music and not has_audio:
        problems.append("music requested but no audio track")
    # Review sheet goes to qc/, so out/ holds only the finished reels.
    (ROOT / "qc").mkdir(exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", out, "-vf", f"fps=1/{max(dur / 12, 0.5):.2f},scale=270:-2,tile=6x2", "-frames:v", "1",
         ROOT / "qc" / f"{out.stem}.jpg"])
    with open(ROOT / "runs.jsonl", "a") as f:
        f.write(json.dumps({"name": name, "ts": int(time.time()), "dur": round(dur, 1), "clips": len(clips),
                            "captions": len(caps), "music": bool(music), "problems": problems, "verdict": None}) + "\n")
    print(f"{'GATE FAIL ' + '; '.join(problems) if problems else 'ok'} → {out} ({dur:.1f}s, {time.time() - t0:.0f}s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main(sys.argv[1])
