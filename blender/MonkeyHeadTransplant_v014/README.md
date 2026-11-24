# MonkeyHeadTransplant_v014

This is a rebuild from scratch, done the same way as the EarInArm v015 rebuild. It keeps the v013 VO and timing: frames **1–1656** at 60 fps, 1080×1920, with one continuous camera and no cuts.

Batch 1 rejected the earlier version. This rebuild fixes those faults:
- The monkeys sit upright on padded seats. Each is snapped by ray cast onto the seat surface.
- There is one surgeon. He is a fresh MPFB model, used for the whole film, wearing loose scrubs, a cloth cap and a mask, all generated from his body.
- His feet stay planted the whole time, so he never walks through furniture.
- The stitches are short thread tubes projected flat on the skin, 0.8 mm off it.

## Package
| File | Contents |
|---|---|
| `MonkeyHeadTransplant_v014_60fps.blend` | The packed farm file (see `SETTINGS.md`) |
| `MonkeyHeadTransplant_v014_VO.mp3` | The voiceover |
| `beats.json` | Synced beat frames (same as v013) |
| `CREDITS.md` | Credits |
| `review/preview.mp4` | The watched preview of this exact package: every 5th frame, 270×480, with the VO |
| `review/CHECK1.md`, `review/CHECK2.md` | Review history |

## Build
Scripts are in `scripts/`. Run them in this order, each one in Blender with `-b`:

1. `01_base.py`. Input: the v013 package (models only). All of its animation is stripped.
2. `02_surgeon.py`
3. `03_layout.py`
4. `04_animate.py`. It reads `camera_keys.json` and `layout.json` (written by step 3).
5. `pipeline/package_for_farm.py`

`contact_check.py` and `forearm_check.py` are the numeric audits.

## Staging
| Item | How it's staged |
|---|---|
| Head carry | Both palms sit on the sides of the skull. Hand IK follows the head every 2 frames. Both forearms stay behind the head on every frame (checked by script). |
| Needle holder | It rests on two small steel bars on the towel. It is Child Of the `wrist.L` bone from frame 430 to 700, held in a closed fist round the shank by the rings, with the thumb along the shaft. The tool tip is solved onto the seam, within 1 mm, with one fixed hand orientation, so the wrist never flips. |
| X-ray | A camera-parented gradient void. Every non-monkey material fades out with it, and the brain, cord, vertebrae and glowing gap fade in. |

## Audit (`contact_check`, every frame)
- **Hands:** no hand, finger or forearm is more than 9 mm inside any body or prop. The remaining ≤9 mm flags are fingers in contact on the carried head and on the shoulder.
- **Needle tip:** it flags "inside MK_Head" at 451–522. This is a false positive from the head's open neck mesh. A direct measurement puts the tip 2–28 mm off the skin, and touching it at the stitch frames.

## Client and director decisions
- After check 1, the client approved everything except the needle-holder grip and the forearm during the head carry. This version fixes only those two.
- It keeps the check-2 fixes for the oscilloscope (moved, no text), the x-ray shards (transparent bounces) and the lamp (raised).
- Everything else is as in check 1.
