#!/usr/bin/env python3
"""Voiceover for the `voice` format: neural TTS (free, edge-tts) + per-word timings for synced captions.
Usage: .venv/bin/python bin/voice.py <slug> "<script>" [--voice en-IN-PrabhatNeural] [--rate +0%]
  Indian voices: en-IN-PrabhatNeural (m), en-IN-NeerjaNeural (f), hi-IN-MadhurNeural (m), hi-IN-SwaraNeural (f).
  Hindi voices read Devanagari; Hinglish in Roman script sounds best with an en-IN voice.
Writes library/voice/<slug>.mp3 and <slug>.json {file, dur, words: [[start, end, word], ...]}."""
import argparse, asyncio, json, subprocess
from pathlib import Path
import edge_tts
import os

os.dup2(os.open(os.devnull, os.O_RDONLY), 0)  # ffmpeg reads stdin: in a shell `while read` loop it would eat the remaining commands

import os as _os
ROOT = Path(_os.environ.get("REEL_HOME") or Path(__file__).resolve().parent.parent)  # data dir (per brand)
ENGINE = Path(__file__).resolve().parent.parent


async def speak(text, voice, rate, mp3):
    words = []
    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    with open(mp3, "wb") as f:
        async for c in comm.stream():
            if c["type"] == "audio":
                f.write(c["data"])
            elif c["type"] == "WordBoundary":  # offsets are in 100-nanosecond ticks
                s = c["offset"] / 1e7
                words.append([round(s, 3), round(s + c["duration"] / 1e7, 3), c["text"]])
    return words


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("slug"); a.add_argument("script")
    a.add_argument("--voice", default="en-IN-PrabhatNeural"); a.add_argument("--rate", default="+0%")
    o = a.parse_args()
    out = ROOT / "library/voice"; out.mkdir(parents=True, exist_ok=True)
    mp3 = out / f"{o.slug}.mp3"
    words = asyncio.run(speak(o.script, o.voice, o.rate, mp3))
    assert words, "TTS returned no word timings"
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3],
                               capture_output=True, text=True).stdout)
    (out / f"{o.slug}.json").write_text(json.dumps({"file": str(mp3.relative_to(ROOT)), "voice": o.voice, "script": o.script,
                                                    "dur": round(dur, 3), "words": words}, indent=1, ensure_ascii=False))
    print(f"{o.slug}: {dur:.1f}s, {len(words)} words")


if __name__ == "__main__":
    main()
