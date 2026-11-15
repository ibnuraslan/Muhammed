# StanleyCup v007e: the director's v007d review (on top of 7f812c8)

Same 1530-frame timeline. Beat order and beat frames are unchanged (1, 139, 271, 391, 607, 973, 1285, 1417), so `beats.json` is unchanged.
- Preview of this exact package: `review/StanleyCup_v007e_preview.mp4` (every 5th frame, 270×480, Cycles 4 samples + OIDN, 12 fps, 25.5 s).
- Before/after: `review/director_items_before_after.jpg` (top: v007d, bottom: v007e).

| # | Item | v007e |
|---|---|---|
| 1 | f1061–1280: static wide hold, faces barely readable | Two medium shots, each with a slow push-in. f1011–1140: him, staring at the dented cup. f1141–1269: her face, close and readable, with her raised hands. A clean cut at f1270 goes to the drop of the bullet (beat 7). |
| 2 | f1351–1530: static wide ending | A medium two-shot from her side with a slow dolly-in, both faces in frame. He half-rises and lifts the dented cup; she has her hand at her chest, then in her lap. |
| 3 | f901–941: blurred foreground hands | Fixed in 7f812c8: from f880 a two-shot holds both faces until the impact shot. |
| 4 | Bullet passing the lens as an orange blob | This was in the exterior chase (about f86–111); f196–236 in the current build is the clean shot behind the couple. The chase camera now trails 40–45 cm behind the bullet at f/11, focused on it, so the bullet reads small and sharp. |

## Checks on this build
- Blur metric (`review/sharpness_check.py`, every preview frame): the only run of 3 frames under the threshold is the sharp bullet-bounce close-up (f1306–1316), exactly 0.25 s. The chase frames now score as sharp.
- rules_check (every 2 frames): 0 arm-over, 0 floating hands, 0 camera brush. hand_audit 0. audit: feet, seat, bullet and camera all 0; fingers 9 mm at most.
- qa_check: EMPTY 39, FILL 0, INSIDE 0, BACKHEAD 0, HOVER/CLAW/FACEPRESS 0. clip_scan 0.
- limb_check: ARMBODY 434. All are within 4 cm of the shoulder joint (`review/limb_points_v007e.json`).
