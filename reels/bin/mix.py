#!/usr/bin/env python3
"""Place audio clips on a timeline, with gain envelopes, then normalise. Replaces the hand-written ffmpeg filter graphs.
Usage: python3 bin/mix.py <mix.json> <out.wav>
mix.json:
 { "dur": 14.5,
   "clips": [ {"file": "refs/ana/x.wav", "t": 0.08, "from": 0.08, "to": 0.46, "vol": 1.0, "fade_in": 0, "fade_out": 0.08},
              {"file": "library/music/song.mp3", "t": 0, "from": 275.1, "vol": 1, "env": [[0,0.42],[3,0.42],[5.4,1.0]]} ],
   "fade_out": [13.8, 0.7],            # master fade (start, length)
   "loudness": {"I": -14.5, "TP": -2.2, "LRA": 9} }
 file   path (relative to cwd); t = where it starts on the reel (s); from/to = trim inside the file (s)
 env    piecewise-linear gain in REEL time [[t, gain], ...] (ducking under a voice, ramps into a drop)
Hard-won rules baked in: clips are decoded to WAV first (adelay is ignored on AAC/mp4 inputs: a clip came out 70 ms short) and the result is padded/trimmed to exactly `dur`; tail is limited to -0.9, loudnorm targets -14.5 LUFS / -2.2 dBTP (the AAC encode adds ~1 dB, so -1.5 TP lands at -1.1);
two clips that share music (a ref's own cut + the clean song) must not overlap: use env or fades."""
import json, subprocess, sys
from pathlib import Path


def env_expr(env, t0):
    """volume expression over clip-local time from reel-time points."""
    pts = [(t - t0, g) for t, g in env]
    expr = f"{pts[-1][1]}"
    for (ta, ga), (tb, gb) in reversed(list(zip(pts, pts[1:]))):
        seg = f"{ga}+({gb}-{ga})*(t-{ta})/({tb}-{ta})" if tb != ta else f"{gb}"
        expr = f"if(lt(t,{tb}),{seg},{expr})"
    return f"if(lt(t,{pts[0][0]}),{pts[0][1]},{expr})"


def prep(c, i, tmp):
    """Decode (and trim) every clip to its own 48k stereo WAV first. adelay is silently ignored on AAC/mp4 inputs inside a filter graph
    (a 12.3 s clip delayed 2.16 s came out 12.3 s long, so the mix was 70 ms short); WAV inputs behave. Trimming at decode also keeps long songs fast."""
    w = tmp / f"c{i}.wav"; cmd = ["ffmpeg", "-v", "error", "-y"]
    if c.get("from") is not None: cmd += ["-ss", str(c["from"])]
    if c.get("to") is not None: cmd += ["-t", str(c["to"] - c.get("from", 0))]
    subprocess.run(cmd + ["-i", c["file"], "-vn", "-ac", "2", "-ar", "48000", str(w)], check=True, stdin=subprocess.DEVNULL)
    ln = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(w)], capture_output=True, text=True).stdout)
    return w, ln


def main():
    import tempfile
    spec = json.loads(Path(sys.argv[1]).read_text()); out = sys.argv[2]
    dur = spec["dur"]; cmd = ["ffmpeg", "-v", "error", "-y"]; fl = []; tmp = Path(tempfile.mkdtemp())
    for i, c in enumerate(spec["clips"]):
        w, length = prep(c, i, tmp); cmd += ["-i", str(w)]
        chain = []
        if c.get("env"): chain.append(f"volume='{env_expr(c['env'], c.get('t', 0))}':eval=frame")
        if c.get("vol", 1) != 1: chain.append(f"volume={c['vol']}")
        if c.get("fade_in"): chain.append(f"afade=t=in:st=0:d={c['fade_in']}")
        if c.get("fade_out"): chain.append(f"afade=t=out:st={max(0, length - c['fade_out'])}:d={c['fade_out']}")
        ms = int(round(c.get("t", 0) * 1000)); chain.append(f"adelay={ms}|{ms}")
        fl.append(f"[{i}:a]{','.join(chain)}[a{i}]")
    n = len(spec["clips"]); tail = f"atrim=0:{dur}"
    if spec.get("fade_out"):
        tail += f",afade=t=out:st={spec['fade_out'][0]}:d={spec['fade_out'][1]}"
    fl.append("".join(f"[a{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0:duration=longest,apad=whole_dur={dur},{tail},alimiter=limit=0.9[m]")
    raw = out + ".raw.wav"
    subprocess.run(cmd + ["-filter_complex", ";".join(fl), "-map", "[m]", "-ar", "48000", raw], check=True)
    ln = spec.get("loudness", {"I": -14.5, "TP": -2.2, "LRA": 9})
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", f"loudnorm=I={ln['I']}:TP={ln['TP']}:LRA={ln.get('LRA', 9)},apad=whole_dur={dur},atrim=0:{dur}", "-ar", "48000", out], check=True)
    Path(raw).unlink()
    info = subprocess.run(["ffmpeg", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    last = [l for l in info.splitlines() if "I:" in l or "Peak:" in l][-2:]
    got = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout)
    print(f"{out}  {got:.2f}s (asked {dur})  " + " | ".join(x.strip() for x in last))


if __name__ == "__main__":
    main()
