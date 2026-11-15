# PopeShot_v008: director review of v007 (9b93c1d)

The shot list and clean cuts are the same as v007, plus one new cut at 1200. Beat frames are unchanged (`beats.json`) and no VO was added.

`review/preview.mp4` and `review/pages/` come from preview.py and watch_pages.sh, run on the build that is packaged here, and I watched every page.

| # | v007 note | v008 |
|---|---|---|
| 1 | The flash washed out the shooter's hair; the flash looked like a fluffy blob | The flash light is removed and character materials and exposure are untouched. The flash is now a **small orange-yellow cone** out of the muzzle, parented to the gun, for 3 frames (255–257). |
| 2 | Pope's face hidden during the hit (291–470) | His head is lifted, so the **pain shows on his face**: eyes squeezed, mouth open, brows knit. The camera is at a **3/4 front** view, framed on his face and chest. |
| 3 | Inset too small, over the columns | **About 50% of the frame width**, lower left, on a **plain dark disc with a thick white border**. The stomach, aorta and spine are clear, along with the bullet path and the **hand** with the finger wound. Shown 300–392. |
| 4 | Stiff guards; T-posed crowd extras | **Guards:** natural arm swing while walking. At the shot (262) they turn toward it and reach for the Pope (jeep-side hand), with the other hand up in alarm. **Crowd:** the "clap" pose that flung the forearms out sideways is replaced by forearms bent forward with the hands meeting in front of the chest. No extra is in a T-pose. |
| 5 | Cell: stiff straight arm; knees in the lens | They sit closer, each turned 45° to the camera, with narrower knees. The Pope's **elbow bends** and his hand rests gently on the prisoner's near shoulder. The camera is raised: **both faces and upper bodies** are in frame. |
| 6 | Bullet not visible | **I1 (1153–1199):** medium close shot of the Pope holding the bullet up toward the camera, with his face clear. The bullet is bright polished lead, 4.5× scale, lit by a small glint light. **I2 (1200–1321):** he hands it up to the cleric on the step-stool; the hands meet at 1236. **J (1322–1360):** crown close-up at f/11, with the bullet **seated front-centre** (about 15% of the frame width) and highlighted. **The ending (1546–1620) pushes in and ends on the bullet** (f/16). |

Known: in the handover shot (1200–1321) the cleric on the stool is in the left foreground, so his back fills the left of the frame. The Pope's face and the hands meeting are on the right.

Files:
- `PopeShot_v008_60fps.blend`: packed, 86 MB, plain git, farm check: no problems.
- Source: `../PopeShot_v001/scripts/03_animate.py` and `04_prepare_package.py`.
