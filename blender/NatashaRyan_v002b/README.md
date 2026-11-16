# NatashaRyan_v002b (B15): The Strange Disappearance Of Natasha Ryan

A vertical true-story short, 1080×1920, 60 fps, Cycles, frames **1–2136**. It is built to the client VO (`NatashaRyan_v002b_VO.mp3`, 35.08 s). The look is bright 3D animation with generic characters only.

| Shot | Frames | VO words |
|---|---|---|
| S01 | 1–86 | In 1998, |
| S02 | 87–152 | a 14-year-old girl |
| S03 | 153–218 | was dropped off at school |
| S04 | 219–299 | by her mother and never |
| S06 | 300–389 | came home. |
| S07 | 390–472 | Police searched everywhere, |
| S08 | 473–588 | but there was no sign of her. |
| S09 | 589–733 | Days became weeks, then months, |
| S10 | 734–907 | and eventually her family feared she was dead. |
| S11 | 908–965 | A year later, |
| S12 | 966–1082 | a local serial killer even confessed |
| S13 | 1083–1180 | to murdering her. |
| S15 | 1181–1264 | Four years passed, |
| S16 | 1265–1392 | and his murder trial finally began. |
| S17 | 1393–1523 | But right in the middle of court, |
| S18 | 1524–1664 | prosecutors announced something unbelievable. |
| S19 | 1665–1780 | After five years missing, |
| S20 | 1781–1910 | the girl had been found alive, |
| S21 | 1911–1975 | living only five |
| S22 | 1976–2052 | minutes away from her family the |
| S23 | 2053–2136 | entire time. |

- `beats.json`: shot start frames at `1 + round(word_s × 60)`.
- `review/preview.mp4`: every 5th frame at 270×480, with the VO, rendered from this exact package.
- The build scripts are in `../NatashaRyan_v001/scripts/` (`01`–`06`).
- **Timing.** Every set's action was animated at 1×. `05_retime.py` places it on the VO with **one constant time shift per set-run** (no stretching). Cameras of a run take the same shift and extrapolate linearly.
- **Logo.** One placement: the white DA KRAS FILMS logo on the delivery van in S03 (frames 153–218, about 45 % of frame width).

## v002b changes (director notes on v002)
1. **Natasha at 18 (S20, S21, S23)** wears a burgundy knit sweater and a denim skirt. These replace the one-colour dark outfit that read as a onesie.
2. **Arms on long holds now have relaxed bent elbows.**
   - The escort officers and the man (S11–S13): the officers turn their heads as they talk.
   - The prosecutor (S15–S19): a second open-hand gesture toward the room, with his other hand, in S18.
   - The father at the window (S10), plus the officer and Natasha in the bedroom.
3. **Shots that showed small figures are reframed.**
   - S08: the camera is ahead of the searcher, who walks toward it and crouches.
   - S15: a push-in from the bench side onto the parents in the front pew.
   - S20: a closer camera plus a stronger soft face fill.
4. **Final shot (S23):** she steps toward the camera and looks up into it, with a slow push-in.

Only the changed ranges were re-rendered from this exact package and spliced into `review/preview.mp4`: 473–588, 734–907, 908–1180, 1181–1780, 1781–1910, 1911–1975 and 2053–2136.
