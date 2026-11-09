#!/usr/bin/env bash
# New HTML-seek reel from the story-intro template.  rf <brand> bin/hr_new.sh <name>  ->  work/<name>/ in the brand workspace
# Then: edit CFG at the top of work/<name>/index.html, and follow template-stack-intro/README.md.
set -euo pipefail
N=${1:?name}; E="$(cd -P "$(dirname "$0")" && cd .. && pwd)"; R="${REEL_HOME:-$E}"
mkdir -p "$R/work/$N/assets"; HOUSE="$(cd "$E/.." && pwd)"
sed "s#__HOUSE__#$HOUSE#g" "$E/template-stack-intro/index.html" > "$R/work/$N/index.html"; cp "$E/template-stack-intro/mix.json" "$R/work/$N/"
echo "work/$N ready (put your own card images/voice in work/$N/assets). render:  rf <brand> node bin/hr_render.cjs work/$N --lint"
