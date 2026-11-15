# DrunkTrain_v006c: farm package (director's review of v006b addressed)

v006c is v006b (see `../DrunkTrain_v006b/README.md`) plus the director's five notes from 23:28 on Nov 14. Beat frames and beat order are unchanged (`beats.json`), and there is no VO.

**`review/preview.mp4` was rendered WHOLE, in one run, from this exact package.** The file was opened with `--factory-startup` and rendered with `pipeline/preview.py` (every 5th frame, 414 frames, 4862 s). There are no staged ranges. `review/pages/p01–p09.jpg` are its contact pages, and I watched every page.

## Director notes → fixes
1. **The white studio void (1406–1680).** The studio, the bubble and the replay are all gone, and beat 10 plays in the real scene. Beat 10 is a medium shot of him standing completely limp beside the halted train, with his head in frame: he sways, his arms swing loose and his head lolls. The train and the witnesses are hidden only during the swig flashback (1261–1410). The camera keys aim at his head.
2. **Headless and body-in-lens frames (1231–1241, 1406–1416, 1551–1561, 1636–1676).**
   - At 1230 the camera is further back (lens 20).
   - From 1410 on, the camera keys hold a medium shot aimed at his head.
   - The camera never passes close to his torso.
3. **Grey slabs (1131–1136) and the whip at 1036.**
   - 1033 is now a **clean cut** to the witnesses: there is no whip pan.
   - The camera path at 1131–1185 was moved off the side frame.
   - The `Ramp` object (the grey slab) is hidden (`08_post.py`).
4. **The dazed hold (1681–1857) was too long, too dark and too still.**
   - The extra hold is gone: the beat 10 sway runs to 1680, and the dazed acting fills 1681–1857 until the walk (1858, unchanged).
   - He turns, puts his right hand to his head, staggers a step, then looks back over his right shoulder at the train.
   - A face fill follows his head from beat 9 on, and the sun is on him.
5. **Mint shirt under red light (871–896).** **Not fixed.** The shirt still reads mint/green there. Extra fills did not change it; it looks like bounce from the red-orange underframe.

The camera has two hard cuts, at **963** and **1033**. Everything else is one continuous move. The camera spline is built per segment, so it never swings across a cut.

## Checks
All checks ran on the packed file.
- **`clip_scan.py`** (b6d7900, step 6), `review/clip_scan_v006c.json`: 1 bad range, the single frame **1699** (his right hand rising to his head, near the shoulder). I rendered 1690, 1699 and 1708 as stills, and the hand is clearly outside the body, so I read it as a false positive at the shoulder joint.
- **`qa_check.py`** (c6240b2, step 6), `review/qa_v006c.json`: EMPTY 116 (the wide outdoor and under-train shots), BACKHEAD 2 and INSIDE 1.
  - BACKHEAD at 541 (beat 4): the train hits his head as he lies across the rail.
  - BACKHEAD at 871 (beat 6): he lies face down under the halted train.
  - INSIDE at 817: a single frame under the moving train during the drag.
- **`body_prop_cross.py`** (rails, loco, both wagons, all four wheelsets; Lad), `review/body_prop_cross_v006c.json`: BPC_RESULT
- Factory-startup check: `CAM_Film`, frames 1–2070, 60 fps, f/11, 0 unpacked images.

## Known issues
- **836–856:** the under-train camera comes within about 1 m of him as the train stops. His shoulder and leg fill the bottom of the frame for about 0.3 s. I found this while watching this preview and have not fixed it yet. The fix is a camera key further back at 842, the same as the keys around it.
- **871–896:** the mint shirt under the red light (note 5 above).
- **1281–1296:** in the swig, his arm crosses his chest and the T-shirt deforms around it.
- **1501–1561:** small dark specks show on his shorts in the 4-sample preview. Check them in the farm test frames.
- In the low-sample preview, deep shadows between ballast stones look black. Check them in the farm test frames.
- No audio.
