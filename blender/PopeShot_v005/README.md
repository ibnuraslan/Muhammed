# PopeShot_v005: motion-preview fix pass on the approved v004b (d77ad0f)

I watched a moving preview (`review/preview.mp4`, made with pipeline/preview.py at every 5th frame plus watch_pages.sh), checked every contact page in `review/pages/`, and fixed each fault I found. Beat frames are unchanged (`beats.json`). No VO was added.

| Fault seen in motion (v004b) | Fix |
|---|---|
| Frames 1–60: the gun is visible only at frame 1, then the camera flies away | The camera stays over the shooter's right shoulder until frame 60, so the gun stays **in his hand** in frame while it rises |
| Frames 81–96: the guards' arms reach forward like mannequins while they walk | Hand targets now follow each guard's walking root and yaw. The arms hang at the sides with a small swing |
| Frames 241–246: a cheering crowd hand fills the lens | The camera at 240 is raised to 2.3 m |
| Frames 486–502: washed-out frames as the camera leaves the x-ray dome (same at ~1531) | The dome is drawn only from inside (backfacing mask) |
| Frames 511–531: the Pope's skirt lifts up into his torso when he slumps | The cassock is re-skinned: hips carry it, and the thighs pull the hem only 35% |
| Frames 536–556: the aide's head and arms come up to the lens | The camera at 555 moves out (FD 2.2 / PERP 1.8) |
| Frames 606–640: the crowd's "gasp" pose raised the arms to a stiff T-pose | The arms stay down and the hands come up to the chest |
| Frames 765–776: a blank green wall while the camera leaves the theatre | The theatre and facade walls are hidden from camera rays during that 12-frame pass |
| Frame ~1027: the camera flies through the cell-gate bars | The gate slides open on the "face to face" beat (frames 1000–1024) |
| Frames 1118–1132: the camera passes through the prisoner's body and his head fills the lens | Simplified: 1132 holds the two-shot (faces, the hand on the shoulder) at about 0.9 m |
| Frames 1440–1480: prayer hands too close | The orbit radius is widened |
| Frames 131–191: the open top of the skirt shows from above | The top rings of the skirt hug the waist |
| Frames 210–226: crowd members near the lens | The camera at 210 is raised 1 m |

Known and accepted:
- Two whip pans still show about 10 frames (≤0.17 s) of wall or structure mid-turn: 766–771 (theatre to square) and 1131–1141 (cell to shrine window).
- Hiding the cell wall made 1131–1141 worse (black frame), so I kept the wall.

Checks on the packed file:
- A ray scan of every 3rd frame (12 rays per frame) found no surface within 0.45 m of the lens apart from the x-ray dome, which is now invisible from outside.
- CAMJUMP maximum is 17.9° per frame.

Also carried from the earlier builds:
- The eye fix (cornea is now transparent, with no black-hole eyes).
- f/8 depth of field.
- Crowd arms bent in all wave and cheer poses.
- The shooter faces the jeep.

Files:
- `PopeShot_v005_60fps.blend`: packed, 88 MB, plain git, farm check: no problems.
- `review/preview.mp4`: moving preview (270×480, every 5th frame, 12 fps = real speed). `review/pages/`: contact pages.
- Source: `../PopeShot_v001/scripts/03_animate.py`.
