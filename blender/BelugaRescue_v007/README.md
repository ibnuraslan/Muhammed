# BelugaRescue_v007 — farm package (director notes on v006)

Moving preview of this exact file: `../BelugaRescue_v001/review/preview.mp4` (every 5th frame, frame numbers burned in);
contact pages `../BelugaRescue_v001/review/preview_pages_v007/`. Beat frames unchanged; no VO added.
- Whale beats 6–8 (800–1300): computed two-shots — her face and the whale in frame together, camera kept 1.2 m off the whale.
- Arms: bent, clawing up / loose and drifting; no straight T or starfish.
- Push up (1440–1975): the whale bites just behind its snout tip and is nudged off her leg; body_prop_cross shows 0 frames
  with leg/hip/body inside the whale (only the ankle in the mouth).
- Rise (1840–1900): more drift and sway; camera holds while she rises past it.
- Coping / end (1920–2190): top-down onto her face, then the wide shot with the nurse and keeper in full.
- Calf grip: palms on the calf, wider macro (whole leg connected), hands lift as the knee draws in.
- Water surface IOR 1.05 (keeps waves, removes most of the mirrored reflection from below).
QA `review/qa_v007.json`, clip scan `review/clip_scan_v007.json` (0 bad ranges), whale crossing `review/bpc_v007.json`.

The full 36.5 s film at 1080×1920, 60 fps, frames 1–2190, ready for RenderStreet. No render has been submitted.

- `BelugaRescue_v007_60fps.blend` (70 MB, compressed): self-contained; all 61 images are packed (textures resized to 1K, 2K for her skin and the HDRI). Plain git file (no LFS).
- `SETTINGS.md`: render settings read back from factory Blender, cost estimate, test frames.
- `CREDITS.md`: includes the **CC BY block for the video description** (calf-muscle anatomy model by Ruslan Gadzhiev).
- `beats.json`: start frame + first words of each of the 12 beats, for `pipeline/retime_to_vo.py` when the voiceover arrives.
- `camera_path.json`: the camera framings (frame, position, aim, lens) the continuous spline passes through.
- `package_check_f880_lowres.png`: 20 %, 4-sample frame rendered from the packed file in factory Blender — proves the package works, not a quality reference.

There is **no voiceover yet**: the film is built to the brief's target beat times. When the VO mp3 arrives:
1. `python transcribe.py vo.mp3` for word times,
2. write anchors from `beats.json` (each beat's frame → the second its first word is spoken),
3. `blender -b BelugaRescue_v007_60fps.blend --python pipeline/retime_to_vo.py -- anchors.json vo.mp3 out.blend`.
Everything that moves is keyframed (bubbles, droplets, X-ray, grade, camera), so the retime warps it all. The ocean surface, caustic gobo,
particulate drift and hair drift run on scene time and do not need warping.

Source: `../BelugaRescue_v001/scripts/` — build order `01_build_people.py`, `02_build_scene.py`, `03_animate.py`, `03b_fx_camera.py` (`scripts/build.sh`), then `scripts/package.sh 003`.
Review: `../BelugaRescue_v001/review/` (B blocking sheets, C 0.2 s polish sheets, contact close-ups, audits).

## Known issues
- Hand audit (every 2 frames diver / 6 frames others, > 4 mm): 26 631 samples in 587 frame-checks (from 571 045 before the pass), all contact rather than wrong poses:
  the keeper's palms and fingers wrapped round the ring-buoy tube at 33–36 s (16 902 — the buoy is now carried by his actual hands), her hands pressed on her
  calves while seated (6 035), two spectators' resting hands at the hip pocket (2 644), whale lip brushing her hand on 2 approach frames (422),
  clapping palms meeting / her hands touching at the coping (585). No backward bends (Limit Rotation on all finger, thumb and wrist bones).
- Also fixed in v007: the black strip on the deck edge (coplanar wall top), the buoy floating below the keeper's hands.
- Audit (BVH, every 10 frames): the palms sit 1–2 cm into the coping top at 34.8–36.3 s (raised slightly after the audit, not re-measured); a few stray whale-vs-diver samples during the push-up (24–33 s), not visible in the sheets; one frame (28.3 s) where the fluke tip dips ~7 cm into the tiles; fin tip into the tiles on 2 frames (9.0 s, 22.8 s); mask rim touches the face on 2 frames.
- The held foot is inside the beluga's mouth by design (lips within ~1–7 mm of the ankle).
- The beluga is our own sculpt (no usable CC-BY/CC0 beluga exists); close-ups at 20–23 s are its weakest angle.
- 28–29 s: the camera looks down on the top of her head for about a second while racing up.
- The above-water surface is quite reflective in the last 4 s.
- No voiceover yet (see above).
