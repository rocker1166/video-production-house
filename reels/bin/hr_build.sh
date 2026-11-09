#!/usr/bin/env bash
# Encode an HTML-seek reel: frames + mixed audio -> mp4, then the QC pack.  bin/hr_build.sh <dir> <audio.wav> <out.mp4> [fps=30]
#   <dir>/frames/0000.jpg ... (from bin/hr_render.cjs)  ->  <out.mp4>, <dir>/qc.jpg (every 12th frame), <dir>/qc_zoom/ (full-size caption moments if lint.json exists)
# Ship gates (print FAIL and exit 1): frame count == audio length, duration within 40 ms, peak <= -1 dBTP after AAC, no clipping.
set -euo pipefail
D=${1:?dir}; A=${2:?audio}; O=${3:?out.mp4}; FPS=${4:-30}
EXT=jpg; [ -f "$D/frames/0000.png" ] && EXT=png
N=$(ls "$D/frames" | grep -c "\.$EXT$")
ffmpeg -v error -y -framerate "$FPS" -i "$D/frames/%04d.$EXT" -i "$A" -map 0:v -map 1:a -c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p \
  -c:a aac -b:a 192k -shortest "$O" </dev/null
VD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$O"); AD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$A")
python3 - "$N" "$FPS" "$VD" "$AD" <<'E'
import sys
n, fps, vd, ad = int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
exp = n / fps
print(f"frames {n} = {exp:.2f}s | mp4 {vd:.2f}s | audio {ad:.2f}s")
if abs(exp - ad) > 0.04: print(f"FAIL: audio is {ad:.2f}s but the picture is {exp:.2f}s (trim or pad the mix)"); sys.exit(1)
E
LOUD=$(ffmpeg -i "$O" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" | tr -s ' ' | tr '\n' ' ')
echo "loudness: $LOUD"
ffmpeg -v error -y -i "$O" -vf "select='not(mod(n,12))',scale=130:-1,tile=15x4" -frames:v 1 -update 1 "$D/qc.jpg" </dev/null
echo "QC sheet: $D/qc.jpg  (a sparse sheet shows structure, NOT text: also read full-size frames at every caption)"
if [ -f "$D/lint.json" ]; then
  mkdir -p "$D/qc_zoom"
  python3 - "$D/lint.json" "$FPS" <<'E' | while read -r f; do ffmpeg -v error -y -i "$O" -vf "select=eq(n\,$f),scale=540:-1" -frames:v 1 -update 1 "$D/qc_zoom/$(printf %04d $f).jpg" </dev/null; done
import json, sys
fps = float(sys.argv[2]); d = json.load(open(sys.argv[1]))
seen = set()
for r in d["script"]:
    f = r["from"] + min(8, (r["to"] - r["from"]) // 2)   # a settled moment, not the first frame of a slam
    if f not in seen: seen.add(f); print(f)
E
  echo "caption frames: $D/qc_zoom/ ($(ls "$D/qc_zoom" | wc -l) files): READ THEM, spelling and glyphs included"
fi
