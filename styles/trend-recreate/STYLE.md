# Style: Trend recreate (same structure, our footage)

From the Studio day-6 reel. Rebuild a trend's structure; never copy its media.

- Find the reference's cut point with per-frame 1x1 luma (`scale=1:1 -pix_fmt gray`), not the scene filter. Align to an `aubiotrack` beat.
- Hook = free-licence stock (Mixkit works with plain curl: `mixkit.co/free-stock-video/<q>/`, files at `assets.mixkit.co/videos/<id>/<id>-{720,1080,2160}.mp4`), jump-cut on the song's beats.
- The payload (screen, product) is an original HTML render. Text goes through HTML, not ffmpeg: this ffmpeg has no `drawtext`.
- Do not bake the song in. Post with Instagram "Use audio" from the reference at 0:00 so the cut lands on the beat.
- Stock 4K crop gives SAR 1214:1215: add `setsar=1` on both branches before concat. Keep `html` (not just `body`) transparent for PNG overlays.
- Freeze gate on a screen recording: a constant slow push-in (1.0 -> 1.14x over ~11 s) plus visible activity between steps, or small typing reads as a hold.
- Budget missed here (70 min vs 30): two full re-renders. Sample-check before the full render.
