# DrunkTrain_v006e: farm package (director's review of v006d addressed)

v006e is v006d (see `../DrunkTrain_v006d/README.md`) plus the director's five fixes from 09:03 UTC on Nov 15. Beat frames and beat order are unchanged (`beats.json` is identical to v006d), and there is no VO.

**As the director asked, only the changed ranges were re-rendered, from this exact package** (md5 `5f148371e8c1e61e75b3ee36237bcaa8`). Each range was opened with `--factory-startup` and rendered with `pipeline/preview.py` at every 5th frame:

| Range | Clip | Pages | Covers |
|---|---|---|---|
| 1140–1240 | `review/r_1140_1240.mp4` | `pages/r_1140_1240_p1.jpg` | fixes 2 and 5 |
| 1255–1330 | `review/r_1255_1330.mp4` | `pages/r_1255_1330_p1.jpg` | fix 3 |
| 1405–2000 | `review/r_1405_2000.mp4` | `pages/r_1405_2000_p1–p3.jpg` | fixes 1 and 4, plus the dazed section and the walk |

I watched every page. Frames outside these ranges are unchanged from v006d, apart from the shorts fix (4), which applies everywhere. The whole-film clip scan below covers that.

## Director notes → fixes
1. **A-pose arms in beat 10 (1556–1600).** The same elbow-limit fix as v006d now starts at 1411, the start of beat 10. The arms hang loose at his sides with a slight bend and a small sway, elbows back. The right elbow closes again at 1681–1752 while his hand is on his head (otherwise the IK lifts the arm into a wave), then reopens.
2. **Blown-out ballast with black holes (1186–1221).** The cause was the `UnderFill` point light. It sat 0.45 m above the ballast and stayed on at 60 W until 1260, after he had crawled out into the sun. It now fades out by 1150, before the cut into the coupling gap. The exposure lift there is also down from +0.7 to +0.15. The ballast now reads as grey stones with normal shadows from 1150 to 1240.
3. **Sleeve stretching in the swig (1281–1311).**
   - **Cause:** his head tips back 44°, so his real mouth sits 17 cm behind and 8 cm above the rest-pose target. The hand was chasing the wrong spot, and the elbow went up and back, stretching the sleeve.
   - **Hand target:** the wrist now aims at the real mouth, and the elbow pole is low and in front of the chest.
   - **Bottle:** in this grip the bottle neck runs along the palm normal (measured), so the palm normal points at the mouth. The neck tip is now at his lips (8 cm from the mouth point at 1300).
   - **Result:** the shoulder and sleeve stay intact.
4. **Black notch on the shorts.**
   - **Cause:** a mesh fault, not the texture. The body's `Delete.male_casualsuit06` group, which hides skin under the shirt, reached below his hips. A patch of thigh skin above the `short02` hem was deleted, so the camera saw into the inside of the shorts.
   - **Fix:** `08_post.py` removes the 1452 leg vertices (below the hip joints) from that group.
   - **Check:** the whole-film clip scan shows no skin through the clothes anywhere.
5. **Shoulder in the lens (1166).** A new hard cut at **1171** goes straight from the coupler/wheel shot to the face framing. 1147–1170 is the wheel shot, with him crawling up from the gap behind the rail.

The camera has four hard cuts, at **906**, **1033**, **1147** and **1171**. Everything else is one continuous move.

## Checks
All checks ran on the packed file.
- **`clip_scan.py`** (step 6, whole film), `review/clip_scan_v006e.json`: **0 bad ranges.**
- **`qa_check.py`** (step 6), `review/qa_v006e.json`: **still running when this README was committed**; the result will be added here.
- **`body_prop_cross.py`** (rails, loco, both wagons, all four wheelsets; Lad), `review/body_prop_cross_v006e.json`: **still running when this README was committed**; the result will be added here.
- Factory-startup check: `CAM_Film`, frames 1–2070, 60 fps, f/11, 0 unpacked images.

## Known issues
- **871–896:** the shirt still reads mint/green under the red light.
- **1175–1185:** a close shot of his face and shoulder beside the wheel. The face reads, but his shoulder is big in the bottom of the frame for about 0.2 s.
- **1300–1330:** the bottle is large in the bottom of the frame at his mouth. It is sharp, not a blur.
- **1751–1990:** he stands and walks wide-legged (drunk). The director asked to leave this alone.
- In the low-sample preview, deep shadows between ballast stones look black. Check them in the farm test frames.
- No audio.
