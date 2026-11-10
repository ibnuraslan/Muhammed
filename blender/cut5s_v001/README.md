# Cut5s_v001: 5 s short-form cut (1080×1920, 60 fps, frames 1–300)

The motion-test action (source frames 196–495: reach → grab → lift → rise → drink), restaged with the pacing from the reference analysis:

| Frames | Time | Camera (marker) | What happens |
|---|---|---|---|
| 1–45 | 0.00–0.75 s | `CAM_A_Reach`, 32 mm, slow push-in | Hand arrives at the bottle; whip-pan out |
| 46–120 | 0.75–2.00 s | `CAM_B_Grab`, 55 mm macro, f/2.8, slow orbit | Fingers close; outline glows on the bottle; lift; whip-pan out |
| 121–200 | 2.00–3.33 s | `CAM_C_Rise`, 26 mm low angle, crane up | He rises with the bottle; whip-pan out |
| 201–300 | 3.33–5.00 s | `CAM_D_Drink`, 50 mm, push-in | Bottle to lips, drink, bottle comes away |

- **Camera cuts** are timeline markers bound to cameras, so the farm renders the cut as edited. Render frames 1–300 with the scene camera; don't render each camera separately.
- **Whip-pans** are 6-frame camera swings on each side of a cut. They need motion blur on (it is: shutter 0.5).
- **Highlight:** `Bottle_Highlight` is an inverted-hull outline parented to the bottle. Emission is keyed, and it is hidden outside frames 66–113.
- **Grip:** the thumb uses IK (`Thumb_Wrap` on `finger1-3.R`) toward the empty `Thumb_Target`, which is parented to the bottle. The target position came from a sweep that minimised hand-in-glass penetration.
- Render settings are the same as `../motion_test_v001/SETTINGS.md` except the range (1–300) and the output path `//render/Cut5s_v001_####.png`.
- Rebuild: `scripts/06_cut_5s.py` run on the animated file from `03_animate.py`.
- No narration or captions. This is a motion and pacing check.
