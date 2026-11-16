# WeepingStatue v002 — B03 "The Weeping Jesus Statue"

Vertical true-story short, 1080×1920, 60 fps, Cycles, timed to the client VO (`WeepingStatue_v002_VO.mp3`, 28.7 s).
Hard cuts, 18 shots, built straight to the VO word frames (`beats.json`); nothing time-stretched.

Files
- `WeepingStatue_v002_60fps.blend` — the render package (textures + VO packed, factory-startup clean, 1 camera `CAM`).
- `WeepingStatue_v002_VO.mp3` — client VO.
- `beats.json` — shot start frames at `1 + round(word_s × 60)`; `shots_vo.json` — the shot blocks used by `scripts/04_anim.py`.
- `review/preview.mp4` — moving preview (every 5th frame, 270×480, Cycles 4 spp + OIDN, frame numbers burned in, with VO).
- `scripts/` — the build (01 cast, 02 sets, 03 statue, 04 shots to `shots_vo.json`, 05 package).

Shots (VO words → frames)
| Shot | Frames | VO | Picture |
|---|---|---|---|
| S01 | 1–143 | "A statue of Jesus suddenly started leaking" | Macro of the marble feet, a drop swells and falls |
| S03 | 144–264 | "what people believed was holy water" | The statue on the concrete cross |
| S02 | 265–349 | "from its feet" | Low angle: a drop falls onto the wet plinth |
| S04 | 350–456 | "Nobody knew where it was coming from" | Crowd at the wall, two point at the feet |
| S05 | 457–562 | "so crowds gathered around" | Crowd 3/4, faces up, a woman lifts her hands to her chest |
| S07 | 563–626 | "collecting the water" | A cup on the plinth fills from the drips |
| S08 | 627–698 | "and touching the statue" | A man lays his palm on the wet stone under the feet |
| S06 | 699–808 | "believing it was a miracle" | The woman in close-up looking up |
| S09 | 809–910 | "But one man investigated" | Bathroom wide: the investigator and the caretaker |
| S10 | 911–983 | "and discovered a bathroom pipe" | He points at the leaking pipe joint |
| S11 | 984–1049 | "had caused a drain" | The floor drain wells up, water spreads |
| S12 | 1050–1122 | "to overflow" | Drops under the pipe coupling |
| S13 | 1123–1212 | "Moisture was traveling through the wall" | Tilt down the damp streak, water runs down |
| S14F | 1213–1350 | "and leaking from the statue" | Back at the statue: the feet drip |
| S15 | 1351–1434 | "Religious groups became furious" | The investigator in front of the frowning crowd |
| S17 | 1435–1507 | "with his explanation" | His close-up, eyes down |
| S16 | 1508–1612 | "and accused him of blasphemy" | Two men point at him |
| S18 | 1613–1724 | "forcing him to flee the country" | He walks away pulling his case (logo) |

Logo: DA KRAS FILMS (white) on both broad faces of the trolley case, S15–S18 (director-approved).
