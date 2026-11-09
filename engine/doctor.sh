#!/bin/bash
# One-shot environment check + self-repair. Every line is a trap that cost time on a past run.
S="$(cd "$(dirname "$0")" && pwd)"; ok=1
say() { printf "%-6s %s\n" "$1" "$2"; if [ "$1" = FAIL ]; then ok=0; fi; return 0; }
command -v ffmpeg >/dev/null && say ok "ffmpeg" || say FAIL "ffmpeg missing (brew install ffmpeg)"
BR=$(node "$S/browser.cjs" 2>/dev/null) && say ok "browser: $BR" || say FAIL "no Edge/Chrome/Chromium (install one, or: npx playwright install chromium)"
PW="$HOME/.cache/reeltools/node_modules/playwright"
if [ ! -d "$PW" ]; then mkdir -p ~/.cache/reeltools && (cd ~/.cache/reeltools && npm init -y >/dev/null && npm i -s playwright@1.55.1); fi
[ -d "$PW" ] && say ok "playwright $(node -p "require('$PW/package.json').version")" || say FAIL "playwright install failed"
[ -x "$S/../.venv/bin/python" ] || { "${PYTHON:-python3}" -m venv "$S/../.venv" && "$S/../.venv/bin/pip" install -q -r "$S/../requirements.txt"; }
PYC="import PIL, numpy, edge_tts"; "$S/../.venv/bin/python" -c "$PYC" 2>/dev/null || "$S/../.venv/bin/pip" install -q -r "$S/../requirements.txt" 2>/dev/null
"$S/../.venv/bin/python" -c "$PYC" 2>/dev/null && say ok "python deps" || say FAIL "venv broken"
if [ "$(uname)" = Darwin ] && { [ -x "$S/cutout" ] || swiftc -O "$S/cutout.swift" -o "$S/cutout" 2>/dev/null; }; then say ok "person cut-out: Apple Vision"
elif "$S/../.venv/bin/python" -c "import rembg" 2>/dev/null; then say ok "person cut-out: rembg"
else say WARN "no person cut-out backend: needed only for plate effects and paper cut-outs. Run: .venv/bin/pip install -r requirements-seg.txt"; fi
([ -f "$S/../.env" ] && grep -q "^ELEVENLABS_API_KEY=.\+" "$S/../.env") || [ -n "$ELEVENLABS_API_KEY" ] && say ok "ElevenLabs key" || say WARN "no ELEVENLABS_API_KEY (optional: only for AI voice, sfx, speech-to-text)"
n=$(ls "$S/../assets/sfx"/*.mp3 2>/dev/null | wc -l | tr -d ' ')
[ "$n" -ge 20 ] && say ok "SFX cache ($n sounds, never regenerate)" || say FAIL "SFX cache has $n sounds"
[ "$ok" = 1 ] && echo "READY" || { echo "NOT READY"; exit 1; }
