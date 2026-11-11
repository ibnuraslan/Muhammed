# HeadsetBullet_v005: farm package

This is the full 25.0 s film (frames 1–1500) at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.
It is built to the brief's target beat times. There is no VO yet: retime with `pipeline/retime_to_vo.py` and `beats.json` when the mp3 arrives.

- `HeadsetBullet_v005_60fps.blend`: the self-contained scene. Every texture is packed.
- `beats.json`: the beat start frames and first words, for the VO retime.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block for the video description.
- `package_check_f343/1240/1350_lowres.png`: 25 %, 6-sample frames from the packed file opened in factory Blender. They show the package works; they are not a quality reference.

The source is `../HeadsetBullet_v001/scripts`. Build order:
1. `00_plain_shirt.py`
2. `01_build_teen.py`
3. `02_build_scene.py`
4. `03_animate.py`, which runs `03a_headset.py`, `03b_effects.py` and `03c_camera.py`
5. `pipeline/anim_look.py`, then `06_anim_look_fixes.py` (v004 look)
6. `07_hand_limits.py` (v005 hands)
7. `05_shrink.py` (1K textures, JPEG/8-bit, orphan purge)
8. `pipeline/package_for_farm.py`

The audit is `scripts/audit.py`. Review sheets and notes are in `../HeadsetBullet_v001/review/`.

## Story beats (target times)
| # | Frame | Line | On screen |
|---|---|---|---|
| 1 | 1 | A bullet was fired toward the house | Bullet chase over the street, lawn, fence and driveway. Birds lift off the fence, the sprinkler turns, leaves drift. |
| 2 | 133 | smashed through the window | The pane bursts into 183 shards; the camera flies through the hole and the curtains flutter. |
| 3 | 241 | headed straight for his head | Follow-cam behind the bullet toward the back of his head. |
| 4 | 355 | gaming at his desk, wearing a headset | Orbit: WASD typing, mouse flicks, the RGB headset, the monitor and LED glow. |
| 5 | 571 | instead of piercing his skull | Macro, slow approach to the ear cup by his temple. |
| 6 | 697 | the bullet hit the headset first | Impact: the crack spreads, chips and dust fly, the RGB ring dies, the head jolts. |
| 7 | 835 | thick padding and the metal frame inside | Cutaway: the dark shell, the yellow foam compressing, the steel ring; the bullet tilts. |
| 8 | 949 | deflected the bullet, sending it safely away | Sparks; chase of the bullet across the room into the wall: chips, dust, the hole. |
| 9 | 1165 | pulled off the broken headset | Hands close on the cups and rip it off; the chair rolls back; he cradles and turns it. |
| 10 | 1315 | realized it had just saved his life | Close-up stunned face, then he turns; over-shoulder push-in to the hole. |

## Changes from v002 (director's notes)
- **Face, the shock beats:**
  - The eyes now use a simple opaque procedural eye (brown iris, pupil, wet coat). MPFB's layered eye rendered dark or pale without caustics.
  - The lids open wide to show the whites, the brows rise, and the mouth drops open (fixed the jaw sign).
  - He blinks and his eyes dart toward the hole before his head turns. He swallows at f1390–1402. His breathing is faster after the impact.
- **Room:**
  - Warm sunbeam through the window, and purple/cyan/pink RGB washes on the walls.
  - Collectible figures on the desk shelf and on a new wall shelf, a messy duvet and a hoodie on the bed.
  - Energy cans with colour bands only, three more on the floor, and an extra abstract poster.
  - The floor is darker and the monitor glow is lower, so his skin no longer clips.
- **Wall hit:** a framed print hangs where the bullet lands. Its glass shatters into 40 falling shards, the bullet hole sits in the art, and the frame swings on its nail and settles.
- **Props reacting:** the can next to his keyboard tips over and rolls when he jerks at the impact. The chair swivels after the impact.
- **Headset:** a boom mic on the left cup (2.5 cm clear of the mouth; the audit shows 0 head or face overlap), plus leatherette bump and stitching on the band pad.
- **Camera:** a key at 1019 keeps the ricochet bullet in frame for the whole flight, and the cup macros at 12.4–13.6 s now vary.

- **Realism pass (client note, 21:00 UTC):** real models now replace primitive stand-ins.
  - Exterior: the box car is now a 3D-scanned covered car, the two neighbour block houses are real house models, and the box mailbox is a real mailbox model.
  - Room: the slab desk is the Poly Haven metal office desk, and the box PC is a gaming PC model. The box bed and grid duvet are now a real bed with a draped sheet.
  - Props: the cylinder cans are a real can mesh (repainted, no labels). The capsule figures on the shelves are scanned wooden and brass decor, and the cylinder ceiling lamp is a real lamp. The bowl and chips were removed, and the rug has a carpet texture.
  - Fixed: the house plinth sat 20 cm above the room floor and was covering it; the wood floor and rug now show.
  - Kept procedural, with reasons: our house shell (Poly Haven plaster and clay roof tiles; it has to line up with the room window the camera flies through), the headset (it must crack, dent and be cut away), the bullet, glass and debris, the posters and the wall shelves.

## v004: animated look (client look change, 22:45 UTC; see `blender/STYLE_ANIMATED.md`)
- Built from the final v003 animation; no animation or geometry changed.
- `pipeline/anim_look.py` changes:
  - AgX Punchy
  - sky-gradient background for camera rays, HDRI fill ×1.6
  - saturation ×1.25
  - bump/normal ×0.35
  - roughness at least 0.35
  - motion blur off
  - lights ×1.25
- `scripts/06_anim_look_fixes.py` adds:
  - the animated f-stop clamped to at least 5.6 (at least 4 only for the ear-cup macro)
  - light sky-blue room walls and a warm honey floor
  - brighter, even room fill with softer RGB washes
  - warm-yellow sparks
  - exposure +0.15
- The bullet strike shows only a spark, the cracking plastic cup and chips. There is no injury anywhere.
- Review sheet: `../HeadsetBullet_v001/review/v004_anim_look_1s.jpg` (1 still per second, 270×480, 8 samples).

## v005: hands pass (client, 23:00 UTC; see "Hands" in `blender/STYLE_ANIMATED.md`)
- Only the hands changed. The animation, look, set and camera are all the same as v004.
- `scripts/07_hand_limits.py` adds Limit Rotation constraints in local space on all 32 finger, thumb and wrist bones.
  - **Fingers:** curl 0–90° on local +X, so they never bend backward. Twist is ±10° and spread ±12°, intersected with the keyed range ±5°.
  - **Thumb:** a cone of its own keyed range ±5°.
  - **Wrists:** the natural range is taken from every phase that reads right, ±10°. The over-bent grab and rip frames (f1180–1280) are clamped to it. This rig's rest-relative wrist angles don't map one-to-one onto anatomical flex and side bend: a fixed ±25° side clamp broke the natural typing hand.
- **Grip fix:** the cup grip moved out 9 mm, so the palms no longer graze his ears at the start of the rip (f1223–1227).
- **Hand audit** (`scripts/audit_hands.py`), every 2 frames, all 1500 frames, BVH. The result is in `../HeadsetBullet_v001/review/v005_hand_audit.txt`:
  - hand × hand: **0**
  - hand × own body (torso, head, legs): **0**
  - hand × shirt: **0**
- **Contact audit** (`scripts/audit.py`):
  - hands into the keys: 2.8 mm max (fingertips pressing)
  - hands into the headset: 3.0 mm max (grip on the soft cushion)
  - head into the worn headset: 0 mm
- **Joint-range lines in the hand audit** ("joint over range", 26 samples) are a heuristic on raw rig angles, not an error count. They fall at f343–357 (the typing hand) and f1185–1261 (hands at the ears and the start of the rip). Both were checked in close-ups and look natural. Elbows peak at 155°: arms fully folded with the hands at the ears.
- **Sheets:**
  - 1 still per second: `../HeadsetBullet_v001/review/v005_hands_1s.jpg`
  - hand close-ups (typing, mouse, startle, reach, grab, rip, cradle, hold): `../HeadsetBullet_v001/review/v005_hand_closeups.jpg`

## Known open items
- **No VO:** timing is to the brief's target times until the retime.
- **Face:** the stunned face uses the jaw, head, neck and breathing only. The MPFB rig here has no brow or eyelid expression controls.
- **Chair roll-back:** during the roll-back (f1255–1285) his right heel lifts about 2 cm with the leg at full reach.
- **Cushion contact:** fingertips press up to 4.6 mm into the soft ear cushion while he cradles the headset (the audit counts this as grasp contact). Fingertips press up to 2.8 mm into the key tops.
- **Glass:** the shards settle on the floor and sill as flat pieces, without bouncing.
- **Dust puff:** it is made of 28 alpha spheres, not a volume, so it reads slightly soft-lumpy in close-up.
- **Bullet framing:** in a handful of chase frames (f91–94, 205–208, 560, 1018–1021) the bullet sits at the frame edge.
