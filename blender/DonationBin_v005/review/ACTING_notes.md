# DonationBin v005: acting notes (review of v004, then the fixes)

v004 frames are the timeline the director re-syncs to the VO. Every story-beat frame is unchanged (`beats.json` is identical).

The re-stage lives in `../../DonationBin_v001/scripts/06_acting_fix.py`, which is the director's draft, verified and extended. Build order: 01, 02, 03 (+03b), then 06, then 05 (look and hands), then 04 and package.

## Problems found in v004 (half-second sheet `review/BEFORE_v004_0p5s.jpg`)
| v004 frames | Problem | Fix in v005 |
|---|---|---|
| 1–73 | Her sill hand is a fist against her own chin (clip scan: hand inside her head), with the palm facing up. | The left palm lies flat, palm down, on the lip of the sill, further out. The right palm faces down inside the chute. Clip scan: 0. |
| 155–175 | The shover's hands are on her backside, and his head blocks the view. | His hands are placed by a ray-cast onto her upper back, at the shoulder blades. His start pose is 13 cm further back. |
| 200–215 | A shoe sole fills the frame as she goes through the chute. | The camera moves back and up (f215, f240). Her feet are small in the frame. |
| 240–360 | The somersault ends with her legs up the wall or in the air. | She tucks and rolls and lands on her back on the clothes. Knees are bent and feet are flat on the clothes by f280, there's a small bounce (f290–300), then a dazed lie. |
| 290–335 | The swinging flap passes through the camera, and frames are dark. | The camera ducks in under the open flap (f288) and stays outside the flap's swing radius. |
| 420–500 | A deep squat facing away, hands on the floor. | From lying she props up on her hands, sits up on the clothes with her knees bent and hands beside her, then turns her head and shoulders to the flap. |
| 600–680 | The crouch to stand is a snap. | She rolls onto one hip, kneels, plants one foot, then stands. |
| ~955 | The camera passes through the bin wall and her body (a blue blur). | The camera re-enters while the x-ray walls are still see-through (f880–905). After that it is keyed in front of her face, inside the bin. |
| 975–1090 | Hunched at the left wall; the camera sees the top of her head or the wall. | She stands upright, palms sliding up the smooth wall, looking up. The camera is at face height in front of her (face-tracked keys). |
| 1110–1165 | At the flap, the camera shows only the back of her head. | Face-tracked keys show her face and hands searching the flap edge. |
| 1180–1300 | The jump at the back wall shows only hair or wall. | Face-tracked keys, plus a corner camera low enough to see her face, looking up. |
| ~1315 | Her free hands pass through her chest between the jump and the scream (clip scan). | Her free hands are held forward, clear of her body. |
| 1320–1340 | Her face is cut off and the frame is mostly her shoulder. | Face-tracked keys show her whole face screaming, with cupped hands. |
| 1500–1840 | Three days: her face is pressed into the wall, her hands are claws, and her legs splay over the camera. | She lies curled on her side in the middle of the clothes, head on her arm, face toward the camera, hands relaxed (curl 0.22–0.25). She breathes and shifts. The camera alternates sides every second. |
| 1910–2090 | The rescue snaps back to the same squat. | She lifts her head at the knock (f1935), pushes up on one arm with the other hand flat on the clothes (f1990), then sits (f2045–2088). |

## Re-check
- **Half-second sheets:** `review/BEFORE_v004_0p5s.jpg` and `review/AFTER_v005_0p5s.jpg` (270×480, 8 samples, every 30 frames).
- **Hand close-ups:** `review/hands_closeups_v005.jpg` holds 14 hand contacts at 270×480.
- **Clip scan** (`pipeline/clip_scan.py`, step 6, 2 cm): see `review/clip_scan_v005.json`. The only range left is f2029, and it is off camera. At f2029 the camera is outside on the firefighters and the panel is still shut. On camera: 0.

## Known, not fixed
- The flap pass-throughs at about f1400 and f1570 still last about 4–8 frames on textured steel.
- In the three days she lies on her side, so her face reads rotated about 90° in a vertical frame.

## Round 2 (director review of fc2718f): eight fixes
| # | Time | Fix |
|---|---|---|
| 1 | 20–24 s | Jump: one side camera (x≈0.63, 14 mm) shows her whole body crouching, jumping, slapping the wall high and sliding down. The turns before and after are stepped turns (`turn_keys`) with her hands in front, so they don't sweep through her chest. Scream: one steady low front-corner camera (0.52, −0.48, 1.50) aimed at her face. Her body is upright, her head is tilted up to the chute, her mouth is open, and her hands are cupped at her mouth (placed from the posed head). |
| 2 | 29–31 s | No black frames. The night fill is raised and the face camera checks for a clear view (no camera inside her shirt and no ground clip). |
| 3 | 26.5 s | The curl start is framed on her face and shoulders (face_cam). |
| 4 | 36–37 s | Walking out, her left hand holds the blanket at her chest and her right arm hangs. The IK arm keys are cleared. |
| 5 | 2.0 s | The camera at f110 is raised and moved to the side, so the shover's head no longer covers her. |
| 6 | 5.0 s | The landing frame is lit (fill and exposure at f290). |
| 7 | close-ups | Hands are re-aimed by a ray-cast search for a clear view of the wrist from inside the bin. f1000 and f1216 show palms on the wall, and f1135 shows her palm on the flap edge. Script: `pipeline/hands_closeups.py`. |
| 8 | 15.5 s | The face_cam framing uses the face point (head bone −3 cm, +5 cm forward), not the top of her head. |
