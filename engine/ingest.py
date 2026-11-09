"""Step 1 of a vox edit: source video -> everything the planner needs, in one go.

  python3 ingest.py [video] <work>
    video  defaults to the newest video in ~/Downloads
  writes <work>/src30.mov (CFR 30fps 1080x1920 mezzanine), stt.json (ElevenLabs Scribe, word timings),
  transcript.txt (sentences with source times + the gaps that get cut), faces_NN.jpg (expression sheets,
  one cell per 0.5s, for picking cut-out frames) and a plan.json skeleton if none exists.
"""
import json, os, subprocess, sys, pathlib, urllib.request, uuid

SKILL = pathlib.Path(__file__).resolve().parent.parent
args = sys.argv[1:]
if len(args) == 1:
    vids = [p for p in (pathlib.Path.home() / "Downloads").iterdir() if p.suffix.lower() in (".mp4", ".mov", ".m4v", ".webm")]
    args = [str(max(vids, key=lambda p: p.stat().st_mtime))] + args
SRC, WORK = pathlib.Path(args[0]).resolve(), pathlib.Path(args[1]).resolve()
WORK.mkdir(parents=True, exist_ok=True)
print("source:", SRC)


def key():
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"]
    for line in (SKILL / ".env").read_text().splitlines():
        if line.startswith("ELEVENLABS_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("No ELEVENLABS_API_KEY in env or " + str(SKILL / ".env"))


def run(cmd):
    subprocess.run(cmd, check=True)


cfr = WORK / "src30.mov"
if not cfr.exists():
    # Frame-exact cutting needs constant frame rate; phone/WhatsApp video is VFR. Fills 9:16 (centre crop).
    run(["ffmpeg", "-y", "-v", "error", "-i", SRC, "-vf",
         "fps=30,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1",
         "-af", "aresample=48000", "-c:v", "libx264", "-crf", "10", "-preset", "medium", "-c:a", "pcm_s16le", cfr])

stt = WORK / "stt.json"
if not stt.exists():
    wav = WORK / "audio.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", cfr, "-vn", "-ac", "1", "-ar", "16000", wav])
    b = uuid.uuid4().hex
    body = b"".join([
        f'--{b}\r\nContent-Disposition: form-data; name="model_id"\r\n\r\nscribe_v1\r\n'.encode(),
        f'--{b}\r\nContent-Disposition: form-data; name="timestamps_granularity"\r\n\r\nword\r\n'.encode(),
        f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="a.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode(),
        wav.read_bytes(), f"\r\n--{b}--\r\n".encode()])
    req = urllib.request.Request("https://api.elevenlabs.io/v1/speech-to-text", data=body, method="POST",
                                 headers={"xi-api-key": key(), "Content-Type": f"multipart/form-data; boundary={b}"})
    stt.write_bytes(urllib.request.urlopen(req, timeout=300).read())

d = json.loads(stt.read_text())
words = [w for w in d["words"] if w["type"] == "word"]
lines, cur = [], []
for i, w in enumerate(words):
    cur.append(f"{w['text']}@{w['start']:.2f}")
    gap = words[i + 1]["start"] - w["end"] if i + 1 < len(words) else 0
    if w["text"].endswith(("।", "?", ".", "!")) or gap > .6:
        lines.append(" ".join(cur) + (f"   [gap {gap:.2f}s]" if gap > .28 else "")); cur = []
if cur: lines.append(" ".join(cur))
(WORK / "transcript.txt").write_text(f"language: {d.get('language_code')}\n" + "\n".join(lines) + "\n")
print((WORK / "transcript.txt").read_text())

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", cfr],
                           capture_output=True, text=True).stdout)
# Expression sheets: 8x4 cells, 0.5s apart -> cell k of sheet n is at n*16 + k*0.5 seconds.
for n in range(int(dur // 16) + 1):
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(n * 16), "-t", "16", "-i", cfr, "-vf",
         "fps=2,crop=1080:1100:0:120,scale=200:-1,tile=8x4", "-frames:v", "1", WORK / f"faces_{n:02d}.jpg"])
print(f"expression sheets: faces_00..{n:02d}.jpg  (cell k of sheet n = {16}*n + 0.5*k seconds)")

plan = WORK / "plan.json"
if not plan.exists():
    plan.write_text(json.dumps({
        "source": str(SRC), "output": str(WORK.parent / (SRC.stem.replace(' ', '-') + "-vox.mp4")),
        "fps": 30, "end_card": 2.6, "cut": {"pad": .09, "max_gap": .28}, "music": {"volume": .75},
        "punch": {}, "scenes": [], "end_scene": "endCard", "end_props": {},
        "sfx": [{"k": "whoosh2", "out": 0, "v": .45}, {"k": "thump", "out": .02, "v": .5},
                {"k": "whoosh2", "at": "end", "v": .55}, {"k": "thump", "at": "end", "plus": .05, "v": .8}]}, indent=1))
    print("wrote plan.json skeleton")
