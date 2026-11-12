# PopeShot_v004b: camera polish on the approved v004 (11c9991)

The only change from v004 is the camera. One-frame snaps (frame 605: 122° in one frame; frames 1126–1127: 84° then 70°) are eased into short whips.
- **How:** the baked camera orientation is post-processed. Any turn over 18° per frame is spread with a smoothstep slerp across a window that grows with the turn (8–20 frames in total).
- **Unchanged:** start and end framings, camera positions, the lens and every other frame. Story-beat frames are identical (`beats.json`).

- `PopeShot_v004b_60fps.blend`: packed, 88 MB, plain git.
- `review/qa_check_v004b.json` (qa_check fc62c27, step 12, run on the packed file):
  - **CAMJUMP 0, ROLL 0.** The maximum turn is now 17.9° per frame.
  - INSIDE 7 (x-ray dome), EMPTY 12 unique frames (transitions, the crown insert, and frame 1129 mid-whip from the shoulder to the cell window), BACKHEAD 1 (frame 1153, the beat-7 wide).
  - HOVER, CLAW, FACEPRESS and FILL are 0.
- Source: `../PopeShot_v001/scripts/03_animate.py` (the camera bake section).
