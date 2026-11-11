# PopeShot: checkpoint B (blocking)

- `review/B_blocking_1ps.jpg`: 1 still per second, 270×480 at 8 samples, from `PopeShot_anim.blend` (not committed; it is rebuilt from the scripts).
- `review/B_camera_path_top.png`: the one camera's full path from above, coloured by beat. It is one spline baked per frame, with no cuts and no camera switching.
- `beats.json`: the beat start frames for the voiceover retime.
- Build: `scripts/01_build_humans.py` → `scripts/02_build_scene.py` → `scripts/03_animate.py`.

## What is in
- **Square:** fluted colonnades (4 rows), a facade with pilasters, a balcony, a dome, distant buildings, cobbles, barriers, waving flags, 40+ MPFB crowd with FK acting (wave, cheer, clap, idle, then a gasp at the shot), and pigeons that take off at the collapse. The Pope is in white with a fitted cassock and zucchetto, standing in an open white jeep (the insignia is painted out). Aides ride in the jeep and guards walk alongside.
- **Shot:** the shooter in the crowd, a slow-motion bullet ride from the muzzle to the robe, then the x-ray porthole on the abdomen (skeleton, gut, aorta, glowing trace) and on the hand (hand bones and trace), inside a teal-navy dome.
- **Collapse:** the aides catch him under the arms (IK to his armpits). He sags with buckled knees.
- **Operating theatre:** reached through a window in the facade. He lies under a fitted drape. Three surgeons and a nurse wear fitted caps, masks and latex gloves made as body shells. The monitor shows an ECG trace that goes from ragged to steady.
- **Balcony years later:** the blessing hand is raised over the crowd below. The camera then flies through the doorway and the barred cell door.
- **Cell:** the two men are seated close together, the Pope's hand is on the prisoner's shoulder, warm beams come through the barred window, and there is haze.
- **Shrine (through the cell window):** the Mary statue with a gold crown, candle racks with flicker, and incense haze. A cleric on a step stool sets the bullet into the crown. The Pope kneels in prayer. The x-ray returns on his torso with the curved path past the aorta and spine, then the camera pulls out to the statue.

## Known gaps → fixing for C
1. The shooter's pistol needs to read clearly (from behind, out of focus) at 0–1 s and on the flash at 4.2 s.
2. 6 s: the x-ray needs a better first framing (the ribs are too close); 23 s: the camera clips the statue veil on the crown macro.
3. The cassock still reads too much like a smooth skirt and needs stronger folds and a hem. The Pope's face and brows need expression tuning, and the brows are washed out.
4. The cell is a bit dark, and the Pope must be fully visible in the orbit (17–19 s are prisoner-heavy).
5. The balcony drape is faceted, and the crowd below the balcony is too sparse in frame.
6. Pigeons have a flat material and should flock more densely across the lens at 10 s.
7. Fingers: the grasp curls on the aides' hands and the cleric's bullet pinch.
