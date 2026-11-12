# RingBullet: acting review of v005 (half-second sheet `v005_before_0p5s.jpg`)

Bar: `blender/briefs/ACTING_FIX_04-10.md`. Story-beat frames (beats.json) stay unchanged. `clip_scan` on v005: 0 bad ranges.

| # | Time (frames) | Problem | Fix in v006 |
|---|---|---|---|
| 1 | 3.0 s (f175–192) | The camera peels off the bullet and looks at a blurred wall, with nothing readable. | During the last third of the ride, the camera aim swings from the bullet to his face, so the man stays in frame through the peel-off. |
| 2 | 6.5 s (f383–400) | Start of the rack focus: a blurred hand fills the frame and the bullet is out of frame. | The macro lock on the bullet starts earlier (f384) and stays centred on the bullet. |
| 3 | 15.0–15.5 s (f896–935) | Wince after the fragment hits his finger: the hurt hand is pressed into his nose and eye, which nobody does with an injured finger. The top of his head fills the frame at 15.0 s. | The hit hand jerks back and down to chest height with the fingers curling. The other hand comes up open beside it. A cradling grip was tried, but it merged the hands, so it was dropped. The camera is lowered so his face and hands read. |
| 4 | 16.0 s (f960) | The right hand is a claw in mid-air at his chest, and the left hand is at his mouth. | Covered by fix 3: both hands are at the chest, apart, until the neck graze. |
| 5 | 16.5–17.5 s (f990–1070) | The neck grab lands behind his ear, not over the graze mark. | The palm is placed over the mark on the side of the neck, from outside: the hand cups the neck under the jaw, with the thumb forward and the fingers wrapping back. |
| 6 | 18.0 s (f1075–1090) | Lowering from the neck, the right hand floats up beside his ear (bad arc key). | The hand comes off the neck straight down and forward to a relaxed position at his side, with no up-arc. |
| 7 | 18.5–19.5 s (f1105–1170) | The orbit on the dented ring is so close that a blurred hand fills the frame, and his face is cut off. | The orbit radius is larger: the ring and hand are sharp, with his face in the frame at 19.5 s. |
| 8 | 20.8–21.5 s (f1250–1290) | Walk-out: both arms swing held well out from the body (a "penguin" look, a side effect of the hand-audit fix). | A natural swing close to the body, with the hands just outside the jacket. The hand audit is re-run. |
| 9 | 0–1 s (f1–60) | The owner stands rigid with his arms half-out before the shot. | Small startle: his weight shifts back, shoulders rise, and the hands come up defensively at the shot (f30–45). |

These checked fine:
- feet planted during the standing beats, and the walk feet
- the robber's grip (dark, side-on)
- the bandage and plaster on the skin
- the officer beckoning
- the ring macros (accepted earlier as macro)

## Result (v006)
- Before and after: `v005_before_0p5s.jpg`, `v006_after_0p5s.jpg`. Hand close-ups: `v006_hand_closeups.jpg`.
- `pipeline/clip_scan.py` on v006: **0 bad ranges** (`clip_scan_v006.json`; v005 was also 0).
- Hand audit: **0** (`hand_audit_v006.txt`). Contact audit: **0** (`audit_v006.txt`).
- `beats.json` is unchanged.
