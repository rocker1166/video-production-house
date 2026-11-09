---
description: Turn a reference video + script into scene-by-scene Gemini Omni/Veo video prompts
argument-hint: [paste your script, attach reference video/screenshots]
---

You are producing ready-to-paste AI video-generation prompts for the creator's social content. The user has attached a **reference video (or screenshots from it)** and pasted a **script**. Your job: study the reference's style and rewrite the script as per-scene prompts for an AI video generator (Gemini Omni Flash / Veo), where each clip is **max 10 seconds**.

If no reference video/screenshots are attached, or no script is provided, ask for the missing piece before continuing — do not invent a style.

The user's script / notes: $ARGUMENTS

## Step 1 — Analyze the reference deeply

Watch/read the reference and describe, concisely:
- **Animation style** — 2D, 3D, kinetic typography, flat, mixed media, etc.
- **Motion** — speed, easing, bounce vs smooth vs snappy
- **Transitions** — cuts, wipes, morphs, zooms
- **Color palette** — exact hex/named colors + background
- **Typography** — weight, animated or static, where text sits on screen
- **Camera** — static, zoom, pan, shake
- **Mood & pacing** — fast, calm, dramatic
- **Sound feel** — whooshes, clicks, bass hits, music genre

Keep this to a tight summary, not an essay.

## Step 2 — Break the script into scenes

Split the script into **8–10 second scenes**. Each scene = one AI clip. Keep on-screen text to **5–6 words max** per scene.

## Step 3 — Write one generation prompt per scene

For EACH scene, output a self-contained prompt (copy-paste into Gemini Omni / Veo) containing:
- What appears on screen and how it animates
- The exact on-screen text (≤6 words)
- Colors, background, typography matching the reference
- Camera movement
- Transition into the next scene
- Sound effects + music mood

## Output format

```
STYLE SUMMARY
<the analysis from Step 1, bullet form>

SCENE 1 (0–9s)
<full paste-ready prompt>

SCENE 2 (9–18s)
<full paste-ready prompt>
...
```

After the scenes, add a one-line reminder: *"On-screen text in AI video is often messy — fix final text in CapCut/Figma."*

Output the prompts directly in the chat so they can be copied. Do not write files unless asked.
