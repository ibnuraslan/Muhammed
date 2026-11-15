# PopeShot_v010: director review of v009 (4c82020)

Beat frames are unchanged (`beats.json`) and no VO was added.

`review/preview.mp4` and `review/pages/` come from preview.py and watch_pages.sh, run on the build that is packaged here, and I watched every page.

| # | v009 note | v010 |
|---|---|---|
| 1 | Cell: low, close camera; blurred knees; silhouette behind the bars | The camera is at **seated eye level, 2 m away** (1015–1152): a side two-shot with both faces in the upper half, his hand on the prisoner's shoulder, and their hands visible. There are no knees in the foreground. The balcony aide (the silhouette) is removed from the scene from 1015. |
| 2 | Surgery: blob under the sheet; unclear face | The camera is flipped to the **head end** (631–762). The Pope's face with the **oxygen mask** is in the foreground, upside-down, and the masked surgeons are behind, working at his abdomen. |
| 3 | Ending: empty room, man in black | The cleric is removed from the shrine from 1361. One move (1546–1620): **his praying face**, then his profile. The camera swings behind him, so **his head is in the foreground with the crowned statue ahead**, then pushes to the crown and ends on the bullet. |
| 4 | Collapse overhead too long | The hit shot runs to 545, so he is seen sagging into the aides' arms. The wide shot is now **1.4 s** (546–630). |

Known: about 4 frames near 1578, mid-swing, show the statue with his head just out of frame.

Camera: every turn inside a shot is at most 10° per frame.

Files:
- `PopeShot_v010_60fps.blend`: packed, 86 MB, plain git, farm check: no problems.
- Source: `../PopeShot_v001/scripts/03_animate.py` and `04_prepare_package.py`.
