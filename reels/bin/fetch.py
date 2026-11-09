#!/usr/bin/env python3
"""Download Pexels clips into library/clips/<place>/ as 1080x1920 30fps, silent, first 12s.
Usage: fetch.py <place> <list.txt>     list lines: "<pexels id> <slug> [1080p file url]"
Pexels blocks scripts on its search and video pages (403), and new API keys are paused. Collect ids and file urls in the
built-in browser with fetch() from a pexels.com tab (see LEARNINGS.md). The videos.pexels.com file CDN is open to curl.
Pexels licence: free for commercial use, no attribution needed. Every clip is recorded in SOURCES.jsonl."""
import json, subprocess, sys, tempfile, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os

os.dup2(os.open(os.devnull, os.O_RDONLY), 0)  # ffmpeg reads stdin: in a shell `while read` loop it would eat the remaining commands

import os as _os
ROOT = Path(_os.environ.get("REEL_HOME") or Path(__file__).resolve().parent.parent)  # data dir (per brand)
ENGINE = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0"}


def get(place, vid, slug, url=None):
    out = ROOT / "library/clips" / place / f"pexels-{vid}.mp4"
    if out.exists():
        return f"have {vid}"
    part = out.with_suffix(".part.mp4")
    size = "1920:1080" if place.endswith("-wide") else "1080:1920"  # *-wide libraries keep 16:9 for the letterbox format
    # url: the 1080p file from the video page. Without it /download/video/<id>/ gives the original (often a 4K 300MB file).
    url = url or f"https://www.pexels.com/download/video/{vid}/"
    with tempfile.NamedTemporaryFile(suffix=".mp4") as raw:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
            while chunk := r.read(1 << 20):
                raw.write(chunk)
        raw.flush()
        fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                              "-of", "csv=p=0", raw.name], capture_output=True, text=True).stdout.split()
        n, d = (fps[0].strip(",") if fps else "30/1").split("/")
        slowmo = int(n) / int(d) >= 47  # 50/60fps source → half speed at 30fps: smooth cinematic slow motion
        vf = ("setpts=2*PTS," if slowmo else "") + \
            f"scale={size}:force_original_aspect_ratio=increase,crop={size},fps=30,setsar=1,format=yuv420p"
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw.name, "-an", "-vf", vf, "-t", "12",
                            "-c:v", "libx264", "-preset", "fast", "-crf", "19", part], capture_output=True, text=True)
    if r.returncode:
        part.unlink(missing_ok=True)
        return f"FAIL {vid}: {r.stderr[-200:]}"
    part.rename(out)  # only finished files get the real name, so "have" is never a half-written clip
    with open(ROOT / "library/clips/SOURCES.jsonl", "a") as f:
        f.write(json.dumps({"file": str(out.relative_to(ROOT)), "source": "pexels", "id": vid, "slug": slug,
                            "url": f"https://www.pexels.com/video/{slug}-{vid}/", "slowmo": slowmo,
                            "licence": "Pexels (free commercial)"}) + "\n")
    return f"ok {vid} {slug}"


if __name__ == "__main__":
    place, lst = sys.argv[1], Path(sys.argv[2])
    (ROOT / "library/clips" / place).mkdir(parents=True, exist_ok=True)
    rows = [l.split()[:3] for l in lst.read_text().splitlines() if l.strip()]
    with ThreadPoolExecutor(4) as ex:
        for msg in ex.map(lambda r: get(place, *r), rows):
            print(msg, flush=True)
