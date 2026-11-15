# PopeShot_v007: director review of v006 (e3b1066)

The film is now cut into shots with clean cuts, as the director's notes allow. Beat frames are unchanged (`beats.json`) and no VO was added.

`review/preview.mp4` and `review/pages/` come from preview.py and watch_pages.sh, run on the build that is packaged here, and I watched every page.

| # | v006 note | v007 |
|---|---|---|
| 1 | The shooter is never seen to shoot | **A (1–74):** his face in profile as he raises the gun, which is in his hand. **C (238–261):** profile again as he fires, with the muzzle flash at 255. Then **cut to the Pope** being hit. |
| 2 | Stiff Y-pose for about 4 s; tiny inset; no reaction until about 500 | The slow motion is removed, so the hit plays in real time. **D (262–467):** at 258 he flinches. His right hand clutches his stomach and the wounded left hand jerks back, then stays at his chest. His face shows pain and he slowly sags. The **inset** is about 46% of the frame width for 1.5 s (300–392). It shows the side-view torso with stomach, aorta and spine, the bullet path drawing itself between them, and a **hand** with the wound marked on the finger. |
| 3 | A guard fills the lens; the camera circles the jeep | **E (468–630):** one held, high medium shot of the aides catching him and lowering him into the jeep. The camera is above the guards' heads. |
| 4 | Surgery from above, with a hollow drape tube | **F (631–762):** medium shot from beside the table at head height. His **face with an oxygen mask** (and tube) is on the table, masked surgeons are around him, and their hands rest on the drape over the abdomen. |
| 5 | Empty frames | Clean cuts at 631 (no empty facade), 1015 (no empty cell door), 1153 (no empty chapel) and 1361 (no candle table). The balcony (763–1014) holds a front view of the Pope instead of drifting into the corridor. |
| 6 | Prison visit: arm through the body, back in the lens | **H (1015–1152):** a side two-shot. Both sit at the same depth, each turned 30° toward the camera, so both faces are visible. His **right** hand goes to the prisoner's near shoulder in the gap between them and crosses no body. The prisoner's face shows sorrow (lowered brows, trembling lip). |
| 7 | The Pope never places the bullet | **I (1153–1321):** a wide medium shot with the statue and crown in frame. The Pope, beside the cleric's step-stool, **hands the bullet up** (the hands meet at 1236). The cleric then sets it in the crown at 1320. **J (1322–1360):** crown close-up at **f/11**, with the crown at about half the frame width and the **bullet visibly set** in its front. |
| 8 | Kneeling Pope, white back in the lens | **K (1361–1545):** a held 3/4 front view of his face as he prays. |
| 9 | Flat white robe and jeep | **Cloth shader** on the cassock, jacket and skullcap: warm off-white, fine weave bump and sheen. **Paint shader** on the jeep: clear-coat over off-white. |

The ending, **L (1546–1620)**, is a push-in past his shoulder to the crown with the bullet, at f/11.

Camera: every turn inside a shot is at most 7.8° per frame.

Files:
- `PopeShot_v007_60fps.blend`: packed, 86 MB, plain git, farm check: no problems.
- Source: `../PopeShot_v001/scripts/03_animate.py` (`SHOTS`, the hit reaction at `HIT = 258`, the shrine handover `HP`/`HO`, the inset, oxygen mask and v007 shader sections) and `04_prepare_package.py`.
