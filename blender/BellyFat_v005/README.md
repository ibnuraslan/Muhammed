# BellyFat_v005: farm package, animated look (replaces v004)

This is the full 21.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted. Use v004. v003 and v002 are kept only as safety copies.

- `BellyFat_v005_60fps.blend`: the self-contained scene, with every texture packed. One camera, `CAM_Film`.
- `SETTINGS.md`: render settings, the visibility-swap note, the geometry-nodes note, test frames and the VO retime steps.
- `CREDITS.md`: one CC-BY model, the "Small and large intestine" model by antonia.sundberg. **Paste its credit line into the video description.** Everything else is CC0 or made for the film.
- `beats.json` and `anchors_template.json`: inputs for the voiceover retime.
- `package_check_lowres.jpg`: frames 60, 400, 1100 and 1270 from the packed file opened in factory Blender, at 20 % and 4 samples.

The source is `../BellyFat_v001/` (`build.sh`, then `scripts/`). The review sheets are `../BellyFat_v001/stills/v005_sheet_1s.jpg` and the audit is `../BellyFat_v001/audit_v004 (geometry and animation are unchanged from v004).txt`.

## v005: animated-CG look (client, 22:45 UTC; blender/STYLE_ANIMATED.md)
Geometry, animation and camera are the same as v004. Only the look changed:
- `pipeline/anim_look.py`: AgX Punchy, saturation ×1.25, bump ×0.35, roughness at least 0.35, f-stop at least 5.6, motion blur off, lights ×1.25.
- `BellyFat_v001/scripts/05_animated_look.py`:
  - explainer layers: peach skin, yellow-orange lumpy fat, red-pink muscle, clean glossy pink bowel, red and blue vessels
  - bright sky-blue dome gradient (#E8F7FF to #4FC3F7)
  - warm-gold energy rings
  - a small clean red entry mark (no wound gore)
  - keyed f-stops clamped to 5.6 or higher, exposure −0.3
- Review sheet: `BellyFat_v001/stills/v005_sheet_1s.jpg` (1 still per second, 270×480, 8 samples).

## What changed from v002 (director notes after B and C, and the client's "no blocks" rule for v004)
- **Fat:** about 7.5k tightly packed, overlapping 3–11 mm lobules, instanced by geometry nodes.
  - The deformation runs live off the bullet: radial push, squash ahead of the tip, a ripple scaled by the energy absorbed, a damped settle wobble after the stop, and a heartbeat pulse.
  - The look is pale creamy SSS with a wet coat and light septa at the lobule seams, with thin, wavy, branching capillaries on the cut face.
- **Bowel:** a real CC-BY small- and large-intestine model, cropped into the cavity behind the peritoneum. It has our glossy pink-grey serosa with a vessel network, a mesentery sheet and a dark cavity behind, plus a slow drift.
- **Muscle:** tighter bundles, striation bump and a wet coat.
- **Block and backdrop:** the block is 1.7× taller, so its edges rarely show, and the cyan gradient is deeper.
- **Swap:** the same procedural 1 mm weave in MacroRoot space on both the real tee and the macro fabric.
  - Focus locks onto the fabric plane when the camera is close, so the swap frames show weave detail.
  - The entry hole is on both the real tee and the macro fabric.
- **Beat 6:** a 1.2 s whip half-orbit in the middle of the orbit, plus the lobule settle and heartbeat.
- **Beat 7:** shopper A turns, steps toward her beside his cart and reaches out.
- **Store realism (client "no blocks" rule):** bevelled cartons with jitter, rimmed cans and shouldered glass bottles (lathe profiles), wire front rails and blank shelf tags. I looked for real CC models first: the product models all carry real brands, so they could not be used, and the shelving models were plain panel units.
- **Store life:** a stocker holding a carton down the aisle (he turns at the bang), and a browsing shopper (she turns to look). Store lights are lowered.

## Known issues
- **No voiceover yet.** The film is timed to the brief's beat table. Retime with `beats.json` when the VO arrives.
- **The ending is short.** She is on screen for 1.3 s after the pull-out, a limit of the 21.5 s target.
- **The beat 6 orbit stays on the open cut-face side.** The far side is inside the tissue block.
- **The bowel's peristalsis** is a slow noise drift, not a travelling contraction wave.
- **Bowel distance.** The nearest bowel loop sits about 5 cm behind the stopped bullet, deeper than the brief's "just short". The peritoneum sheet lies between them.
- **f121 slow-motion ramp.** It is deliberate, and the audit flags it as a speed jump.
