---
name: carousel-factory
description: Make Instagram/LinkedIn carousels for ANY product or niche - 1080x1350 slides, art-led (AI-generated pictures) or photo-led, brand colours and wordmark, optional real app screens in a phone frame, exported as numbered PNGs plus a review PDF. Six art variants. Use on "/carousel", "make a carousel", "carousel for <topic>", "next carousel", "same carousel in another style", for a brand that has been onboarded.
---

# Carousel factory: topic in, numbered slides out (any brand)

`C=carousel/cf <brand>` runs the engine inside `workspaces/<brand>/carousel/`. No workspace -> `brand-onboard`.
Read first: `brands/<brand>/BRAND.md` (claims!), `workspaces/<brand>/carousel/LEARNINGS.md`, `carousel/design-philosophy.md`.

## 0. Brief
Hook slide, 3-5 content slides, end slide. Slide 1 carries the whole promise (it decides saves and sends). One idea per slide, headline up to 8 words, one line of body.
Claim only what the product does and what BRAND.md allows. Sponsored/creator content gets its required label. The end slide uses the brand's `end_cta`.

## 1. Variant = the design
`$C variants` lists them: illustrated, realistic, watercolour, retro, collage, clay. Set `"variant"` in the spec or override with `--variant v` (writes to `<slug>~<v>/`, so one spec lives in every design side by side).
One variant per carousel; keep a consistent variant per subject so the grid reads as a set. Add a variant = an entry in `styles.json` (prompt + type: family, weight, upper, italicEm, kicker) + the font file in `carousel/fonts/`.
A `workspaces/<brand>/carousel/styles.json` overrides the shipped ones; `art/anchor.png` is the approved look that `useRef` styles copy (technique and palette only).

## 2. Spec
`specs/<slug>.json`, copy `carousel/specs/example.json`: top-level `variant`, `subject` (what the pictures show, niche context), `brand` (optional per-spec override), `slides`.
Per slide: `key`, `scene` (the picture), `kick`, `h` (wrap the one key word in `<em>`), `p`, `lab`, `sign`, `tone` (`light`|`dark`), `pick` (`a`|`b`), `phone: {src, off}`, `photo`.
Scenes: people small and from behind, calm top third for the headline, **no text or signs in the picture** (the model garbles them: say "blank paper").

## 3. Generate, look, pick
`$C jobs <slug>` prints the cost (about $0.13 per image) - **ask the owner above the brand's `image_budget_usd`**. `$C gen <slug>` needs `GEMINI_API_KEY` (env or repo `.env`). One seed per scene; a second only for a hero shot.
`$C sheet <slug>` -> `art/<slug>/_sheet.jpg`: read it, set `pick`, redo a bad slide with `--only key`. Reroll for noise, rewrite the scene only for a prompt bug.

## 4. Real product screens
Capture screens of the real product into the workspace (simulator, browser, screenshots) and list what each shows and what is safe to publish in an `INDEX.md`. Never publish screens with real people's names, chats or notifications.

## 5. Render and review
`$C render <slug>` -> `out/<slug>/slide-NN.png`; `$C pdf <slug>` also writes `pdf/<slug>.pdf` (LinkedIn takes the PDF, Instagram takes the PNGs in order). Needs Microsoft Edge (set `EDGE=` for another path); headless Chrome can be SIGKILLed in sandboxes.
Read every slide at full size: type clears the picture, nothing overlaps, the phone never covers the caption, the brand name and colours are right.

## 6. Hand off and learn
Give the posting order, file paths and what is still placeholder. **Never post.** The reply is the verdict: `house.py verdict last ... --tags` + a dated rule in the workspace `LEARNINGS.md`. `house.py log` it (style `carousel`).
