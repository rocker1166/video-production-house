# story-intro template (formats 17 `stack` / 25 story version)

A 14.5s vertical intro/teaser built as an HTML page: `seek(frame)` draws everything, Edge captures the frames, ffmpeg adds the audio.
Beats: hi/we are/brand + traveller cards -> "and we" zoom -> hero line -> **places** (full-bleed names) -> **crew** (counter-scrolling rows + chip)
-> **app** (3 phones rise) -> "with / you" -> teal iris -> logo. One idea and ONE motion per beat; every caption describes the picture.

```bash
bin/hr_new.sh my-intro                                  # work/my-intro/ (index.html + assets symlink + mix.json)
# 1. edit CFG at the top of work/my-intro/index.html (words, places, crew, phones, faces, beatA); photos go in spec/stack-intro/assets/
#    place photos: 1080x1920 jpg named full-<place>-<idx>.jpg; people: 720px jpg; clips live in library/clips (ffmpeg -ss 1 -frames:v 1)
node bin/hr_render.cjs work/my-intro --step 12 --out q  # sparse look first (structure only, 20s)
node bin/hr_render.cjs work/my-intro --lint # full render + CAPTION SCRIPT + overflow check (read the script aloud)
python3 bin/mix.py work/my-intro/mix.json work/my-intro/mix.wav
bin/hr_build.sh work/my-intro work/my-intro/mix.wav out/NNN-name.mp4   # encode + ship gates + QC sheet + full-size caption frames
```
Re-render only what changed: `--from 164 --to 238` (frames are overwritten in place), then `hr_build.sh` again.

## Audio (this template is timed to the ref's own cut)
`mix.json` = the ref's "Hi" + a quiet bit of the clean song + the ref's music from 2.16s (its whooshes are baked in). To use another song,
find ITS hits first: `.venv/bin/python bin/cues.py <song-or-reel> --out cues.json`, then move the beat frames in `layout()`
(hit1 f70, main hit f164, crew f239, app f281, clear f328, logo f384/399) onto the new hits. Do not align to the beat grid.

## Fonts (checked by hr_render: HR_FONTS)
Playfair Display 900 + italic, EB Garamond italic (small italic text), Geist Bold (brand, from hiring/the brand_Brand_Kit). Playfair italic draws `p` like `b` at ~100px.

## Assets are not in git (stock stills, icons, screens: ~19 MB)
Rebuild `spec/stack-intro/assets/` from: place stills = `ffmpeg -ss 1 -i library/clips/<place>/<clip>.mp4 -frames:v 1` (full-res for `full-*.jpg`, `scale=720:-1` for the rest),
clay icons = `design-ref/icons3d-trial/new-countries/*.png`, app screens + logo = `hiring/the brand_Brand_Kit/` (`app-screens/`, `logo/brand-logo-white.png`). File names used are in CFG.
