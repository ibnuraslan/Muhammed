# SpeakWithoutSight v005: moving-preview pass (director, Nov 14 19:04)

Watched as motion with `pipeline/preview.py` (every 5th frame, 270x480, frame numbers burned in) and `pipeline/watch_pages.sh`. Every page was watched.
`review/preview.mp4` is that preview at real speed (12 fps). `review/preview_pages/` holds the contact pages.

The preview is of this exact build. Frames 1–1056 were rendered from the build before the last change, which only touched keys from 1061 on (the lips fix) and is identical below that. Frames 1061–1980 are from the final build.

Beat frames are unchanged. No VO was added.

## Faults found while watching, and the fixes
| Frames | Fault | Fix |
|---|---|---|
| 451–466, 1621–1690 | Teacher's arm held up over the girl's head | Cause: uncapped "push up" de-intersect keys. Pushes are now capped at 4 cm. |
| 471–526, 1056–1091 | Teacher's sleeve fills the lens during the wrist grips | Simplified: no grips. Her right hand hangs at her side, then rests on the girl's knee; the girl raises her own hand. |
| 531–1063 | Hand on the throat hovers in front of the neck (fingertip-only pad, read in profile) | Flat palm on the front of the throat, fingers up under the jaw (`hand_poses` "shield") |
| 751–1050 | X-ray glass forearm and floating skeleton hand (see-through limbs) | The girl's arm and hand stay solid. The teacher's larynx cross-section and the pulse dots stay. |
| 1100–1180 | Fingertips 3–4 cm short of the lips (hover) | Pad aimed deeper so it lands on the lips. Lips de-intersect pass is skin-only. The 1125 camera uses the side framing. |
| 1101–1300 | Fingertips slide up into the nostrils | No nose slide. Fingertips stay on the lips. |
| 1391–1406 | Giant blurred hair blob across the lens | The 1385 camera stays on the teacher's side |
| 1483–1975 | Girl's left upper arm pressed into her chest on her own lips/throat touches (limb_check 5–8 points) | Elbow out to her side |
| 1866 | "OK" claw on the way back to the lap | `hand_poses` "relaxed" |
| 1881–1906 | Gasp hands pressed on the nose and mouth | Hands held in front of the chin |
| everywhere | Starfish hands (qa FAN 757) | `Person.fingers` aligns each finger with the middle finger, as `hand_poses` does. Mother's sewing hand curl evened out. |
| everywhere | Black-hole eye risk | `eye_fix.py` (LegoInNose a44130b) applied to all MPFB characters |
| macros | Shallow focus | f/8 base, f/11 on the 1310–1395 macro |

## Checks on the packaged build
- `clip_scan` (official, skin only): **BAD_RANGES []**
- `qa_check`: BACKHEAD, FACEPRESS, HOVER, CLAW, FAN, EMPTY, ROLL and CAMJUMP all **0**. Remaining flags, all intended:
  - PROPMOVE: PulseDot_* are the glowing vibration dots (FX, not props). Model_Larynx at f1063 is the cross-section model fading out.
  - ATTACH 1 frame (1801): the father's cap in the far background.
  - INSIDE 25: the ExplainerDome backdrop sphere for the x-ray beat.
  - FILL (hair): face close-ups.
- `limb_check`: ARMBODY remaining hits are only the known 2–3-point shoulder false positives. PROPHEAD is the larynx model and pulse dots inside the teacher's throat (the intended cross-section).

## Known, minor
- 1836–1856: the girl's right arm reaches straight out of frame toward the teacher's lips (the teacher is off-frame in that close-up).
- 1966–1980: the dog's back just enters the bottom edge for the last 0.25 s.
