# AIAsleep: acting review of v003 (half-second sheet, 270×480)

Sheets: `v004_before_half_s_A.jpg` (0–21.5 s) and `v004_before_half_s_B.jpg` (22–43 s). Frame = 1 + t × 60.
The question for each still: would a real driver move like this, here, for this reason?

| # | Time (frame) | Problem | Fix in v004 |
|---|---|---|---|
| 1 | 9.0 s (541) | A blink lands on "he wasn't sleeping" and reads as asleep. `blink()` also reset brows and jaw to neutral, so every blink snapped the brows. | `blink()` keys the lids only. No blink on the "not sleeping" line; blinks moved between lines. |
| 2 | 10.6–12.0 s (636–720) | Head shake: six swings 10 frames apart, a robotic buzz. | Two natural shakes, about 0.33 s per swing, with ease. |
| 3 | 18.8–19.0 s (1130–1150) | Frustrated exhale is a wide-open "gasp" mouth (jaw 8°). | Lips barely part (jaw 2°); the exhale reads through shoulders dropping and the head going back. |
| 4 | 20.0–20.5 s (1201–1231) | Right hand flips off the wheel high up near the mirror as a claw, then returns. Not a real gesture. | A small open-palm "what?" lift a few cm above the rim, fingers relaxed, then back to grip. |
| 5 | 42.0 s (2521) | The sigh is a gaping mouth (jaw 6°). | jaw 2°, plus a shoulder drop. |
| 6 | All film | No breathing; long stretches of a frozen torso and hands. | Clavicle breathing every 2 s, small steering corrections every 1.5–2 s, a mirror glance in beat 1. |
| 7 | 4.0 s (241) | Camera low under the chin during the flinch; the face is a blur looking up. | 234/270 framings raised to face height. |
| 8 | 10.5 s (631) | Frame filled by his ear and the back of his head (the path goes through the head to the back seat). | The orbit goes round on the passenger side (new key 635). |
| 9 | 12.0 s (721) | Back of the head fills the right half; face unreadable. | 720 framing moved forward to a 3/4 front of his face. |
| 10 | 18.5–19.5 s (1111–1171) | The camera crosses right in front of his face (from the screen side to the window side): headliner, half a face, blur. | 1140 framing kept on the passenger side, close on his face. |
| 11 | 21.0–21.5 s (1261–1291) | Frame filled by his shoulder and sleeve. | 1302 framing moved clear of the shoulder. |
| 12 | 22.0 s (1321) | Sunroof glass seen from above as a bright slab over a hand blob. | Roof and glass stay hidden until 1330, while the camera clears the roof. |
| 13 | 28.5 s (1711) | Flat grey blank: shallow DOF on the IR eye close-up. | f-stop rises earlier (f/16 by 1690). |
| 14 | 41.5 s (2491) | Blurry mouth fills the frame (the pull-back slides along his face). | Pull straight back off the eye first (new key 2470). |
| 15 | 42.5 s (2551) | Side and back of his head fill the frame (the path cuts across the head to the back seat). | Go round on the passenger side (new key 2535). |
| 16 | 16.0 s (961) | Mid-whip blur of the console. | Kept as a whip accent (about 4 frames); the screen reads by 16.3 s. |
| 17 | Hands | Re-grip at 11.5 s is a half-open hand hovering for about 0.4 s. | Shorter hover (8 frames) and a lower lift, so the palm stays on the rim. |

Story-beat frames (`beats.json`) are unchanged.

## Found on the after pass and fixed
| # | Time (frame) | Problem | Fix |
|---|---|---|---|
| 18 | 28.5 s (1711) | The IR eye close-up was still a grey blank: Bezier overshoot carried the camera to 1.7 cm off the cornea. | Removed the back-and-forth key at 1770. All camera and aim keys now use clamped auto handles (no overshoot through faces), and 1680/1728 are re-keyed to the real eye position. |
| 19 | 28.5–29.6 s | Two mirror near-passes at 629 and 1133 (2 cm). | Keys 635/1140 lowered under the mirror. |
| 20 | 20.0 s | Gesture hand flat-splayed. | Relaxed half-curl (k 0.5). |

## Result
- `review/v004_after_half_s_A.jpg`, `review/v004_after_half_s_B.jpg`: the same half-second sheet on v004.
- `review/v004_hand_closeups.jpg`: 24 close-ups of every hand action (grips, re-grip, gesture, steering corrections, sigh).
- `review/v004_clip_scan.json`: director `clip_scan.py`, 0 bad ranges.
- `review/v004_hand_audit.txt`: hand vs hand, torso/shirt and head all 0. The rim check flags 1–2 finger-bone samples on grip frames, which is the rim inside the curled fist.
- `review/v004_camera_clearance.txt`: the window-frame entry at 121–123, a sun-visor pass at 723 (2.9 cm) and the intended skin dive at 1791 only.

## Director review of 3777fec, fixed
| # | Time (frame) | Problem | Fix |
|---|---|---|---|
| 21 | 4.0 / 10.0 / 14.0 s (hand close-ups) | Near hand lifted off the wheel with the fingers spread. | Re-grip and gesture are now slides along the rim: fingers stay curled, palm in contact (hands(700,-98,98); R hand 90→76→80→90). |
| 22 | 15.0–15.5 s (901–931) | Up-the-nose angle. | Push-in raised to just above eye level. The sun visors are removed from render (they read as flipped up) because they blocked the eye-level camera. |
| 23 | 9.5 s, 41.5 s | Half-open mouth with lower teeth bared (snarl). | All jaw keys 0.5°: lips relaxed, teeth hidden. |
| 24 | 42.5 s (2551) | Back of his head on the last character beat. | 2535/2562 framings moved in front of him (3/4 face). |
| 25 | 16.0 / 17.0 s (961, 1021) | Blurred fabric and wheel. | The camera arrives on the HUD by 958 and holds/drifts on it to 1030. |
