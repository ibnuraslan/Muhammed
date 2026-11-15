# EscapeArtist v008: the director's v007 list, and how v008 answers it

Build: `06_fix_v007.py` (with DOF at f/11) → **`07_v008.py`** → `04_package.py`. Beat start frames are unchanged and no VO is added. Frames are film frames at 60 fps.

## Camera
- **The continuous camera is replaced by 44 short shots joined by clean cuts** (the director allowed cuts on 2026-11-14 at 23:52). The cut frames are in `cuts.json`.
- Each shot follows the acting character's head, smoothed over ±8 frames, from in front or at three-quarter, so faces show on every beat.
- Where a wall stands between the subject and the camera, the camera is pulled in to the subject's side of it. It is never inside a wall.
- Removed: the AimFix constraints, the wall- and bar-hiding keys, the fly-throughs, and every empty-wall frame (director's item 1).
- DOF is on at f/11, focus follows the subject every frame, and motion blur is off.

## The director's v007 items
| # | v007 fault | v008 |
|---|---|---|
| 1 | Empty frames (670–680, 1090, 1405, 1500–1525, 2485–2505, 2890, 3155–3175, 3485–3495, 3530–3560, 3630–3680, 3730–3750) | Every shot is on a person. Clean cuts replace the transitions. |
| 2 | Saw: hand and arm through the bars, bars across the face | Shot from inside the cell beside him, with his face in profile. His left hand grips bar 2 on his own side. The saw is in his right fist, held level, with the blade through the gap between bars 2 and 3. No arm passes the bar plane. |
| 3 | Fence: "Spider-Man" back view, T-pose on top, cardboard blanket, black-slab mesh | Side three-quarter view with his face, hand-over-hand with bent elbows, a woven wool blanket with folds and thickness, a crouch on top, then a cut to him running toward camera. The chain-link alpha texture is kept as PNG in the package, so the mesh reads as chain-link; the old JPEG step dropped the alpha. |
| 4 | Faces never shown (boy's workbench, the run, face pressed into his arm at the wall) | The boy is shot from beside the bench, the run is toward camera, and the tally is re-posed with his head up and scratching at chest height. |
| 5 | Toolbox sliding by itself, oversized; stepmother holding "nothing" | The toolbox is at 60% scale and stays still on the floor until the father's fist takes it. It hangs upright from his fist, then from the boy's, and the boy's free arm hangs relaxed. The stepmother holds a black mobile phone at her ear, with her elbow bent. |
| 6 | Stepmother: 4 s alone, hair over her face, the same point | About 1.5 s (1128–1217) at medium distance, from the side where her face is clear. Then the boy's reaction. |
| 7 | Judge: giant gavel in the lens, long pull-back | Medium shot with a 65% gavel in a hammer grip, then a cut to the gate. |
| 8 | Old man: 5 s, barely moves | Three shots (3228, 3360, 3446). He lifts his head to the window light (3392–3430), then stands and goes to the window. |
| 9 | Lens fragments (2615, 2780–2805, 3500–3525) | Gone: each shot frames a face at a distance. |
| 10 | Ends on the empty fence | Ends on his face behind the bars with a slow push-in (3680–3750). |

**Protest signs:** they stay blank. The brief forbids text, and the director confirmed this at 23:55. They bob on the sticks.

## Preview of the delivered file
- `review/preview.mp4` (62.6 s, real speed) and `review/pages/p01–p16` show the delivered `EscapeArtist_v008_60fps.blend`.
- The full `preview.py` pass ran every 5th frame. Three ranges that changed after it (camera only) were re-rendered from the final package at the same settings and spliced in: 1470–1495, 1860–1890 and 2185–2440. A per-frame camera dump shows nothing else changed.
- I watched every page.

## Checks on the delivered file
- `body_prop_cross` (the director's cc7dcb0 version):
  - Bars, WinBar_0_*, 2186–2440: **0 visible crossings**.
  - Fence, 1600–1795: the hits are his fingers hooked into the chain-link while climbing, plus his legs and seat on the blanket as he sits and swings over. The hits sit on the blanket's surface layer, and nothing passes the wire.
- `qa_check`: see `qa_v008.json`.
  - CAMJUMP flags fall on the cuts (`cuts.json`), as intended.
  - INSIDE, HOVER, ROLL and FACEPRESS are 0 on the previous build of this file.

## Known remaining items
- 2440–2470: he turns from the window with his back to the camera for about 0.3 s, before the face.
- 2590–2680: the bent tube reads as a flat white shape in his fist. It is kept brief and plain on purpose (brief: no weapon detail).
- 3500–3525: a thin dark line under the sill at the frame bottom.
- Fence 1600–1675: his chest is close to the lens.
