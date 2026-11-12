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

## Director review of v006 (40b7da8): round 2 fixes
| # | Director note | Fix |
|---|---|---|
| R1 | 4.0–4.5 s: the shielding hand's palm and thumb press into his nose and eye. | The shield is held in front of his face, with the nearest finger about 16 cm from the face (measured by BVH, frames 262–880; about 18–21 cm during the impact jolt). The fingers are closer together (spread 26° → 8°, curl about 6°) and the impact jolt toward the face is halved. The back of the hand stays toward the bullet, because the wedding ring has to face the shot for the story. |
| R2 | Close-ups 5.0 and 6.0: claw hands. | The lowering right hand gets a relaxed finger key (curl 12°, thumb 12°). The wince hand now rests flat on his chest and tie (palm on the chest, fingers loosely curved, curl 18°) instead of pinching. |
| R3 | 17.0 s: the far hand hovers beside his ear. | The hand on the neck is moved about 1 cm in, so the palm visibly touches the side of the neck over the graze (close-ups neck_cup_side and neck_cup_front). |
| R4 | 2.5–3.0 s: two fully blurred frames. | During the bullet-ride peel-off, the focus distance now follows the aim from the bullet to his face, so either the bullet or his face is sharp in every cell. |
| R5 | Close-ups 11, 14, 15 and 16 miss the hands. | `scripts/clip_closeups.py` is rewritten. Each shot targets the hand centre (wrist plus middle-finger bones) and tries 27 camera offsets, keeping the first with a clear line of sight. There are now 16 close-ups, all showing the hand, feet or dressing. |

Also: the contact audit's camera-inside test now needs two independent ray directions to agree. A grazing ray on a bevelled ceiling beam had given one false positive at f1091; the camera there was at 1.47 m.

Checks after round 2:
- `clip_scan`: **0 bad ranges**
- hand audit: **0**
- contact audit: **0**
- beats.json unchanged

## Round 3: self-check fixes before resubmitting
- **Shield (4.0–4.5 s):** both hands are lower (wrist z 1.36) and wider apart, so his eyes and face show above them from the camera. They're still held about 16 cm out from the face, so nothing is pressed in.
- **Terror eyes:** the head tilts back less during the slow motion (−5° to −10°, was −12° to −20°) and the wide-eye amount is smaller, so the irises stay visible instead of rolling up to white.
- **Wince hand (f905–936):** the curl is lowered to 14° on the way to the chest, so it no longer reads as a pinch.
- **Hidden sparks:** parked 10 m below the floor while hidden, so they don't sit beside his hand.

## qa_check.py, intended flags (qa_v006.json)
| Flag | Frames | Why it stays |
|---|---|---|
| BACKHEAD Robber | 1 (beat 1) | The brief's sensitive rule: never show the robber's face. Beat 1 is over his shoulder, and the owner's face is in frame and readable. |
| FILL "surface < 12 cm" | 73 | The camera rides the 9 mm bullet in slow motion, about 8 cm behind it. The bullet is the subject; the owner reads behind it. |
| HOVER Owner.L near Spark37 | 781, 787 | A spark from the split flies past his hand. It's moving FX, not a prop to hold. |
| HOVER Owner.L near FragmentA | 895–1243 | The bullet fragment lodged in the side of his middle finger (the story). It sits on the finger skin by the nick, about 1.4–2.5 cm from the fingertip and knuckle points the script measures. Nothing is held. |

No CLAW, FACEPRESS, INSIDE or EMPTY flags.

## Round 4 (hand_poses.py, updated qa_check c6240b2)
- Every finger key now goes through the shared `pipeline/hand_poses.py`:
  - shield: raised hands
  - flat_palm: palm laid on the side of the neck
  - wrap_grip: the robber's gun hand
  - relaxed: everything else

  Its `add_hand_limits` is on all three rigs (fingers, thumbs, wrists, elbow IK). A ±9° splay is kept on the middle finger and pinky so they stay off the wedding band (inside the ±10° spread limit).
- The neck palm was nudged out with a mid key at f1012. `clip_scan` reports 0 bad ranges.
- `qa_check` on the package: only BACKHEAD Robber at f1 and FILL during the bullet ride (about f67–73), both intended (see the table above). The HOVER flags are gone with the updated script.
- Hand audit: 1 frame (f1271). A single triangle pair touches as the walk begins: a fingertip of the far-side hand brushing the jacket hem. It isn't visible and is under the 2 cm clip_scan threshold.
