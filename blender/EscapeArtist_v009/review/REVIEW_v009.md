# EscapeArtist v009: the director's v008 review, and how v009 answers it

Build: `06_fix_v007.py` → `07_v008.py`. Section V9 holds this round's changes, along with camera-list edits. Then `04_package.py`.
- Beat start frames are unchanged (`beats.json` is identical), no VO is added, and DOF is at f/11.
- Frames below are film frames at 60 fps.

## Must fix
| # | v008 fault | v009 |
|---|---|---|
| 1 | Filing with his hands at his crotch (320–415) | The close-up framing starts at 300: the file and the scrap sit at chest level in frame, with the file in his fist. |
| 2 | Adult behind the boy cut off at the head; the boy's forearms straight on the counter | The workbench shots (678–941) frame the boy only, from his other side, close on his face and hands. His elbows are bent and his hands pinch the coins. The father has his own full-figure shot at 790. |
| 3 | Gavel arm straight out sideways; red/blue strobe in the court | The red/blue lights are off from 1422 (steady courtroom light). The judge strikes with a bent elbow, his other hand flat on the desk, and the gavel is in a hammer grip with the head striking down. |
| 4 | Face against the fence post; a brown sheet sliding in at the top | The climb camera is outside the fence, 2 m from him, with the post out of the line of sight. The over-the-top shot starts at 1712, so the blanket isn't seen sliding in. |
| 5 | Head a white blob or missing going over the sheet | A low camera on his face side; his head and face stay visible on the top. |
| 6 | Brown block floating above the fence after the crossing | The blanket is hidden once he is over (from 1761). |
| 7 | 3.3 s of A-pose running in place | Two angles: a high wide at 2700 down the corridor (he covers ground toward camera), then a three-quarter at 2790 beside him. His arms are bent and pumping, with the bent tube in his right fist. |
| 8 | Pale mask patch with a hard seam on the aged face | The cause was the hard edge of the slot light. It now has spot blend 1.0 and a 0.35 m soft size, and the face reads as one even skin tone (3360–3445). |
| 9 | Old man as a bust on a ledge; a bar down his face; hands drifting | Ending, 3680–3750: he stands behind the cell-front bars, framed to the waist. The camera sits on the gap between two bars so both eyes are clear, with a slow push-in. Both fists are on the bars for the whole shot (wrists checked on the bar axes). At 3498 the window shot is from inside the cell. |

## Also fixed
| # | v008 | v009 |
|---|---|---|
| 10 | The boy frozen with the toolbox for 4.5 s | Head and spine reactions: he looks down at the box, flinches when she shouts (about 1222–1250) and looks up at her. Her shot starts when she turns to camera (1115). |
| 11 | 4 s of near-frozen sawing with a thumbs-up claw | A bigger stroke (±5.5 cm), with his body rocking with it. His right fist wraps the handle, and his left hand is wrapped on the bar. Cut at 2310 to a wider shot from inside the cell. body_prop_cross on the bars: 0 visible crossings. |
| 12 | 3 s of frozen seated pose | Split into two angles at 2040, with his head turning. |
| 13 | The door rail through his hips walking out | The camera is in the corridor on the far side from the open door, so the door is behind him. |
| small | A bar splitting his face at 200 | The close-up camera sits on the gap between two bars. |

## Preview of the delivered file
- `review/preview.mp4` (real speed) and `review/pages/` show the delivered `EscapeArtist_v009_60fps.blend`.
- The full `preview.py` pass ran every 5th frame. Ranges changed after it were re-rendered from the final package at the same settings and spliced in: 650–675, 1045–1215, 1380–1545, 1585–1715 and 3675–3750.
- Everything else was checked unchanged by a per-frame camera dump. The animation changes made after the pass are all inside those ranges.
- I watched every page.

## Checks on the delivered file
- `body_prop_cross`: 0 visible crossings on the window bars while sawing (2186–2440), and 0 on the cell-front bars in the ending (3676–3750).
- `qa_check` (`qa_v009.json`, run on the build before the late camera/ending fixes): INSIDE 0, HOVER 0, ROLL 0, FACEPRESS 0. CAMJUMP flags fall on the cuts (`cuts.json`), plus 2889 (the cut into the tally close-up).

## Known remaining items
- **Signs:** the protest placards stay blank. The brief forbids text, and the director confirmed this.
- **Placard grip (3620–3675):** the "small" item, where the placard is held behind his head, is not changed in this round.
