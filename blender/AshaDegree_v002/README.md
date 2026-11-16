# B06 AshaDegree, v002 (Phase 2: built to the client's VO)

Vertical explainer, 1080×1920, 60 fps, Cycles. **Frames 1–2009 (33.5 s).** 23 shots with hard cuts.

## Contents
- `AshaDegree_v002_60fps.blend`: the farm package (84 MB, everything packed). See SETTINGS.md.
- `AshaDegree_v002_VO.mp3`: the client's VO. It is also packed in the .blend as a sound strip from frame 1.
- `beats.json`: shot start frames, computed as `1 + round(word_time × 60)`, with the first words of each shot.
- `review/preview.mp4`: the moving preview with the VO (every 5th frame, 270×480), plus the check reports.
- CREDITS.md.

## How it was built
- Source scripts: `blender/AshaDegree_v001/scripts/`, steps 01–07.
- Each set's action is animated at 1× on its own source timeline (Phase 1). Phase 2 (`06_vo_layout.py`) shifts each set by **one constant offset**. **Nothing is time-stretched.**
- Every shot has its own camera, keyed over its window. Cuts fall on the VO words.
- The S02→S03 cut falls exactly on the frame where the book bag moves from the floor to her back.
- The VO wording differs from the reference, so the layout follows the recording:
  - The motorist "turned around… approached": the car stops ahead, then reverses slowly toward her.
  - "Nobody knows why she left that night": the cyan memory figure walks the wet road.
  - "or where she went": closes on the framed portrait (our own render of the generic girl).

| Shot | Frames | VO | Picture |
|---|---|---|---|
| S01 | 1–77 | In 2000, | living room: girl kneels behind her pink book bag (toy box with our logo) |
| S02 | 78–134 | a nine-year-old girl | close: she looks up |
| S03 | 135–211 | packed a book bag and | standing, bag on her back, turns to the open French doors |
| S04 | 212–352 | quietly left her house in the rain. | walks out through the door into the rain |
| S05 | 353–456 | It was extremely early in the morning | night highway, rain, red umbrella (behind) |
| S06 | 457–535 | when a driver spotted her | front: her face under the umbrella, headlights behind her |
| S07 | 536–640 | walking beside the highway. | the car passes her (road-side camera) |
| S08 | 641–731 | He turned around to check on her, | wide: the car stopped ahead |
| S09 | 732–824 | but as he approached, | she stops and glances back, the car reverses toward her |
| S10 | 825–953 | she suddenly ran into the woods. | she runs off the road into the trees |
| S11 | 954–1004 | By daylight, | running between the firs in the rain |
| S12 | 1005–1086 | she had vanished. | she disappears into the woods |
| S13 | 1087–1169 | A few belongings were later found | day: two searchers at the shed |
| S14 | 1170–1253 | inside a nearby shed, | searcher with his clipboard |
| S15 | 1254–1308 | but there was no | torch search in the woods |
| S16 | 1309–1374 | sign of her. | a searcher sweeps his torch |
| S17 | 1375–1423 | A year later, | the wrapped pink bag in the dirt |
| S18 | 1424–1519 | her book bag was discovered buried | worker reaches for it (face visible) |
| S19 | 1520–1588 | at a construction site | wide: the site, the fallen school-crossing sign |
| S20 | 1589–1685 | inside a plastic bag, | close: his hand on the plastic |
| S21 | 1686–1811 | but it revealed nothing. | the worker looks at the bag |
| S22 | 1812–1926 | Nobody knows why she left that night, | glowing memory figure walks the wet road |
| S23 | 1927–2009 | or where she went. | the framed portrait, push-in |

## Checks on this exact packed file (`review/`)
- `body_prop_cross.json`: whole film, step 6, every held or touched prop: **0 visible crossings**.
- `limb_check.json`: step 2: **clean**.
- `clip_scan.json`: step 6: **BAD_RANGES []**.
- `qa_check.json` (multi-camera run, step 6). Every flag is expected:
  - CAMJUMP ×22: the 22 intended hard cuts.
  - PROPMOVE and ATTACH: worn items (scrunchie, caps, bags, hard hat) follow their bones through constraints.
  - INSIDE: S01 (1–77) and S23 (1927–2009) cameras sit outside single-sided room walls.
  - BACKHEAD: shots that are back views by design (S05, S08–S11, S22).
  - EMPTY: the bag close, the site wide and the portrait.
  - CLAW: SearchC's right hand closed on the torch handle (S15–S16).
- `preview.mp4`: frames 1–2009, every 5th frame, with the VO. I watched it start to finish.
  - After my first watch I fixed S10 (follow camera), S11 (wet ground less bright), S16 (fern at the lens), the torch pinky (S15–S16) and S21 (camera now moves). I then re-rendered 821–1376 and 1686–1811 from this package, spliced them in and watched them again.
