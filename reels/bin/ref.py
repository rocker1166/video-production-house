#!/usr/bin/env python3
"""Analyse reference reels: download, cuts, frame sheet, song (Shazam), lyrics (ElevenLabs), stats.
Usage: .venv/bin/python bin/ref.py <instagram/youtube url> [more urls]
Writes refs/<id>.mp4 + refs/ana/<id>.{json,sheet.jpg,mp3,stt.json} and prints one summary line per reel.
Then read the sheet (captions, shot types) and pick or build a format (WORKFLOW.md)."""
import asyncio, json, os, statistics, subprocess, sys, urllib.request
from pathlib import Path

os.dup2(os.open(os.devnull, os.O_RDONLY), 0)  # ffmpeg reads stdin: in a shell `while read` loop it would eat the remaining commands

import os as _os
ROOT = Path(_os.environ.get("REEL_HOME") or Path(__file__).resolve().parent.parent)  # data dir (per brand)
ENGINE = Path(__file__).resolve().parent.parent
REFS, ANA = ROOT / "refs", ROOT / "refs/ana"
KEY_FILE = ENGINE.parent / ".env"  # ELEVENLABS_API_KEY lives in the repo .env


def run(*cmd):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, check=True).stdout


def song(mp3):
    from shazamio import Shazam
    try:
        t = (asyncio.run(Shazam().recognize(str(mp3))).get("track")) or {}
        return f"{t.get('title')} — {t.get('subtitle')}" if t else None
    except Exception as e:  # Shazam is unofficial: a failure must not stop the rest of the analysis
        return f"shazam failed: {e}"


def lyrics(mp3, out):
    key = os.environ.get("ELEVENLABS_API_KEY") or next((l.split("=", 1)[1].strip() for l in (KEY_FILE.read_text().splitlines() if KEY_FILE.exists() else [])
                                                       if l.startswith("ELEVENLABS_API_KEY=")), None)
    if not key:
        return None
    r = run("curl", "-s", "https://api.elevenlabs.io/v1/speech-to-text", "-H", f"xi-api-key: {key}", "-F", "model_id=scribe_v1",
            "-F", "timestamps_granularity=word", "-F", f"file=@{mp3}")
    out.write_text(r)
    return json.loads(r).get("text")


def analyse(url):
    vid = url.rstrip("/").split("/")[-1].split("?")[0] if "/p/" in url or "/reel/" in url else None
    REFS.mkdir(exist_ok=True); ANA.mkdir(exist_ok=True)
    if not vid or not (REFS / f"{vid}.mp4").exists():
        run("yt-dlp", "-q", "--no-warnings", "--write-info-json", "-o", REFS / "%(id)s.%(ext)s", url)
        vid = vid or json.loads(run("yt-dlp", "-q", "--dump-json", url))["id"]
    mp4 = REFS / f"{vid}.mp4"
    info = json.loads((REFS / f"{vid}.info.json").read_text()) if (REFS / f"{vid}.info.json").exists() else {}
    dur = float(run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4))
    wh = run("ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", mp4).strip()
    # cropdetect first: letterboxed 16:9-in-9:16 reels hide their cuts from the scene detector behind the black bars.
    crop = [l.split("crop=")[1].split()[0] for l in subprocess.run(["ffmpeg", "-t", "5", "-i", str(mp4), "-vf", "cropdetect=24:2:0", "-f", "null", "-"],
                                                                    capture_output=True, text=True).stderr.splitlines() if "crop=" in l]
    vf = (f"crop={crop[-1]}," if crop else "") + "scale=270:-2,select='gt(scene,0.28)',showinfo"
    cuts = [float(l.split("pts_time:")[1].split()[0]) for l in subprocess.run(["ffmpeg", "-i", str(mp4), "-vf", vf, "-an", "-f", "null", "-"],
                                                                              capture_output=True, text=True).stderr.splitlines() if "pts_time:" in l]
    shots = [b - a for a, b in zip([0] + cuts, cuts + [dur])]
    run("ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", "fps=2,scale=300:300:force_original_aspect_ratio=decrease,pad=300:300:(ow-iw)/2:(oh-ih)/2,tile=8x5",
        "-frames:v", "1", ANA / f"{vid}.sheet.jpg")
    # dense 4fps sheet (12x5 = 15s): the 2fps sheet above hides fast-moving reels. Read THIS one to write the beat plan.
    run("ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", "fps=4,scale=170:-1,tile=12x5", "-frames:v", "1", ANA / f"{vid}.dense.jpg")
    mp3 = ANA / f"{vid}.mp3"
    run("ffmpeg", "-v", "error", "-y", "-i", mp4, "-vn", "-ac", "1", "-ar", "22050", "-b:a", "96k", mp3)
    # sync points: hits + quiet gaps (voice with ducked music). Align to THESE, not to the beat grid (see LEARNINGS 2026-11-06).
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent)); import cues as _cues
        sys.argv = ["cues", str(mp4), "--out", str(ANA / f"{vid}.cues.json")]; _cues.main()
    except Exception as e:  # cue extraction must never stop the rest of the analysis
        print("   cues failed:", e)
    s = {"id": vid, "url": url, "creator": info.get("channel") or info.get("uploader"), "likes": info.get("like_count"),
         "caption": (info.get("description") or "")[:200], "dur": round(dur, 1), "size": wh, "cuts": [round(c, 2) for c in cuts],
         "median_shot": round(statistics.median(shots), 2), "song": song(mp3), "lyrics": lyrics(mp3, ANA / f"{vid}.stt.json")}
    (ANA / f"{vid}.json").write_text(json.dumps(s, indent=1, ensure_ascii=False))
    print(f"{vid} · {s['dur']}s {wh} · {len(shots)} shots, median {s['median_shot']}s · ♪ {s['song']} · likes {s['likes']}\n"
          f"   lyrics: {(s['lyrics'] or '-')[:120]}\n   sheet: {ANA / (vid + '.sheet.jpg')}\n   dense: {ANA / (vid + '.dense.jpg')} (4fps: read this)\n   cues:  {ANA / (vid + '.cues.json')}")


if __name__ == "__main__":
    for u in sys.argv[1:]:
        analyse(u)
