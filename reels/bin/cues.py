#!/usr/bin/env python3
"""Where are the real sync points in a song or a reference reel's audio? (hits, quiet gaps, level by second)
Usage: .venv/bin/python bin/cues.py <audio-or-video> [--out cues.json] [--top 12]
Why: aligning to aubio's beat grid was wrong twice (a strings intro sat half a beat off its stabs; the ref's cards cut at a flat 0.24s, 29% on-grid = chance).
What matters is the HITS (a sudden jump in level) and the GAPS (a voice with the music ducked). Cut and slam on those, not on the grid.
Output: {dur, hits:[{t, jump_db}] strongest first then sorted by time, gaps:[{start,end}], level:[dB per second], onsets:[t] (aubio)}"""
import json, subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np


def decode(path, sr=22050):
    tmp = Path(tempfile.mkdtemp()) / "a.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), str(tmp)], check=True, stdin=subprocess.DEVNULL)
    with wave.open(str(tmp)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return tmp, x, sr


def main():
    args = sys.argv[1:]; path = args[0]
    out = args[args.index("--out") + 1] if "--out" in args else None
    top = int(args[args.index("--top") + 1]) if "--top" in args else 12
    tmp, x, sr = decode(path); dur = len(x) / sr
    hop = int(sr * 0.01)  # 10 ms
    rms = np.array([np.sqrt(np.mean(x[i:i + hop * 2] ** 2) + 1e-12) for i in range(0, len(x) - hop * 2, hop)])
    db = 20 * np.log10(rms + 1e-9)
    # hit = level rises >= 9 dB within 60 ms over the 300 ms before, and is not tiny
    hits = []
    for i in range(30, len(db) - 6):
        before = np.mean(db[i - 30:i - 3]); peak = np.max(db[i:i + 6])
        jump = peak - before
        if jump >= 9 and peak > -38 and (not hits or i * 0.01 - hits[-1]["t"] > 0.12):
            hits.append({"t": round(i * 0.01, 2), "jump_db": round(float(jump), 1)})
    # gaps = level under -38 dB for >= 0.3 s (a voice-only reel has its music ducked here: -43 LUFS in the coconat ref)
    gaps, start = [], None
    for i, v in enumerate(db):
        if v < -38 and start is None: start = i
        if (v >= -38 or i == len(db) - 1) and start is not None:
            if (i - start) * 0.01 >= 0.3: gaps.append({"start": round(start * 0.01, 2), "end": round(i * 0.01, 2)})
            start = None
    level = [round(float(np.mean(db[s * 100:(s + 1) * 100])), 1) for s in range(int(dur))]
    onsets = []
    try:
        o = subprocess.run(["aubioonset", "-i", str(tmp), "-O", "hfc", "-t", "0.4"], capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout
        onsets = [round(float(l), 2) for l in o.split()]
    except Exception:
        pass
    strongest = sorted(hits, key=lambda h: -h["jump_db"])[:top]
    res = {"file": str(path), "dur": round(dur, 2), "hits": sorted(strongest, key=lambda h: h["t"]), "gaps": gaps, "level_db_per_s": level, "onsets": onsets}
    if out: Path(out).write_text(json.dumps(res, indent=1))
    print(f"{path}: {dur:.1f}s")
    print("  hits (t, +dB):", ", ".join(f"{h['t']}s +{h['jump_db']}" for h in res["hits"]))
    print("  gaps:", ", ".join(f"{g['start']}-{g['end']}s" for g in gaps) or "none")
    print("  level/s:", level)


if __name__ == "__main__":
    main()
