# NoPilotPlane_v004: farm package (new animated look + hands pass)

First-person hypothetical, 73.5 s at 1080×1920 and 60 fps (frames 1–4410), ready for RenderStreet. No render has been submitted. This is the version to render. v002 and v003 are in the old photoreal look and are superseded.

- `NoPilotPlane_v004_60fps.blend`: 41 MB, every texture packed, a normal git file (no LFS). One camera, `CAM_Film`, in one continuous move.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block ("Seat" by maximmus).
- `beats.json`: beat start frames for `pipeline/retime_to_vo.py`. There is no voiceover yet; the film is timed to the brief's target times.
- Review: `../NoPilotPlane_v001/review/v4_1s_sheet_A_0-39s.jpg`, `v4_1s_sheet_B_40-73s.jpg`, `hands_closeups_sheet.jpg`, `audit_hands_v4.txt`.

## What changed from v002
**Look (client LOOK CHANGE, `STYLE_ANIMATED.md`):**
- `pipeline/anim_look.py`: AgX Punchy, saturation ×1.25, bump ×0.35, roughness at least 0.35, no motion blur.
- `scripts/05_look_tune.py`:
  - sky dome: clean cyan to near-white
  - lighter ground haze
  - light grey-blue cockpit panels with wear contrast cut to 25 %
  - a light liner
  - navy uniforms for the pilots
  - a soft area box over the cockpit, plus face, door and galley fills
  - exposure +0.3
  - original eye, teeth and lash shaders kept
- Camera shake halved and the breathing sway reduced (no handheld look). A light jolt is kept in the dive.

**Hands (client HANDS rule):**
- **Joint limits:** 1,664 Limit Rotation constraints (local space) on every finger, thumb and wrist bone of every character. Fingers curl forward only, ±10° spread, thumb ±30°. Wrists ±60° flex and ±25° side. YOU's elbows have IK limits.
- **Haul (27.9–33.2 s):** the left hand grips the first officer's collar and the right hand the top of his near shoulder. Both are re-keyed every 8 frames from his moving bones and sit outside the jacket.
- **Yoke:** palms on the horns, fingers curled 78°, thumb opposing.
- **Throttle:** the hand closes on the lever knob at 59.2–59.8 s; the reach gap is closed (YOU leans across).
- **Other hand keys:**
  - the radio left hand holds the captain's headrest throughout
  - the aisle hand no longer touches a passenger's head (10.6 s)
  - the face-rub hands are kept apart (0.8 s)

## Hand audit (`audit_hands.py`, every 2 frames, 2,205 samples)
6,495 vertex hits in 178 samples (down from 43,399 in 322 before the pass):
- **Own clothes and body (5,460):** short brushes of the forearm over the shirt during big reaches. These are at 0 s and 9.0–9.4 s (pushing up from the armrests), 14–16.5 s (door frame and headrest grabs), 17.5–19.8 s, 21–23 s, 26.6–27.0 s and 64.9–67.7 s (twisting to look back).
- **The first officer (701):** fingers resting on the jacket at 28.6–29.0 s and 29.9–30.9 s while he swings back. Contact, not a hand through the body.
- **Hand against hand (334):** 27.4–27.5 s, as both hands reach for him.

## Known issues
- The hits above are not 0. None reads as a hand through a body in the close-ups, but they are listed for the client.
- Review stills need at least 24 samples on the face frames. At 8 samples the procedural eyes read black; at 48 samples with these light paths they are blue.
- The captain on the floor is static. The dive town is box-instanced.
