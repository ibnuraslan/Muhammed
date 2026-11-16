# WeepingStatue v002b — B03 "The Weeping Jesus Statue"

Vertical true-story short, 1080×1920, 60 fps, Cycles, timed to the client VO (`WeepingStatue_v002b_VO.mp3`, 28.7 s).
Hard cuts, 18 shots, built straight to the VO word frames (`beats.json`); nothing time-stretched.

Files
- `WeepingStatue_v002b_60fps.blend` — the render package (textures + VO packed, factory-startup clean, 1 camera `CAM`).
- `WeepingStatue_v002b_VO.mp3` — client VO.
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
| S08 | 627–698 | "and touching the statue" | A man reaches up and touches the wet stone beside the statue's foot with his fingertip |
| S06 | 699–808 | "believing it was a miracle" | The woman in close-up looking up |
| S09 | 809–910 | "But one man investigated" | Bathroom wide: the investigator and the caretaker |
| S10 | 911–983 | "and discovered a bathroom pipe" | He points at the leaking pipe joint |
| S11 | 984–1049 | "had caused a drain" | The floor drain wells up, water spreads |
| S12 | 1050–1122 | "to overflow" | Drops under the pipe coupling |
| S13 | 1123–1212 | "Moisture was traveling through the wall" | Tilt down the damp streak, water runs down |
| S14F | 1213–1350 | "and leaking from the statue" | Back at the statue: the feet drip |
| S15 | 1351–1434 | "Religious groups became furious" | He raises open palms, looks back over his shoulder and leans away; the crowd leans in, two men point/gesture |
| S17 | 1435–1507 | "with his explanation" | His close-up, eyes down |
| S16 | 1508–1612 | "and accused him of blasphemy" | Two men point at him |
| S18 | 1613–1724 | "forcing him to flee the country" | He walks away pulling his case (logo) |

Logo: DA KRAS FILMS (white) on both broad faces of the trolley case, S15–S18 (director-approved).

Checks on this package (work/qa, not committed): body_prop_cross 0 visible crossings (13 props × 11 rigs, every 3rd frame; S08 every frame);
clip_scan one sampled frame 631 (S08 start, the reaching man passes behind the statue's leg, no contact); limb_check remaining hits are the
2–3 pt shoulder-root false positives (CrowdM4's bulky jacket) and the statue's arms on the crossbar (intended). qa_check EMPTY on the
object shots (feet, drain, pipe: the VO names them), CAMJUMP at the hard cuts, PROPMOVE on the water drops — all intended.

## v002b changes (director notes on v002)
- S15: defensive action (open palms at chest, head turns back toward the crowd, leans away); crowd leans in, two visible men point/gesture.
- S17 eyes: the "liner" was the eyelash cards rendering solid black — the PopeShot-derived characters' lash/brow/hair textures had lost
  their alpha (JPEG-packed). They now use the alpha-intact copies (Tsunami2004 source); softer catchlight (2 W) and face fill (6 W).
  This also cleans the hairline/brows of every crowd member who used those textures (whole preview re-rendered and re-watched).
