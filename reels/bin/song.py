#!/usr/bin/env python3
"""Get a song ready to edit to: the audio, where the hook starts, and the beat grid.
Usage: .venv/bin/python bin/song.py <slug> "<title artist>" [--ref refs/ana/<id>.mp3 | --start SEC] [--len 15] [--mood "tags"]
  --ref    a reference reel's audio: finds where in the song that reel starts (the part that went viral)
  --start  hook start in seconds; with neither, the loudest --len window is used
Writes library/music/<slug>.mp3 (full song) and <slug>.json {file, start, len, bpm, beats: seconds from start}.
The song is baked into the reel (no silent copy). bin/bgm.py lists every prepared song as the reusable BGM store."""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np
import os

os.dup2(os.open(os.devnull, os.O_RDONLY), 0)  # ffmpeg reads stdin: in a shell `while read` loop it would eat the remaining commands

import os as _os
ROOT = Path(_os.environ.get("REEL_HOME") or Path(__file__).resolve().parent.parent)  # data dir (per brand)
ENGINE = Path(__file__).resolve().parent.parent
SR = 8000


def pcm(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def ref_offset(song, ref):
    # FFT cross-correlation of the reel's audio against the full song.
    n = 1 << int(np.ceil(np.log2(len(song) + len(ref))))
    c = np.fft.irfft(np.fft.rfft(song, n) * np.conj(np.fft.rfft(ref, n)), n)[: len(song) - len(ref)]
    i = int(np.argmax(c))
    peak = c[i] / (np.sqrt(np.sum(song[i:i + len(ref)] ** 2) * np.sum(ref ** 2)) + 1e-9)
    return i / SR, float(peak)


def loudest(song, length):
    s = np.convolve(song ** 2, np.ones(SR), "valid")[::SR]  # energy per second
    w = int(length)
    return float(np.argmax(np.convolve(s, np.ones(w), "valid")))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("slug"); a.add_argument("query")
    a.add_argument("--ref"); a.add_argument("--start", type=float); a.add_argument("--len", type=float, default=15)
    a.add_argument("--mood", default="", help="catalogue tag, e.g. 'romantic, slow, mountains'")
    o = a.parse_args()
    mp3 = ROOT / "library/music" / f"{o.slug}.mp3"
    ref_mp4 = ROOT / "refs" / f"{Path(o.ref).stem}.mp4" if o.ref else None

    def use_ref_audio():
        # The reel's own track IS the viral version (sped-up, remix, mashup): take it at full quality, starting at 0.
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", ref_mp4, "-vn", "-ac", "2", "-ar", "44100", "-b:a", "192k", mp3], check=True)
        print(f"using the reference reel's own audio ({ref_mp4.name}) as the track")
        return 0.0

    if not mp3.exists():
        subprocess.run(["yt-dlp", "-q", "--no-warnings", "-x", "--audio-format", "mp3", "-o", str(mp3.with_suffix(".%(ext)s")),
                        f"ytsearch1:{o.query} official audio"])
    if not mp3.exists():  # yt-dlp can exit 0 without producing a file (no search hit)
        if not ref_mp4:
            sys.exit(f"could not download {o.query!r}")
        start = use_ref_audio()
    elif o.ref:
        start, score = ref_offset(pcm(mp3), pcm(ROOT / o.ref))
        print(f"ref match at {start:.2f}s (score {score:.2f})")
        if score < 0.3:  # YouTube has a different version than the reel used
            start = use_ref_audio()
    else:
        start = o.start if o.start is not None else loudest(pcm(mp3), o.len)
    o.len = min(o.len, float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3],
                                             capture_output=True, text=True).stdout) - start - 0.05)
    beats = [float(t) for t in subprocess.run(["aubio", "beat", "-i", str(mp3)], capture_output=True, text=True, check=True).stdout.split()]
    period = float(np.median(np.diff(beats)))
    bpm = 60 / period
    # aubio needs ~2.5s to lock on and reports no beats before that: extend the grid backwards.
    while beats[0] - period >= 0:
        beats.insert(0, round(beats[0] - period, 3))
    rel = [round(t - start, 3) for t in beats if start <= t < start + o.len]
    if len(rel) < 4:
        sys.exit("fewer than 4 beats in the window: check --start/--len")
    meta = {"file": str(mp3.relative_to(ROOT)), "query": o.query, "mood": o.mood, "ref": Path(o.ref).stem if o.ref else None, "start": round(start, 3), "len": o.len, "bpm": round(bpm, 1), "beats": rel}
    mp3.with_suffix(".json").write_text(json.dumps(meta, indent=1))
    print(f"{o.slug}: start {start:.2f}s, {bpm:.0f} bpm, {len(rel)} beats in {o.len:.0f}s")


if __name__ == "__main__":
    main()
