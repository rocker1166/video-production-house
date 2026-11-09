#!/usr/bin/env python3
"""Brief → reel spec. A reel is a list of ACTS (library + length + cut rule) plus captions; cuts land on the song's beats.
Usage: make.py <format> <place> <song> [options] [--render]          (place = library name; a label for multi-place formats)
  title      --text "LADAKH"                              one place word, centred
  mood       --text "OFFICE KE BAHAR..."                   one handwritten line
  audio                                                   no text: the song carries it
  solution   --words "Monday,EMI,..." --text "Ilaaj: Spiti 🏔️" [--intro 6]   pain words on black, one per beat, then the place
  story      --lines "setup|punchline" [--intro 2.3]      setup line, punchline on the cut
  lyrics     --lyrics library/music/<slug>.lyrics.json    the song's own words
  drone      --text "Kerala 🌿" [--hold 4]                 a few long aerial holds, tiny place tag
  flip       --lines "Everyone wants this|But I want this[|closing line]" [--from city] [--intro 6]
             act 1 = the normal life (city library), act 2 = the place; contrast and myth-buster reels
  quote      --text "Leaving home to go home..." [--look soft|bold] [--hold 3.5]   slow shots under one top line
  listicle   --places "ladakh,spiti,kashmir" --text "Header|sub"   header, then one place name per act
  itinerary  --text "3-day Manali itinerary 📥|Save this" --steps "DAY 1|Old Manali cafes;DAY 2|Solang valley"
  pov        --text "pov: you finally take that long-awaited trip ✈️" [--from journey]   journey shots, then the place
  voice      --vo <slug from voice.py> --places "ladakh,kerala" [--text "fixed top hook"]   narration + word captions
  cinematic  --text "HIMACHAL PRADESH"                    16:9 clips letterboxed (use a *-wide library), tiny serif label
  recap      --route "DELHI → BIR BILLING|5N/6D" --days "STRANGERS,DAY 1,DAY 2,FAMILY"   group-trip story cards
Common: --every N (cut every N beats) --len SEC --seed N --grade cinematic|natural
song: a slug prepared by song.py (library/music/<slug>.json); bin/bgm.py lists them."""
import argparse, json, random, re, statistics, subprocess, sys
from pathlib import Path
import os

os.dup2(os.open(os.devnull, os.O_RDONLY), 0)  # ffmpeg reads stdin: in a shell `while read` loop it would eat the remaining commands

import os as _os
ROOT = Path(_os.environ.get("REEL_HOME") or Path(__file__).resolve().parent.parent)  # data dir (per brand)
ENGINE = Path(__file__).resolve().parent.parent
FPS = 30
# Shot kinds from the Pexels slug; consecutive shots rotate kinds so the reel never shows three roads in a row.
KINDS = {"aerial": ("aerial", "drone", "above"),
         "road": ("road", "motor", "drive", "truck", "bridge", "pass", "gondola", "train", "railway"),
         "water": ("lake", "river", "waterfall", "stream", "shikara", "boat", "backwater"),
         "culture": ("flag", "prayer", "buddha", "monastery", "temple", "statue", "wheel", "stupa", "monk", "bell", "procession"),
         "life": ("market", "street", "camel", "horse", "hiker", "fabric", "village", "people", "man-", "walk", "cricket", "cow", "mule",
                  "child", "woman", "worker", "elephant")}
PERSON = ("man-", "hiker", "people", "woman", "boys", "child", "tourists", "youth", "worker", "walker")
SRCS = {}


# Caption words → slug words, so a step about a Volvo gets a road/bus shot (itinerary, quote).
SYN = {"volvo": ("road", "drive", "bus"), "bus": ("road", "drive", "bus"), "cafes": ("street", "market", "village", "town"),
       "cafés": ("street", "market", "village", "town"), "bonfire": ("night", "camp", "tent"), "stars": ("night", "camp"),
       "tunnel": ("road", "drive", "pass"), "trek": ("hiker", "trail", "walk"), "temple": ("temple", "monastery")}
STOP = {"with", "your", "this", "that", "from", "only", "know", "real", "next", "trip", "save", "plan", "have", "when", "what", "travellers"}


def want_from(text):
    ws = {w.lower() for w in re.findall(r"[A-Za-zé]{4,}", text)} - STOP
    return tuple(ws | {s for w in ws for s in SYN.get(w, ())}) or None


def kind(slug):
    if "indian-flag" in slug:  # a flagpole is not an iconic prayer-flag opener (it opened 4 Manali reels)
        return "land"
    return next((k for k, words in KINDS.items() if any(w in slug for w in words)), "land")


def probe_len(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                capture_output=True, text=True).stdout)


def motion(folder):
    """Mean frame-to-frame change per clip (cached). Near-still shots score low and get dropped."""
    cache = folder / "motion.json"
    m = json.loads(cache.read_text()) if cache.exists() else {}
    for f in sorted(folder.glob("*.mp4")):
        if f.name in m or f.name.endswith(".part.mp4"):
            continue
        r = subprocess.run(["ffmpeg", "-v", "error", "-t", "8", "-i", f, "-vf",
                            "fps=6,scale=96:-2,format=gray,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
                            "-f", "null", "-"], capture_output=True, text=True).stdout
        ys = [float(l.split("=")[1]) for l in r.splitlines() if "YAVG" in l]
        m[f.name] = round(statistics.mean(ys[1:]), 3) if len(ys) > 2 else 0
    cache.write_text(json.dumps(m, indent=0))
    return m


class Pool:
    """A library's clips in play order: stillest quarter dropped, kinds round-robin, iconic (culture) first."""

    def __init__(self, lib, rng, need):
        folder = ROOT / "library/clips" / lib
        if not folder.is_dir():
            sys.exit(f"no library {lib}: fetch it first (pexels.md)")
        mot = motion(folder)
        files = [f for f in sorted(folder.glob("*.mp4")) if not f.name.endswith(".part.mp4")]
        if len(files) > need * 1.3:
            cut = sorted(mot[f.name] for f in files)[len(files) // 4]
            files = [f for f in files if mot[f.name] >= cut]
        pool = {}
        for f in files:
            pool.setdefault(kind(SRCS.get(f.name, f.stem)), []).append(f)
        for v in pool.values():
            rng.shuffle(v)
        kinds = list(pool)
        rng.shuffle(kinds)
        kinds.sort(key=lambda k: k != "culture")
        self.order = []
        while any(pool.values()):
            for k in kinds:
                if pool[k]:
                    self.order.append(pool[k].pop())
        self.lib, self.seed = lib, rng.random()

    def take(self, want=None):
        if not self.order:
            sys.exit(f"library {self.lib} ran out of clips: fetch more, raise --every, or shorten the reel")
        if want:  # e.g. a person for the payoff shot, an aerial for drone holds; rotate by seed so sibling reels differ
            score = {f: sum(w in SRCS.get(f.name, "") for w in want) for f in self.order}
            best = max(score.values(), default=0)
            hits = [f for f in self.order if best and score[f] == best]  # most caption words matched ("snow" + "valley" beats "valley")
            if hits:
                f = hits[int(self.seed * len(hits))]
                self.order.remove(f)
                return f
        return self.order.pop(0)


def snap(t):
    return round(t * FPS) / FPS


def A(lib, end=None, beats=None, every=None, hold=None, want=None, first=None):
    """One act: until `end` seconds (snapped to a beat) or for `beats` beats; cut every N beats or hold ~`hold` s per shot.
    `want` = slug words every shot prefers (aerial for drone); `first` = slug words for the act's first shot (a person)."""
    return {"lib": lib, "end": end, "beats": beats, "every": every, "hold": hold, "want": want, "first": first}


def cap(text, at, end, style, fade=0.25):
    return {"text": text, "at": round(at, 4), "dur": round(end - at, 4), "style": style, "fade": fade}


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("format", choices=["title", "mood", "audio", "solution", "story", "lyrics", "drone", "flip", "quote", "listicle",
                                      "itinerary", "pov", "voice", "cinematic", "recap"])
    a.add_argument("place"); a.add_argument("song")
    for k in ("text", "words", "lines", "places", "steps", "route", "days"):
        a.add_argument(f"--{k}", default="")
    a.add_argument("--lyrics"); a.add_argument("--vo"); a.add_argument("--from", dest="src", default=None)
    a.add_argument("--look", default="soft", choices=["soft", "bold"])
    a.add_argument("--intro", type=float); a.add_argument("--hold", type=float); a.add_argument("--every", type=int, default=1)
    a.add_argument("--len", type=float); a.add_argument("--seed", type=int, default=1); a.add_argument("--grade", default="cinematic")
    a.add_argument("--render", action="store_true")
    o = a.parse_args()
    f = o.format
    need = {"title": o.text, "mood": o.text, "solution": o.text and o.words, "story": "|" in o.lines, "lyrics": o.lyrics,
            "drone": True, "flip": "|" in o.lines, "quote": o.text, "listicle": o.places and o.text, "itinerary": o.steps and o.text,
            "pov": o.text, "voice": o.vo and o.places, "cinematic": o.text, "recap": o.route and o.days, "audio": True}
    if not need[f]:
        sys.exit(f"format {f}: missing its options (see --help)")
    rng = random.Random(o.seed)
    SRCS.update({Path(json.loads(l)["file"]).name: json.loads(l)["slug"] for l in (ROOT / "library/clips/SOURCES.jsonl").read_text().splitlines()})
    song = json.loads((ROOT / "library/music" / f"{o.song}.json").read_text())
    beats = [snap(b) for b in song["beats"]]
    lyr = json.loads((ROOT / o.lyrics).read_text()) if o.lyrics else None
    vo = json.loads((ROOT / "library/voice" / f"{o.vo}.json").read_text()) if o.vo else None
    places = [p.strip() for p in o.places.split(",") if p.strip()]
    P, E = o.place, o.every

    def beat_near(t):
        return min(beats, key=lambda b: abs(b - t))

    # ---- acts + caption plan per format; caption builders get the act bounds once cuts are known ----
    default_len = {"drone": 9, "quote": 8, "flip": 14}.get(f, 15)
    L = o.len or (lyr["end"] - song["start"] if lyr else vo["dur"] + 0.8 if vo else default_len)
    intro = o.intro
    if f in ("title", "mood", "audio", "lyrics", "cinematic"):
        acts = [A(P, L, every=E)]
    elif f == "solution":
        acts = [A("black", intro or 6.0), A(P, L, every=E, first=PERSON)]
    elif f == "story":
        acts = [A(P, intro or 2.3, every=E), A(P, L, every=E, first=PERSON)]
    elif f == "drone":
        acts = [A(P, L, hold=o.hold or 4, want=("aerial", "drone"))]
    elif f == "flip":
        acts = [A(o.src or "city", intro or L * 0.45, every=E), A(P, L, every=E, first=PERSON)]
    elif f == "quote":
        acts = [A(P, L, hold=o.hold or 3.5, want=want_from(o.text))]
    elif f == "listicle":
        acts = [A(places[0], intro or 2.4, every=8)] + [A(p, beats=max(E, 2), every=max(E, 2)) for p in places]
    elif f == "itinerary":
        steps = [s.split("|", 1) for s in o.steps.split(";") if s.strip()]
        acts = [A(P, intro or 2.4, every=8)] + [A(P, beats=4, every=2, want=want_from(txt)) for _, txt in steps]
    elif f == "pov":
        acts = [A(o.src or "journey", intro or L * 0.4, every=E), A(P, L, every=E, first=PERSON)]
    elif f == "recap":
        days = [d.strip() for d in o.days.split(",") if d.strip()]
        acts = [A(P, intro or 2.4, every=8, want=PERSON)] + [A(P, beats=4, every=2, want=PERSON) for _ in days]  # a group story: people everywhere
    elif f == "voice":
        # One act per spoken sentence, cycling through the places; act changes sit on the sentence's first word.
        # edge-tts word timings carry no punctuation: take sentence lengths (in words) from the script text.
        # edge-tts can also merge words into one token ("Tea gardens"), so a sentence ends at the token holding its last word.
        lasts = [re.findall(r"[\w']+", s)[-1].lower() for s in re.split(r"[.!?]+", vo["script"]) if re.findall(r"[\w']+", s)]
        sents, cur, k = [], [], 0
        for w in vo["words"]:
            cur.append(w)
            if k < len(lasts) and re.findall(r"[\w']+", w[2].lower())[-1:] == [lasts[k]]:
                sents.append(cur); cur, k = [], k + 1
        if cur:
            sents.append(cur)
        acts = [A(places[i % len(places)], (sents[i + 1][0][0] + 0.25) if i + 1 < len(sents) else L, every=2) for i in range(len(sents))]

    # ---- bounds: act ends on beats (voice: on words), then cuts inside each act ----
    bounds, t = [], 0.0
    for i, act in enumerate(acts):
        if act["beats"]:
            later = [b for b in beats if b > t + 0.3]
            end = later[min(act["beats"], len(later)) - 1] if later else L
        elif f == "voice":
            end = snap(act["end"])
        elif i < len(acts) - 1:
            end = beat_near(min(act["end"], L))
        else:  # the reel ends on the last beat at or before L
            end = max([b for b in beats if t + 0.6 < b <= L + 0.01], default=snap(L))
        bounds.append((t, end))
        t = end
    total = t
    if total > song["len"] + 0.01:
        sys.exit(f"reel is {total:.1f}s but {o.song}.json only has beats for {song['len']}s: rerun song.py with a bigger --len")

    pools, clips = {}, []
    for act, (s, e) in zip(acts, bounds):
        if act["lib"] == "black":  # a black card is one shot, whatever its length
            pts = []
        elif act["hold"]:
            pts, k = [], s + act["hold"]
            while k < e - act["hold"] * 0.5:
                pts.append(beat_near(k)); k += act["hold"]
        else:
            ev = act["every"] or 1
            lo = s + (0.6 if s == 0 else 0.3)  # the opening shot gets at least 0.6s
            pts = [b for b in beats[::ev] if lo <= b <= e - 0.3]
        # Skip a cut that would leave a shot under 0.3s (merge it into its neighbour), never drop the shot:
        # dropping shortened the act and slid every caption after it off its pictures (reel 009, 190 bpm).
        cuts = [s]
        for p in sorted(set(pts)):
            if p - cuts[-1] >= 0.3 and e - p >= 0.3:
                cuts.append(p)
        cuts.append(e)
        shots = [round(y - x, 4) for x, y in zip(cuts, cuts[1:])]
        if act["lib"] == "black":
            clips += [{"color": "black", "dur": d} for d in shots]
            continue
        lib = act["lib"]
        if lib not in pools:
            pools[lib] = Pool(lib, rng, 20)  # shortcut: assumes ~20 shots per library; libraries over 26 clips lose their stillest quarter
        for j, d in enumerate(shots):
            clip_file = pools[lib].take(act["first"] if j == 0 and act["first"] else act["want"])
            room = probe_len(clip_file) - d - 0.5
            c = {"file": str(clip_file.relative_to(ROOT)), "start": round(rng.uniform(0.5, max(0.5, room)), 2), "dur": d}
            if lib.endswith("-wide"):
                c["fit"] = "letterbox"
            clips.append(c)
    total = round(sum(c["dur"] for c in clips), 4)
    # captions are timed from act bounds: the clips must fill those bounds exactly
    assert abs(total - bounds[-1][1]) < 0.02, f"clips {total}s != acts {bounds[-1][1]}s"
    b0, bl = bounds[0], bounds[-1]

    caps = []
    if f in ("title", "mood", "cinematic"):
        caps = [cap(o.text, 0, total, {"title": "title", "mood": "mood", "cinematic": "film"}[f])]
    elif f == "drone":
        caps = [cap(o.text or P.title(), 0, total, "label")] if o.text != "-" else []
    elif f == "quote":
        caps = [cap(o.text, 0, total, "quote" if o.look == "soft" else "hook")]
    elif f == "solution":
        words = [w.strip() for w in o.words.split(",") if w.strip()]
        slots = [0.0]
        for b in beats:
            if b < b0[1] - 0.4 and b - slots[-1] >= 0.45:
                slots.append(b)
        starts = slots[: len(words)]  # one word per beat; the last (the punch) holds until the drop
        for i, (w, at) in enumerate(zip(words, starts)):
            caps.append(cap(w, at, starts[i + 1] if i + 1 < len(starts) else b0[1], "pain", 0.08))
        caps.append(cap(o.text, b0[1], total, "small"))
    elif f in ("story", "flip"):
        parts = [s.strip() for s in o.lines.split("|")]
        st = "story" if f == "story" else "hook"
        caps = [cap(parts[0], 0, b0[1], st, 0.15)]
        close = parts[2] if len(parts) > 2 else None
        end_b = max(b0[1] + 1.5, total - 2.4) if close else total
        caps.append(cap(parts[1], b0[1], end_b, st, 0.15))
        if close:
            caps.append(cap(close, end_b, total, st, 0.15))
    elif f == "lyrics":
        word = lyr.get("mode") == "word"
        ls = [(snap(tm - song["start"]), txt) for tm, txt in lyr["lines"]]
        for i, (at, txt) in enumerate(ls):
            end = min(ls[i + 1][0] if i + 1 < len(ls) else total, total)
            if end - at > 0.2:
                caps.append(cap(txt, at, end, "lyricword" if word else "lyric", 0.05 if word else 0.15))
    elif f == "listicle":
        head, _, sub = o.text.partition("|")
        caps = [cap(head, 0, b0[1], "listhead", 0.15)] + ([cap(sub, 0, b0[1], "listsub", 0.15)] if sub else [])
        caps += [cap(p.replace("-", " ").title(), s, e, "place", 0.08) for p, (s, e) in zip(places, bounds[1:])]
    elif f == "itinerary":
        head, _, sub = o.text.partition("|")
        caps = [cap(head, 0, b0[1], "hook", 0.15)] + ([cap(sub, 0, b0[1], "small", 0.15)] if sub else [])
        for (day, text), (s, e) in zip(steps, bounds[1:]):
            caps += [cap(day.strip(), s, e, "day", 0.1), cap(text.strip(), s, e, "step", 0.1)]
    elif f == "pov":
        caps = [cap(o.text, 0, total, "pov")]
    elif f == "recap":
        route, _, sub = o.route.partition("|")
        caps = [cap(route, 0, b0[1], "route", 0.15)] + ([cap(sub, 0, b0[1], "routesub", 0.15)] if sub else [])
        caps += [cap(d, s, e, "recap", 0.1) for d, (s, e) in zip(days, bounds[1:])]
    elif f == "voice":
        if o.text:
            caps.append(cap(o.text, 0, total, "hook"))
        ws = vo["words"]
        for i, (s, e, w) in enumerate(ws):
            nxt = ws[i + 1][0] if i + 1 < len(ws) else min(e + 0.6, total)
            caps.append(cap(w.strip(".,!?"), snap(s + 0.3), min(snap(nxt + 0.3), total), "word", 0.04))

    name = f"{o.place}-{f}-{o.song}-s{o.seed}"
    spec = {"name": name, "format": f, "place": o.place, "song": o.song, "xfade": 0, "grade": o.grade, "clips": clips,
            "music": {"file": song["file"], "start": song["start"], "fadeOut": 0.6}, "captions": caps}
    if vo:  # the narration starts 0.3s in; the song becomes a quiet bed under it
        spec["voice"] = {"file": vo["file"], "at": 0.3}
        spec["music"]["volume"] = 0.18
    out = ROOT / "spec" / f"{name}.json"
    out.write_text(json.dumps(spec, indent=1, ensure_ascii=False))
    print(f"{out.relative_to(ROOT)}: {len(clips)} shots, {total:.1f}s, {len(caps)} captions, song from {song['start']}s")
    if o.render:
        subprocess.run([sys.executable, ENGINE / "bin/render.py", out], check=True)


if __name__ == "__main__":
    main()
