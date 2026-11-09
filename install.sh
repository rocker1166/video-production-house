#!/usr/bin/env bash
# One-shot setup for macOS, Linux (apt, dnf, pacman) and Windows via WSL2. Safe to rerun.
#   bash install.sh            installs what is missing, creates .env, runs the doctor and the ledger self-test
#   SEG=1 bash install.sh      also installs the person-cut-out backend (rembg); automatic on Linux/WSL
# Windows: use WSL2 (Ubuntu). In PowerShell run `wsl --install -d Ubuntu`, then run this script inside Ubuntu.
set -euo pipefail
cd "$(dirname "$0")"
OS=$(uname -s)
have() { command -v "$1" >/dev/null 2>&1; }
case "$OS" in
  Darwin)
    have brew || { echo "Install Homebrew first: https://brew.sh"; exit 1; }
    for b in ffmpeg aubio yt-dlp node python3; do have "$b" || { f=$b; [ "$b" = python3 ] && f=python@3.12; echo "installing $f"; brew install "$f"; }; done
    [ -d "/Applications/Microsoft Edge.app" ] || [ -d "/Applications/Google Chrome.app" ] || brew install --cask microsoft-edge
    xcode-select -p >/dev/null 2>&1 || { echo "Run: xcode-select --install   then rerun this script"; exit 1; } ;;
  Linux)
    if have apt-get; then SUDO=""; have sudo && SUDO=sudo
      $SUDO apt-get update -qq && $SUDO apt-get install -y -qq ffmpeg aubio-tools nodejs npm python3 python3-venv python3-pip curl fonts-noto fonts-noto-color-emoji
      have yt-dlp || python3 -m pip install --user --break-system-packages -q yt-dlp || python3 -m pip install --user -q yt-dlp
    elif have dnf; then sudo dnf install -y ffmpeg-free aubio nodejs npm python3 python3-pip yt-dlp google-noto-sans-fonts
    elif have pacman; then sudo pacman -S --needed --noconfirm ffmpeg aubio nodejs npm python python-pip yt-dlp noto-fonts
    else echo "Unsupported distro: install ffmpeg, aubio, node, python3 (+venv), yt-dlp yourself, then run engine/doctor.sh"; exit 1; fi
    SEG=1 ;;
  MINGW*|MSYS*|CYGWIN*) echo "Native Windows is not supported. Use WSL2: in PowerShell run  wsl --install -d Ubuntu  then rerun this script inside Ubuntu."; exit 1 ;;
  *) echo "Unsupported OS: $OS"; exit 1 ;;
esac
# onnxruntime (needed by rembg) has no wheels for the very newest Python: prefer 3.12, 3.11, 3.13, 3.10
for p in python3.12 python3.11 python3.13 python3.10; do have "$p" && { export PYTHON=$p; break; }; done
[ -f .env ] || cp .env.example .env
bash engine/doctor.sh || true
[ "${SEG:-0}" = 1 ] && { .venv/bin/pip install -q -r requirements-seg.txt || echo "WARN: rembg install failed; person cut-outs and plate effects will be unavailable (check your Python version)"; bash engine/doctor.sh >/dev/null || true; }
python3 ledger/house.py selftest
echo "Done. Open Claude Code in this folder (cd $(pwd) && claude); skills, commands and hooks load from .claude/."
