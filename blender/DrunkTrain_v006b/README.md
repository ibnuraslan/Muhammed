# DrunkTrain_v006b: farm package (director's review of v006 addressed)

v006b is v006 (see `review/V006_notes.md`) plus the director's five notes from 22:11 on Nov 14. Beat frames are unchanged (`beats.json`) and there is no VO.

**`review/preview.mp4` was rendered WHOLE, in one run, from this exact package**, opened with `--factory-startup` (`pipeline/preview.py`, every 5th frame, 414 frames, 3492 s). There are no staged ranges. `review/pages/p01–p09.jpg` are its contact pages, and I watched every page.

## Director notes → fixes
1. **X-ray slabs and shards (1406–1606).** The muscle mesh tears in motion. I tried masking the forearms and every muscle vertex outside the glass body, and it still looked shredded, so **the x-ray is dropped**. Beat 10 ("his muscles were completely relaxed") is now his real, clothed body standing completely limp in the studio, arms swinging loose.
2. **About 4 s of a tiny figure in an empty white void.** The replay is now **1.5 s (1591–1680), framed medium on him going limp**. Then there is a **clean cut** back to the real scene, where he stands dazed beside the train (sways, head down) until the walk at beat 12 (1858, unchanged).
3. **Blue noise and the pale bubble (1851–1856).** Gone. The bubble disappears at the cut (1680→1681), so there are no bubble frames on the way out.
4. **Wagon clip as the camera rose through the gap (966–1000).** There is a **clean cut at 963** from under the train to a side view of the halted train and the gap he lies in, with the witnesses running in.
5. **Upside-down close under-train frames (651–760).** The under-train camera is 2 m ahead of him (was 1.25 m), so his whole body and the train read.

The camera is one continuous move except for the two cuts the director asked for (963 and 1681). The camera spline is built per segment, so it never swings across a cut.

## Checks
All checks ran on the packed file.
- `clip_scan.py` (b6d7900): **0 bad ranges** (`review/clip_scan_v006b.json`).
- `qa_check.py` (c6240b2, step 6): EMPTY 121 (the wide outdoor shots), BACKHEAD 2 and INSIDE 1 (`review/qa_v006b.json`).
  - BACKHEAD at 541 (beat 4): the train hits his head as he lies across the rail.
  - BACKHEAD at 871 (beat 6): he lies face down under the halted train.
  - INSIDE at 817: a single frame under the moving train during the drag.
- `body_prop_cross.py` (rails, loco, both wagons, all four wheelsets), `review/body_prop_cross_v006b.json`: **9 visible frames**. Eight are glancing contacts with the loco underframe while he is dragged (649, 685, 688, 700, 718, 721, 724, 754). One is a toe on the rail head as he climbs over (1192). The body animation is the same as v006; the wider under-train camera now shows contacts at 685–721 that were off-screen before. v005 had about 100 frames.
- Factory-startup check: `CAM_Film`, frames 1–2070, 60 fps, f/11, 0 unpacked images.

## Known issues
- Going into the replay, the camera passes close to his torso for about 0.15 s (1581–1591).
- The dazed hold (1681–1857) is a quiet 3 s: he sways and keeps his head down.
- In the low-sample preview, deep shadows between ballast stones look black. Check them in the farm test frames.
- No audio.
