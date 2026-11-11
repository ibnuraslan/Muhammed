# BellyFat_v003: farm package (replaces v002)

This is the full 21.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted. Use v003; v002 is kept only as a safety copy.

- `BellyFat_v003_60fps.blend`: the self-contained scene, with every texture packed. One camera, `CAM_Film`.
- `SETTINGS.md`: render settings, the visibility-swap note, the geometry-nodes note, test frames and the VO retime steps.
- `CREDITS.md`: everything is CC0 or made for the film, so no CC-BY block is needed in the video description.
- `beats.json` and `anchors_template.json`: inputs for the voiceover retime.
- `package_check_lowres.jpg`: frames 60, 400, 1000 and 1270 from the packed file opened in factory Blender, at 20 % and 4 samples.

The source is `../BellyFat_v001/` (`build.sh`, then `scripts/`). The review sheets are `../BellyFat_v001/stills/v003_polish_sheet_*.jpg` and the audit is `../BellyFat_v001/audit_v003.txt`.

## What changed from v002 (director notes after B and C)
- **Fat:** about 7.5k tightly packed, overlapping 3–11 mm lobules, instanced by geometry nodes.
  - The deformation runs live off the bullet: radial push, squash ahead of the tip, a ripple scaled by the energy absorbed, a damped settle wobble after the stop, and a heartbeat pulse.
  - The look is pale creamy SSS with a wet coat and light septa at the lobule seams, with thin, wavy, branching capillaries on the cut face.
- **Bowel:** coiled small-bowel loops about 2.3 cm across, with tight touching folds. They have glossy pink-grey serosa with a vessel network, a mesentery sheet with vessels, a dark cavity behind, and a slow drift.
- **Muscle:** tighter bundles, striation bump and a wet coat.
- **Block and backdrop:** the block is 1.7× taller, so its edges rarely show, and the cyan gradient is deeper.
- **Swap:** the same procedural 1 mm weave in MacroRoot space on both the real tee and the macro fabric.
  - Focus locks onto the fabric plane when the camera is close, so the swap frames show weave detail.
  - The entry hole is on both the real tee and the macro fabric.
- **Beat 6:** a 1.2 s whip half-orbit in the middle of the orbit, plus the lobule settle and heartbeat.
- **Beat 7:** shopper A turns, steps toward her beside his cart and reaches out.
- **Store life:** a stocker holding a carton down the aisle (he turns at the bang), and a browsing shopper (she turns to look). Store lights are lowered.

## Known issues
- **No voiceover yet.** The film is timed to the brief's beat table. Retime with `beats.json` when the VO arrives.
- **The ending is short.** She is on screen for 1.3 s after the pull-out, a limit of the 21.5 s target.
- **The beat 6 orbit stays on the open cut-face side.** The far side is inside the tissue block.
- **The bowel's peristalsis** is a slow noise drift, not a travelling contraction wave.
- **f121 slow-motion ramp.** It is deliberate, and the audit flags it as a speed jump.
