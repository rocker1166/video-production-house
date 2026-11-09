#!/bin/bash
# Contact sheets, the cheap look before the expensive render.
#   qc.sh <work> stills   -> <work>/qc/sheet.png   one still per scene (render.cjs --stills), 6 per row
#   qc.sh <work> final    -> <work>/qc/final_NN.jpg the composed reel at 2fps, 10x10 per sheet
set -euo pipefail
S="$(cd "$(dirname "$0")" && pwd)"; W="$(cd "$1" && pwd)"
if [ "$2" = stills ]; then
  rm -f "$W"/qc/*.png
  node "$S/render.cjs" "$W" --stills
  names=$(python3 -c "import json;print(' '.join(j['name'] for j in json.load(open('$W/jobs.json'))))")
  args=(); f=""; i=0; labels=""
  for n in $names; do args+=(-i "$W/qc/$n.png"); f+="[$i:v]format=rgba,scale=360:-1,pad=370:650:5:5:color=0x777777[p$i];"; labels+="[p$i]"; i=$((i+1)); done
  # pad the grid to whole rows of 6
  while [ $((i % 6)) -ne 0 ]; do f+="color=c=0x777777:s=370x650:d=1[p$i];"; labels+="[p$i]"; i=$((i+1)); done
  rows=""; r=0
  for ((k=0; k<i; k+=6)); do f+="$(for j in 0 1 2 3 4 5; do printf "[p$((k+j))]"; done)hstack=6[r$r];"; rows+="[r$r]"; r=$((r+1)); done
  if [ $r -gt 1 ]; then f+="${rows}vstack=$r[out]"; else f+="${rows}null[out]"; fi
  ffmpeg -v error -y "${args[@]}" -filter_complex "$f" -map "[out]" -frames:v 1 "$W/qc/sheet.png"
  echo "$W/qc/sheet.png"
else
  out=$(python3 -c "import json;print(json.load(open('$W/plan.json'))['output'])")
  rm -f "$W"/qc/final_*.jpg
  ffmpeg -v error -y -i "$out" -vf "fps=2,scale=216:-1,tile=10x10" "$W/qc/final_%02d.jpg"
  ls "$W"/qc/final_*.jpg
fi
