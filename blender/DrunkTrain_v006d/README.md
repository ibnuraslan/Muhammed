# DrunkTrain_v006d: farm package (director's review of v006c addressed)

v006d is v006c (see `../DrunkTrain_v006c/README.md`) plus the director's three notes from 05:14 UTC on Nov 15. Beat frames and beat order are unchanged (`beats.json` is identical to v006c), and there is no VO. As the director approved at 05:22, the notes are fixed with cuts and action, not by moving beats.

**`review/preview.mp4` was rendered WHOLE, in one run, from this exact package.** The file (md5 `f1876e5fcb59ff57767e817f6f90945d`) was opened with `--factory-startup` and rendered with `pipeline/preview.py` (every 5th frame, 414 frames, 5004 s). There are no staged ranges. `review/pages/p01–p09.jpg` are its contact pages, and I watched every page.

## Director notes → fixes
1. **Mannequin stance (1690–2000).**
   - **Cause:** this MPFB rig's rest pose has the elbow bent 46.5°, and the shared hand library sets the elbow IK limit to `ik_min_x = 0`. The arm could never straighten past its rest bend, so every "hanging" arm was held at about 45° with the elbows out.
   - **Elbow fix:** the Lad's elbow limit is opened to −34° (about 12° of bend left). It is keyframed only from 1681 on (the right arm from 1753, once his hand is down), so earlier, approved shots are untouched. This is in `03b_fx_camera.py`; the shared library is not changed.
   - **Arm pose:** the elbow pole now points straight back, and the hands hang a little wider so they clear the thighs.
   - **Acting order:** he puts his right hand on top of his head and rubs it (1687–1753; before, the palm faced out and it read as a wave). Then he looks back over his right shoulder at the train (1743–1803), staggers a step (about 1809), and walks toward the camera from 1858.
   - **Not done as asked:** the section is still 1681–1857 (about 3 s, not 2.5 s), because beat 12 (the walk) starts at 1858 and beats are unchanged. It also does not end on a medium shot of him rubbing his head: the rub comes first, then the look-back and the stagger, which lead into the walk.
2. **Near-black under-train (860–1000).**
   - The side-view cut moved from 963 to **906**, so the under-train shot after the stop is about 0.75 s.
   - A fill light under the train (`UnderFill`) runs at 170 W from 13.8 s to 16.4 s.
   - The camera at 842 is 1.8 m from him. **It is 0.36 m above the ballast, not 1 m:** the underframe leaves no room for a 1 m camera height under the train.
3. **Wheel/coupler filling the lens (about 1140–1145).** A new hard cut at **1147** replaces those frames. After the cut (1151–1161), the coupler and wheel fill the top of the frame while he crawls out below, and 1166–1176 is a close shot of his face beside the wheel. Neither fills the lens.

The camera has three hard cuts, at **906**, **1033** and **1147**. Everything else is one continuous move. The camera spline is built per segment, so it never swings across a cut.

## Checks
All checks ran on the packed file.
- **`clip_scan.py`** (step 6), `review/clip_scan_v006d.json`: **0 bad ranges.** The first v006d build had hands into the thighs during the walk (1873–1969); the arm fix above cleared them.
- **`qa_check.py`** (step 6), `review/qa_v006d.json`: EMPTY 109 (the wide outdoor and under-train shots), BACKHEAD 2, INSIDE 0 (v006c had 1, at 817).
  - BACKHEAD at 541 (beat 4): the train hits his head as he lies across the rail.
  - BACKHEAD at 871 (beat 6): he lies face down under the halted train.
- **`body_prop_cross.py`** (rails, loco, both wagons, all four wheelsets; Lad), `review/body_prop_cross_v006d.json`: **9 visible frames**, the same frames as v006c. Eight are glancing contacts with the loco underframe while he is dragged (649, 685, 688, 700, 718, 721, 724, 754). One is a toe on the rail head as he climbs over it (1192).
- Factory-startup check: `CAM_Film`, frames 1–2070, 60 fps, f/11, 0 unpacked images.

## Known issues
- **871–896:** the shirt still reads mint/green under the red light.
- **1281–1306:** in the swig, his arm crosses his chest and the T-shirt deforms around it.
- **1501–1561, and 1931–1966 in the walk:** small dark specks or a dark notch show on his shorts in the 4-sample preview. Check them in the farm test frames (1530 is in `SETTINGS.md`).
- **1751–1990:** he stands and walks wide-legged (drunk). The arms now hang naturally, but the stance is unchanged.
- In the low-sample preview, deep shadows between ballast stones look black. Check them in the farm test frames.
- No audio.
