# NoPilotPlane_v003: farm package

First-person hypothetical, 73.5 s at 1080×1920 and 60 fps (frames 1–4410), ready for RenderStreet. No render has been submitted.

- `NoPilotPlane_v003_60fps.blend`: the self-contained scene. Every texture is packed. One camera, `CAM_Film`, in one continuous move.
- `SETTINGS.md`: render settings and suggested test frames.
- `CREDITS.md`: the CC-BY block for the video description (one model: "Seat" by maximmus).
- `beats.json`: beat start frames for the VO retime. There is no voiceover yet; the film is built to the brief's target times. When the VO arrives, run `pipeline/retime_to_vo.py` with those frames as the old anchors.

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
- **No voiceover yet.** Beats are on the brief's target times. Retime with `pipeline/retime_to_vo.py` when the VO arrives. Beat 19 starts at frame 4315; the float-out starts at 71.4 s (frame 4285).
- **Contacts** (`../NoPilotPlane_v001/review/audit_C*.txt`):
  - YOU's hands sink into the first officer's jacket while hauling him (29–32 s). They grab cloth, but it is not a clean surface contact.
  - The throttle touch is about 17 cm short for 3 frames at 59.5 s.
  - About 0.3 s of foot hover while YOU sits into the right seat (38–39 s).
- **Cabin:** a few passengers' knees sit close to the seat back in front (the real seat model leaves tighter knee room than the old procedural seats).
- **Exterior:** the town under the dive is box-instanced and reads as busy noise at small sizes. The ground is a procedural patchwork with distance haze; there are no photo-scanned terrain textures.
- **Captain on the floor:** posed once and static. He doesn't react to the dive.
- **Changed from v002:** instrument modules (standby instruments, clock, gear lever with three greens, knob modules) fill the plain area below the main displays, and the cockpit floor is a ribbed rubber mat. Everything else is identical to v002.
