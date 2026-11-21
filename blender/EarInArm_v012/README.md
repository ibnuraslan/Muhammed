# EarInArm_v012: fixes for the client's rejection of v011 (synced to your voiceover)

This is built from Connect01's EarInArm scripts (`../EarInArm_v001/scripts/`), with the v012 fixes below. It is retimed to the same voiceover and timing as v011 (`../briefs/sync/01.anchors.json`, frames **1–1572**). v011 is untouched.

- `EarInArm_v012_60fps.blend`: the self-contained scene, with every texture packed.
- `EarInArm_v012_VO.mp3`: the voiceover, the same recording as v011. It is also packed into the .blend as the scene's sound strip.
- `beats.json`: beat start frames on the VO: 1, 109, 301, 463, 649, 907, 1129, 1267, 1447; end 1572.
- `SETTINGS.md` (render settings) and `CREDITS.md`.
- `review/preview.mp4`: a 270×480 preview rendered from this exact package, every 2nd frame at 30 fps (real time), with the frame number in the corner and the VO.
- `review/*.json`: qa_check, clip_scan, limb_check, cam_clear and body_prop_cross on this package.

## v012 vs v011 (client rejection)
1. **Patient:**
   - He has real short MPFB hair: short02, rebound to his head bone and shrinkwrapped to the scalp. He is not bald.
   - His skin is warmer and natural, with dark brown irises, the eye fix and a camera catchlight on every character.
   - The 3-second stare (old frames 216–295, now about 3.6–4.9 s) is alive: three blinks, a breath, and a head turn to glance at the surgeon, with a slow push-in.
2. **Ear grafts / headphones:** the white gauze disc is now a soft, skin-toned ear shape (subdivided, smooth), sitting close to the head.
3. **Crotch framing:** the 77–155 shot (now about 1.3–2.6 s) is a waist-up two-shot.
   - The surgeon's hands examine the patient's left forearm on the armrest, where the pocket will go.
   - His idle hands stay at his own chest height, and there is no forceps reach toward the patient.
   - The forceps appear only from the cut to the tray.
4. **Staff:**
   - The nurse's bob is back under her cap (she was bald), and both caps sit over the hair.
   - Scrub tops and trousers are different shades: surgeon light teal over dark teal, nurse light blue over navy.
   - Masks cover the nose and mouth, so faces and eyes read.
5. **Arm on the board:**
   - The elbow is bent and the palm is up.
   - On the board the patient is awake and relaxed: he breathes, blinks, and turns his head toward the arm and the surgeon. He rests with his eyes closed only in the waiting shot.
6. **Set:**
   - Warm wall paint and warmer key lights.
   - Framed posters on three walls (abstract colour, no text).
   - A tall blue-and-white cabinet, a sink unit with a steel basin and tap, a wall clock, and a chair rail round the room.

## Frame mapping
The times in the rejection notes match the v011 shots when read as 30 frames per second of the 60 fps file (e.g. 4.5–5.2 s ≈ v011 frames 135–157 = the forearm two-shot; 7.1–9.7 s = the worried close-up; ~11 s = the nurse at the tray; 21–25 s = the arm on the board). Each fix was checked on that shot, and also on the shots at the same times read at 60 fps.
