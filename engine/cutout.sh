#!/bin/bash
# Creator cut-outs for the paper scenes: frame at a source second -> Vision subject lift -> halftone,
# then (re)writes <work>/assets.js with every PNG in <work>/assets as data URIs (CSS masks refuse file:// images).
#   cutout.sh <work> name=seconds [name=seconds ...]     e.g. cutout.sh ugc/work shock=9.9 ask=29.0
#   cutout.sh <work>                                      just rebuild assets.js (after dropping a logo PNG in assets/)
set -euo pipefail
S="$(cd "$(dirname "$0")" && pwd)"; W="$(cd "$1" && pwd)"; shift
mkdir -p "$W/assets" "$W/cut"
PY="$S/../.venv/bin/python"
[ -x "$PY" ] || { "${PYTHON:-python3}" -m venv "$S/../.venv" && "$S/../.venv/bin/pip" install -q -r "$S/../requirements.txt"; }
# subject lift: Apple Vision on macOS (fast), rembg elsewhere (pip install -r requirements-seg.txt)
if [ "$(uname)" = Darwin ] && { [ -x "$S/cutout" ] || swiftc -O "$S/cutout.swift" -o "$S/cutout" 2>/dev/null; }; then LIFT=("$S/cutout"); else LIFT=("$PY" "$S/cutout.py"); fi
for pair in "$@"; do
  name="${pair%%=*}"; t="${pair#*=}"
  ffmpeg -v error -y -ss "$t" -i "$W/src30.mov" -frames:v 1 "$W/cut/raw_$name.png"
  "${LIFT[@]}" "$W/cut/raw_$name.png" "$W/assets/her_$name.png" >/dev/null
  "$PY" "$S/halftone.py" "$W/assets/her_$name.png" >/dev/null
  echo "her_$name  <- ${t}s"
done
"$PY" - "$W" <<'EOF'
import base64, json, pathlib, sys
a = pathlib.Path(sys.argv[1]) / "assets"
img = {p.stem: "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode() for p in sorted(a.glob("*.png"))}
(a.parent / "assets.js").write_text("window.IMG = " + json.dumps(img) + ";")
print("assets.js:", ", ".join(img))
EOF
