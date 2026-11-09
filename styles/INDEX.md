# Style registry

`seed` = written from lessons, no example video in the repo yet. `proven` = has an `approved` run in `ledger/runs.jsonl`.
Autonomy per style: `python3 ledger/house.py score`.

| Style | Use when | Pipeline | Status |
|---|---|---|---|
| `vox` | raw UGC/talking head -> paper-editorial explainer Reel | skill `video-editing` | proven (Demo invoice) |
| `vox-film` | a script -> narrated Remotion film, paper collage, 16:9 or 9:16 | `styles/vox-film/` | seed (upstream vox-skill, ships its own example) |
| `beatcut` | topic/subject -> stock-footage reel cut on a song's beats or a voiceover, any brand | skill `reel-factory` | proven in travel, untested elsewhere |
| `carousel` | topic -> 1080x1350 art-led slides + PDF, any brand | skill `carousel-factory` | proven in travel, untested elsewhere |
| `html-teaser` | brand/launch teaser with no footage: kinetic type, logo reveal, HTML seeked to frames | `styles/html-teaser/` | seed |
| `trend-recreate` | copy a trending reel's structure with our own footage/screen | `styles/trend-recreate/` | seed |

Add a style: skill `style-forge`. Every style = `STYLE.md` + `examples/` + (earned) `RULES.md`.
