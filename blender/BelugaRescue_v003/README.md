# BelugaRescue_v003 — farm package (animated look + hands pass)

Changes from v002: the client's animated look (STYLE_ANIMATED.md): `anim_look.py` (AgX Punchy, saturation up, bump down, roughness ≥ 0.35,
motion blur off, f-stop ≥ 5.6 except the two story beats), sunny partly-cloudy sky instead of the hall, bright clear cyan water (thin volume),
icy-blue tiles/rock, clean white beluga (no scars), cyan→white explainer card, glossy pink calf muscle with cream tendon, solid-colour clothes
and shoes (removes a printed emblem from one MakeHuman T-shirt). Hands pass: Limit Rotation on all 288 finger/thumb/wrist bones, elbow IK limits,
arm-reach scaled per character, fixed an inverted "arm out" direction that crossed idle hands in front of the body, re-keyed claps, glass
touches, hand-over-mouth, buoy grip and calf grip. Hand audit: `../BelugaRescue_v001/review/hands_audit_v003.txt`.

The full 36.5 s film at 1080×1920, 60 fps, frames 1–2190, ready for RenderStreet. No render has been submitted.

- `BelugaRescue_v003_60fps.blend` (69 MB, compressed): self-contained; all 61 images are packed (textures resized to 1K, 2K for her skin and the HDRI). Plain git file (no LFS).
- `SETTINGS.md`: render settings read back from factory Blender, cost estimate, test frames.
- `CREDITS.md`: includes the **CC BY block for the video description** (calf-muscle anatomy model by Ruslan Gadzhiev).
- `beats.json`: start frame + first words of each of the 12 beats, for `pipeline/retime_to_vo.py` when the voiceover arrives.
- `camera_path.json`: the camera framings (frame, position, aim, lens) the continuous spline passes through.
- `package_check_f880_lowres.png`: 20 %, 4-sample frame rendered from the packed file in factory Blender — proves the package works, not a quality reference.

There is **no voiceover yet**: the film is built to the brief's target beat times. When the VO mp3 arrives:
1. `python transcribe.py vo.mp3` for word times,
2. write anchors from `beats.json` (each beat's frame → the second its first word is spoken),
3. `blender -b BelugaRescue_v003_60fps.blend --python pipeline/retime_to_vo.py -- anchors.json vo.mp3 out.blend`.
Everything that moves is keyframed (bubbles, droplets, X-ray, grade, camera), so the retime warps it all. The ocean surface, caustic gobo,
particulate drift and hair drift run on scene time and do not need warping.

Source: `../BelugaRescue_v001/scripts/` — build order `01_build_people.py`, `02_build_scene.py`, `03_animate.py`, `03b_fx_camera.py` (`scripts/build.sh`), then `scripts/package.sh 003`.
Review: `../BelugaRescue_v001/review/` (B blocking sheets, C 0.2 s polish sheets, contact close-ups, audits).

## Known issues
- Hand audit (every 2 frames diver / 6 frames others, > 4 mm): 11 544 samples in 736 frame-checks, all contact rather than wrong poses:
  her hands pressed on her calves while seated (6 035), fingers wrapped round the buoy tube (1 815), a resting hand at the hip pocket of two
  spectators (≈2 600), clapping palms meeting (≈250), the whale's lip brushing her hand on 2 approach frames (422). No backward bends (limits).
- Audit (BVH, every 10 frames): the palms sit 1–2 cm into the coping top at 34.8–36.3 s (raised slightly after the audit, not re-measured); a few stray whale-vs-diver samples during the push-up (24–33 s), not visible in the sheets; one frame (28.3 s) where the fluke tip dips ~7 cm into the tiles; fin tip into the tiles on 2 frames (9.0 s, 22.8 s); mask rim touches the face on 2 frames.
- The held foot is inside the beluga's mouth by design (lips within ~1–7 mm of the ankle).
- The beluga is our own sculpt (no usable CC-BY/CC0 beluga exists); close-ups at 20–23 s are its weakest angle.
- 28–29 s: the camera looks down on the top of her head for about a second while racing up.
- The above-water surface is quite reflective in the last 4 s.
- No voiceover yet (see above).
