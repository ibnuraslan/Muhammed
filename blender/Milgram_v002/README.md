# Milgram_v002: The Milgram Experiment, built to the voiceover

ConnectB25. Built straight to the client VO `Milgram_v002_VO.mp3` (33.0 s): every shot starts on its word
(frame = 1 + round(seconds × 60) from `Milgram_v002_VO.words.json`). Each shot's action was animated at 1× as its own clip
and cut at the next word; nothing is time-stretched. Render settings: `SETTINGS.md`. Credits: `CREDITS.md`.

Review: `review/preview.mp4` (every 5th frame, 270×480, Cycles 4 samples, with the VO) was rendered from this exact
package and watched start to finish.

## Shots (frames, first words)
| Shot | Frames | VO |
|---|---|---|
| 01 | 1–86 | Every time the stranger answered |
| 02 | 87–157 | incorrectly, |
| 03 | 158–217 | you pressed a button that |
| 04 | 218–323 | supposedly shocked him. |
| 06 | 324–386 | And each wrong answer |
| 07 | 387–516 | meant the voltage got higher. |
| 08 | 517–638 | Eventually, the stranger started screaming |
| 09 | 639–751 | and begging you to stop. |
| 05 | 752–851 | But a man in a lab coat calmly |
| 10 | 852–948 | told you to continue. |
| 12 | 949–1007 | So you did. |
| 13a | 1008–1078 | Even when the stranger appeared |
| 13b | 1079–1140 | to collapse, |
| 23 | 1141–1243 | you kept pressing the button. |
| 17 | 1244–1350 | But the shocks weren't real. |
| 18 | 1351–1458 | The stranger was an actor. |
| 19 | 1459–1522 | You were the actual |
| 20 | 1523–1602 | test subject. |
| 26 | 1603–1690 | The experiment showed how far |
| 28 | 1691–1774 | ordinary people could go |
| 24 | 1775–1868 | when an authority figure simply |
| 29 | 1869–1982 | told them to keep going. |

## Notes
- Hard cuts are baked into one camera (`CAM_Main`); there are no camera markers.
- No on-screen text. The only logo is the DA KRAS FILMS poster on the lab wall (shot 26, and in the background of 06).
- The shocks are short stylised arcs; nobody is injured on screen.
- Build scripts: `../Milgram_v001/scripts/` (01_build.py, 02_shots.py with `shots_vo.json`, 03_finish.py).
