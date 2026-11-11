# HeadsetBullet_v002: farm package

This is the full 25.0 s film (frames 1–1500) at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.
It is built to the brief's target beat times. There is no VO yet: retime with `pipeline/retime_to_vo.py` and `beats.json` when the mp3 arrives.

- `HeadsetBullet_v002_60fps.blend`: the self-contained scene. Every texture is packed.
- `beats.json`: the beat start frames and first words, for the VO retime.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block for the video description.
- `package_check_f40/700/1300_lowres.png`: 25 %, 6-sample frames from the packed file opened in factory Blender. They show the package works; they are not a quality reference.

The source is `../HeadsetBullet_v001/scripts`. Build order:
1. `00_plain_shirt.py`
2. `01_build_teen.py`
3. `02_build_scene.py`
4. `03_animate.py`, which runs `03a_headset.py`, `03b_effects.py` and `03c_camera.py`
5. `pipeline/package_for_farm.py`

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

## Known open items
- **No VO:** timing is to the brief's target times until the retime.
- **Face:** the stunned face uses the jaw, head, neck and breathing only. The MPFB rig here has no brow or eyelid expression controls.
- **Chair roll-back:** during the roll-back (f1255–1285) his right heel lifts about 2 cm with the leg at full reach.
- **Cushion contact:** fingertips press up to 4.6 mm into the soft ear cushion while he cradles the headset (the audit counts this as grasp contact). Fingertips press up to 2.8 mm into the key tops.
- **Glass:** the shards settle on the floor and sill as flat pieces, without bouncing.
- **Dust puff:** it is made of 28 alpha spheres, not a volume, so it reads slightly soft-lumpy in close-up.
- **Bullet framing:** in a handful of chase frames (f91–94, 205–208, 560, 1018–1021) the bullet sits at the frame edge.
