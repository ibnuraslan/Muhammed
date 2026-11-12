# NoPilotPlane_v005: farm package (animated look, hands pass, director v005 notes)

First-person hypothetical, 73.5 s at 1080×1920 and 60 fps (frames 1–4410), ready for RenderStreet. No render has been submitted. This is the version to render. v002–v004 are superseded.

- `NoPilotPlane_v005_60fps.blend`: 41 MB, every texture packed, a normal git file (no LFS). One camera, `CAM_Film`, in one continuous move.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block ("Seat" by maximmus).
- `beats.json`: beat start frames for `pipeline/retime_to_vo.py`. There is no voiceover yet; the film is timed to the brief's target times.
- Review: `../NoPilotPlane_v001/review/v5_1s_sheet_A_0-39s.jpg`, `v5_1s_sheet_B_40-73s.jpg`, `v5_hands_closeups_sheet.jpg`, `audit_hands_v5.txt`.

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

## v005 changes (director notes)
- **Door (11.6–12.2 s):**
  - The door starts ajar (28°) because the captain fell against it.
  - YOU pushes it flat against the wall in 0.25 s, at 11.74–11.98 s, and walks 12 cm further from the hinge.
  - The camera turns right into the cockpit.
  - The door now fills the frame for about 0.3 s instead of about 3 s.
- **15 s:** the cabin carpet no longer runs into the cockpit (it was z-fighting into black). The cockpit floor mat is lighter, with a soft fill light above the captain, so his legs rest on a visible floor.
- **First officer:**
  - Face turned toward the cabin and chin down (seated).
  - Lighter navy uniform with the MakeHuman fabric normal map back at full strength (folds, seams, collar, tie), and value lifted.
  - YOU starts the haul 10 cm further back, so both men read.
- **Radio (21–26 s):** the handset is light grey and slightly larger, so the fingers read as wrapped around it rather than as an empty claw.
- **Hands:** a hold key on the right-hand door frame after the push (it no longer sweeps through YOU's own chest).

## Hand audit (`audit_hands.py`, every 2 frames, 2,205 samples)
5,188 vertex hits in 175 samples (v004: 6,495; before the hands pass: 43,399):
- **Own clothes and body (3,980):** short forearm-over-shirt brushes during big reaches. These are at 0 s and 9.0–9.4 s (armrests), 15.8–16.5 s (headrest), 17.6–19.8 s, 26.6–26.9 s, 31.9–32.7 s and 64.9–66.3 s.
- **The first officer (896):** fingers resting on the jacket and sleeve at 28.5–29.1 s and 29.9–30.9 s while he swings back.
- **Hand against hand (312):** 27.4–27.5 s.

The last re-key (a 10 cm step back at 26.9–27.8 s, and the first officer's seated head turn cut from 55° to 30°) came after this audit run, so the counts are for the build just before it.

## Known issues
- The hits above are not 0. None reads as a hand through a body in the close-ups, but they are listed for the client.
- Review stills need at least 24 samples on the face frames. At 8 samples the procedural eyes read black; at 48 samples with these light paths they are blue.
- The captain on the floor is static. The dive town is box-instanced.
