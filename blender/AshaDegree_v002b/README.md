# B06 AshaDegree, v002b (director's fix round on v002)

Vertical explainer, 1080×1920, 60 fps, Cycles. **Frames 1–2009 (33.5 s).** 23 shots with hard cuts.

## Contents
- `AshaDegree_v002b_60fps.blend`: the farm package (79 MB, everything packed). See SETTINGS.md.
- `AshaDegree_v002b_VO.mp3`: the client's VO. It is also packed in the .blend as a sound strip from frame 1.
- `beats.json`: shot start frames, computed as `1 + round(word_time × 60)`, with the first words of each shot.
- `review/preview.mp4`: the moving preview with the VO (every 5th frame, 270×480), plus the check reports.
- CREDITS.md.

## How it was built
- Source scripts: `blender/AshaDegree_v002b/scripts/`, steps 01–07. These are the Phase 1 scripts plus the Phase 2 fixes and steps 06–07. v001 stays as it passed P1, and v002 is untouched. They run from the v001 folder, which holds the `work/` intermediates.
- Each set's action is animated at 1× on its own source timeline (Phase 1). Phase 2 (`06_vo_layout.py`) shifts each set by **one constant offset**. **Nothing is time-stretched.**
- Every shot has its own camera, keyed over its window. Cuts fall on the VO words.
- The S02→S03 cut falls exactly on the frame where the book bag moves from the floor to her back.
- The VO wording differs from the reference, so the layout follows the recording:
  - The motorist "turned around… approached": the car stops ahead, then reverses slowly toward her.
  - "Nobody knows why she left that night": the girl walks the wet road. She is opaque, in her real clothes, under the red umbrella; the cooler grade marks it as a memory.
  - "or where she went": closes on the framed portrait (our own render of the generic girl).

| Shot | Frames | VO | Picture |
|---|---|---|---|
| S01 | 1–77 | In 2000, | living room: girl kneels behind her pink book bag (toy box with our logo) |
| S02 | 78–134 | a nine-year-old girl | close: she looks up |
| S03 | 135–211 | packed a book bag and | standing, relaxed bent arms; she glances at the open door and her right hand takes the bag strap |
| S04 | 212–352 | quietly left her house in the rain. | walks out through the door into the rain, still holding the strap |
| S05 | 353–456 | It was extremely early in the morning | night highway, rain, red umbrella (behind) |
| S06 | 457–535 | when a driver spotted her | front: her face under the umbrella, headlights behind her |
| S07 | 536–640 | walking beside the highway. | the car passes her (road-side camera) |
| S08 | 641–731 | He turned around to check on her, | wide: the car stopped ahead |
| S09 | 732–824 | but as he approached, | she stops and glances back, the car reverses toward her |
| S10 | 825–953 | she suddenly ran into the woods. | she runs off the road into the trees |
| S11 | 954–1004 | By daylight, | running between the firs in the rain |
| S12 | 1005–1086 | she had vanished. | she disappears into the woods |
| S13 | 1087–1169 | A few belongings were later found | day: two searchers at the shed |
| S14 | 1170–1253 | inside a nearby shed, | searcher reading his clipboard, held out in front |
| S15 | 1254–1308 | but there was no | torch search in the woods |
| S16 | 1309–1374 | sign of her. | a searcher sweeps his torch |
| S17 | 1375–1423 | A year later, | the wrapped pink bag in the dirt |
| S18 | 1424–1519 | her book bag was discovered buried | worker reaches and takes the wrapped bag by both ends |
| S19 | 1520–1588 | at a construction site | wide: he lifts it as he rises; the fallen school-crossing sign |
| S20 | 1589–1685 | inside a plastic bag, | medium: he holds it at his chest and turns it, looking at it |
| S21 | 1686–1811 | but it revealed nothing. | he lowers the bag and looks up and away |
| S22 | 1812–1926 | Nobody knows why she left that night, | the girl herself (opaque, her own clothes, red umbrella) walks the wet road, cooler night grade |
| S23 | 1927–2009 | or where she went. | the framed portrait, push-in |

## v002b changes (director's notes on v002)
1. **f1812–1926:** the glowing see-through figure is gone. It is now the normal opaque girl in her own clothes with the red umbrella and pink bag, and the world light is a cooler blue.
2. **f141–211:** her arms are relaxed with bent elbows. She glances toward the open door, and her right hand comes up to the new shoulder strap (the bag now has two dark plum straps, skinned to her body) and holds it as she walks out (S04).
3. **f1171–1251:** the clipboard is held out in front at reading distance, with a gap to his chest. S13 (1087–1169) shows the same hold in the wide.
4. **f1424–1811:** the worker now has a real action sequence, and his pose changes from shot to shot:
   - S18: deep squat; he reaches.
   - S19: he takes the bag by its two ends and lifts it as he rises.
   - S20: he holds it at his chest and turns it, looking down at it.
   - S21: he lowers it and looks up and away.

   The bag's carry loop now lies flat inside the plastic, so S17 (1375–1423) changed slightly too.

Re-rendered and spliced into the preview: 136–352, 1086–1253, 1376–1926 (each from this exact package). Every other preview frame comes from v002 and is unchanged in this file.

## Checks on this exact packed file (`review/`)
- `body_prop_cross_masks_on.json`: whole film, step 6, every held or touched prop plus the new straps, with the meshes as rendered: **0 crossings**.
- `body_prop_cross.json`: the official run. It turns the MASK modifiers off, which brings back the body skin that the shirt and sleeves hide.
  - 36 frames (139–349) flag that hidden skin (spine01, breast, forearm) against the new straps.
  - None of it can render, because those vertices are masked out; the masks-on run confirms 0.
  - The worker and the bag: **0** in both runs.
- `limb_check.json`: **clean**. `clip_scan.json`: **BAD_RANGES []**.
- `qa_check.json` (multi-camera): the same expected flags as v002.
  - CAMJUMP ×22 are the hard cuts. PROPMOVE and ATTACH are worn items. INSIDE is the single-sided walls in S01 and S23.
  - BACKHEAD flags back views. EMPTY flags the bag close, the site wide and the portrait. CLAW is SearchC's fist on the torch.
- `preview.mp4`: frames 1–2009 with the VO. I watched all the changed ranges, rendered from this package.

