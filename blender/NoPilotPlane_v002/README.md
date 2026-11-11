# NoPilotPlane_v002: farm package

First-person hypothetical, 73.5 s at 1080×1920 and 60 fps (frames 1–4410), ready for RenderStreet. No render has been submitted.

- `NoPilotPlane_v002_60fps.blend`: the self-contained scene. Every texture is packed. One camera, `CAM_Film`, in one continuous move.
- `SETTINGS.md`: render settings and suggested test frames.
- `CREDITS.md`: the CC-BY block for the video description (one model: "Seat" by maximmus).
- `beats.json` (in `../NoPilotPlane_v001/`): beat start frames for the VO retime. There is no voiceover yet; the film is built to the brief's target times. When the VO arrives, run `pipeline/retime_to_vo.py` with those frames as the old anchors.

## How it is built
Source: `../NoPilotPlane_v001/scripts/`. Build order:
1. `01_build_humans.py` once per character (YOU, CAPT, FO, PA–PF), MPFB2 + MakeHuman CC0 assets
2. `patch_logos.py` and `make_displays.py` (texture prep: emblems painted out of 3 shirts; symbol-only cockpit displays)
3. `02_build_set.py` (cabin, real seat model, galley, door, cockpit, exterior)
4. `03_animate.py` (passengers, pilots, YOU, props, flight profile, alarms, camera bake)
5. `04_package.py` (texture shrink + `pipeline/package_for_farm.py`)

The camera is the eye point of the MPFB body "YOU" (head bone tracks the authored look), so the hands, arms and legs in frame are real geometry. From 71.4 s the camera leaves the head and floats round to YOU's face (reveal by 72.6 s, settle to 73.5 s).
The airliner never moves: attitude, altitude and speed live on `EXT_ROT` / `EXT_MOVE`, which carry the ground, towns, field, clouds, birds, sky dome and sun.

## Known issues
(filled in at packaging)
