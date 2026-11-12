# AIAsleep v004: farm package (Connect29)

43.5 s vertical short (1080×1920, 60 fps, frames 1–2610). A driver's in-car attention AI keeps flagging him as asleep because his epicanthic folds partly cover the iris. One continuous camera, no cuts. Animated-CG look per `blender/STYLE_ANIMATED.md`.

## Files
- `AIAsleep_v004_60fps.blend`: packed and compressed (61 MB, normal git file, no LFS). Verified with `--factory-startup`: 0 unpacked images, no linked libraries, renders.
- `beats.json`: beat start frames and first words for `pipeline/retime_to_vo.py` (no VO yet; built to the brief's target times).
- `SETTINGS.md`, `CREDITS.md` (with the CC-BY block for the video description).
- `package_check_lowres.jpg`: factory-startup test render (frames 120, 1650, 1950, 2350).
- Review material: `blender/AIAsleep_v001/review/` (1/s sheet, hand close-ups, hand audit, camera clearance).
- Source scripts: `blender/AIAsleep_v001/scripts/01…05` (driver, set, animation, fold + section, look + hands), plus `audit.py`, `hand_audit.py`, `cam_clearance.py`.

## Beats
1 scan beam + face mesh · 2 red closed-eye alarm · 3 confused · 4 sits up, re-grips · 5 forced wide eyes → green · 6 relax → red, exhale · 7 time-lapse drive with rhythmic red flashes · 8 into the dash camera: IR grade, tracking box, iris circle · 9 dive into a sagittal lid cross-section (skin, orbicularis, orbital fat, tarsus, rim bone, eyeball) on the sky-blue gradient · 10 fold over the inner corner, iris circle flickers red · 11 pull back out of the car, which drives on.

## Audits
- Hands (every 2 frames, 1305 frames): hand vs hand 0, hand vs own torso/shirt 0, hand vs head 0. The rim check flags 1–2 finger-bone axis samples inside the rim on grip frames. That is the rim inside the curled fist; close-ups show the fingers wrapping with no visible clipping.
- Camera clearance (every 2 frames): only the intended ≤6-frame skin dive at 1803–1805, plus brief near-passes at 121–123 (window frame) and 1311 (sun visor).
- Feet planted all film (static IK targets).

## Director fixes applied after C (00:17 UTC)
- 15 s: the push-in is sharp (f/9) and pulled back, so the eyes and brows read.
- 30 s: the dive into the cutaway is 9 frames earlier, so the 1/s sample lands on the readable section. The approach is frontal.
- 22 s: the roof drops out only for frames 1305–1318 while the camera rises; no murky frame.
- 23–24 s: dark asphalt now tiles at real scale (the plank streaks are gone), with lane lines and glowing street lamps sweeping past.
- Light panels are invisible to the camera (the blue blob is gone).
- The eye socket skin inside the eyeballs is culled, and the medial sclera is matte.
- 31 s: an added section key keeps the cutaway in frame.

## Audits
- Hand audit (`review/D_hand_audit.txt`), every 2 frames over 1305 frames: hand vs hand 0, hand vs torso/shirt 0, hand vs head 0. The rim check flags 1–2 finger-bone axis samples inside the rim on grip frames: the rim is inside the curled fist, and the close-ups show a clean wrap.
- Camera clearance (`review/D_camera_clearance.txt`): 2 brief near-passes on the window frame at frames 121–123 as the camera enters the car.

## Known issues
- No voiceover yet; retime with `beats.json` when it arrives.
- A faint dark squiggle shows at the inner corner of his right eye in the steep close-up just before the dive (about 0.2 s). It is refraction in the MPFB procedural eye.
- The epicanthic fold is a modest shape key and is subtle at medium distance. The side-by-side ghost eye without the fold is not built.
- 21 s is a close over-the-shoulder shot during his hand gesture.
- The IR grade uses the compositor (CPU device set); keep compositing enabled on the farm.

## v004 changes (director, 00:41 UTC)
- 31 s: an added section key keeps the eye cutaway in frame (no cyan blank).
- 21 s: an over-the-shoulder cabin fill (`CabinFill_Rear`) lifts the near-black frame.
- 16 s: a HUD/console fill (`HUD_Fill`), and the whip to the screen stays forward of the wheel, so the green eye icon reads from 16.3 s.
- The fill lights are invisible to the camera. Everything else is unchanged from v002; the hand audit counts are unchanged.

## v004: acting pass (client, Nov 12; `blender/briefs/ACTING_FIX_04-10.md`)
The full problem list and fixes are in `blender/AIAsleep_v001/review/ACTING_notes.md`. Before and after half-second sheets: `review/v004_before_half_s_{A,B}.jpg` and `review/v004_after_half_s_{A,B}.jpg`.
- Blinks move the lids only (brows no longer snap). No blink lands on "he wasn't sleeping".
- Head shake is two natural swings instead of a six-swing buzz.
- The exhale and the sigh no longer gape (jaw 2°); they read through his shoulders and head.
- The 20 s gesture is a small, relaxed open-palm lift just above the rim, not a high claw.
- He breathes (clavicles), makes steering corrections, and glances at the mirror.
- Camera: every framing that was filled by his head, shoulder, mouth or headliner, or that went inside his face (28.5 s), is re-staged on the passenger side. Camera and aim keys use clamped handles, so the path can't overshoot.
- Story-beat frames are unchanged (`beats.json` is identical).
- Checks: director `clip_scan.py` gives 0 bad ranges. Hand audit: hand vs hand, torso/shirt and head all 0 (rim-in-fist samples as before). Camera clearance shows only the window-frame entry and the intended skin dive.
