# NoPilotPlane_v006: farm package (animated look, hands pass, director v005 notes)

First-person hypothetical, 73.5 s at 1080×1920 and 60 fps (frames 1–4410), ready for RenderStreet. No render has been submitted. This is the version to render. v002–v005 are superseded.

- `NoPilotPlane_v006_60fps.blend`: 41 MB, every texture packed, a normal git file (no LFS). One camera, `CAM_Film`, in one continuous move.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block ("Seat" by maximmus).
- `beats.json`: beat start frames for `pipeline/retime_to_vo.py`. There is no voiceover yet; the film is timed to the brief's target times.
- Review: `../NoPilotPlane_v001/review/v6_1s_sheet_A_0-39s.jpg`, `v6_1s_sheet_B_40-73s.jpg`, `v6_hands_closeups_sheet.jpg`, `audit_hands_v6.txt`.

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

## v006 changes (director: the unconscious pilot read as a grey mannequin)
- **Uniform colour:** dark navy #1A2440 on the pilots' suits. A brightness mask keeps the MakeHuman shirt and tie areas of the texture, and the fabric normal map is at full strength, so the folds read. Settings are in `05_look_tune.py`.
- **Uniform pieces:** built in `03_animate.py` under `uniform()`, each held by a Child Of constraint on a bone so it moves with the body. 14 objects on the first officer and the captain:
  - four gold rings on each cuff
  - navy epaulettes with four gold bars
  - white collar points
  - a dark tie and knot
  - lapel edges with a light highlight line
  - a gold wing badge (shape only, no text)
  - a black belt with a gold buckle
  - a lighter crease line down each trouser front
- **Haul (29–31 s):** YOU steps back about 10 cm. The first officer's arm swings down onto the yoke instead of up toward the camera, so his body, arms, legs and the pedestal are all in frame.
- **Close-up check:** `../NoPilotPlane_v001/review/v6_first_officer_front_closeup.jpg` (a front test view, not in the film) shows the collar, striped tie, epaulette with four bars, lapels and cuff stripes.

## Hand audit (`audit_hands.py`, every 2 frames, 2,205 samples)
4,214 vertex hits in 137 samples (v005: 5,188; v004: 6,495; before the hands pass: 43,399):
- **Own clothes and body (3,450):** short forearm-over-shirt brushes during big reaches. These are at 0 s and 9.0–9.4 s, 15.8–16.5 s, 17.6–19.8 s, 31.9–32.8 s and 64.9–66.3 s.
- **Hand against hand (468):** 27.4–27.5 s.
- **The first officer's body (296):** fingers on his shoulder as he tips back, 30.3–30.9 s.

## Known issues
- The hits above are not 0. None reads as a hand through a body in the close-ups, but they are listed for the client.
- Review stills need at least 24 samples on the face frames. At 8 samples the procedural eyes read black; at 48 samples with these light paths they are blue.
- The captain on the floor is static. The dive town is box-instanced.
