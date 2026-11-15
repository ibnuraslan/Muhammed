# PopeShot_v006: director review of v005 (e8fffd3)

Fixes from the director's review of v005. Beat frames are unchanged (`beats.json`) and no VO was added. `review/preview.mp4` and `review/pages/` come from preview.py and watch_pages.sh, run on this build, and I watched every page.

| v005 note | v006 |
|---|---|
| 1. **X-ray** (hollow cut-open robe, glass torso and organs, glass skeleton hand, blue/sand void) | **Removed entirely.** The robe stays solid. No anatomy, glass hand or dome; the anatomy meshes are deleted from the package. The camera holds medium shots of the Pope in the square (334–480) and a side view of him praying in the shrine (1405–1520), clear of the altar candles. A **small round inset diagram** appears in the upper-right corner for about 2.5 s and 1.7 s (340–488 and 1414–1515). It is a clean side-view cut-away: torso outline, spine, aorta, stomach and intestines, with the bullet path drawing itself between them and missing the aorta and spine. It has no text, is camera-only, and sits near the focus plane so it stays sharp at f/8. |
| 2. Blurred wall and beige blur on the whip from the cell to the shrine | **Clean cut** at frame 1129: the prisoner two-shot cuts to the shrine window. |
| 3. Black window-bar frames on the whip from the theatre to the square | **Clean cut** at frame 763 (the "years later" beat). The theatre framing is pulled back to the whole team before the cut. |
| 4. Surgery: blocky patient shape; a surgeon's hands at the patient's head | The drape is a smooth blanket over the body: true height per band and a flat-topped profile, smoothing 14 and subdivision 2. SurgA and SurgB now stand level with the abdomen, and their hands rest on the drape over it. SurgC, at the head end, holds a sterile pose at his own chest and touches nothing. |
| 5. Ending: about 4 s static wide shot from behind | A continuous **push-in** past his shoulder as he prays, ending close on the statue's **crown with the bullet** seated in it (frames 1555–1620). |

Also:
- The skirt now starts under the jacket hem, so there is no visible waist rim or tub shape. Its top is closed and follows the lower spine when he bends.

Known and minor:
- Around 1361 and 1406 the camera moves into the shrine side view. For about one preview frame each it shows a bare altar top, then a glimpse of a green wall beyond the shrine.

Camera:
- One take, apart from the two director-requested cuts.
- Every other turn is at most 17.8° per frame.

Files:
- `PopeShot_v006_60fps.blend`: packed, 86 MB, plain git, farm check: no problems.
- Source: `../PopeShot_v001/scripts/03_animate.py` (look for the `INSET DIAGRAM`, `CUTS` and drape sections) and `04_prepare_package.py`.
