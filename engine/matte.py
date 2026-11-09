#!/usr/bin/env python3
"""Cross-platform person matte (Linux, Windows/WSL, or macOS without Xcode). Same contract as matte.swift:
  matte.py <in.mov> [balanced|accurate]  ->  raw gray8 540x960 frames on stdout, one per input frame.
Needs `pip install -r requirements-seg.txt` (rembg + onnxruntime; first run downloads the u2net_human_seg model, ~170 MB).
CPU only: roughly 0.3-1 s per frame, so a 45 s clip takes minutes (Apple Vision does it in about a minute)."""
import subprocess, sys
import numpy as np
from PIL import Image
from rembg import new_session, remove

W, H = 540, 960
src = sys.argv[1]
session = new_session("u2net_human_seg")
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       stdout=subprocess.PIPE, stdin=subprocess.DEVNULL)
out, prev, n, size = sys.stdout.buffer, None, 0, W * H * 3
while True:
    raw = dec.stdout.read(size)
    if len(raw) < size:
        break
    m = np.asarray(remove(Image.frombytes("RGB", (W, H), raw), session=session, only_mask=True), dtype=np.float32)
    m = m if prev is None else 0.65 * m + 0.35 * prev  # light temporal smoothing so edges do not shimmer
    prev = m
    out.write(m.astype(np.uint8).tobytes())
    n += 1
out.flush()
sys.stderr.write(f"matte frames: {n}\n")
