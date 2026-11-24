# Round 3 (director-approved targeted round): stopped before the preview. The numeric audit failed.

This is a work-in-progress copy of `04_animate.py`. The delivered package was built from `../04_animate.py` (check 3, ON HOLD).

## What worked (numerically)
- **Carry:** palms on the left and right sides of the skull, fingers pointing up and back. Getting there took three changes:
  - the wrist limits widened (flex ±75°, side ±45°);
  - the lift lowered to 3 cm, with a 1.5 cm arc;
  - more forward lean.

  Result: 0 fingertip frames inside the head, and 0 frames with a forearm in front of the head.
- **Sideways shift:** from frame 1130 the surgeon stands 18 cm to his right, and his elbow poles follow.
- **Neck disc:** coloured to the skin tone.

## What failed
- **Ring grip on the needle holder:** each finger bone is posed directly. The thumb and ring finger go into the rings, the index runs along the shaft, and the tool offset is taken from the posed fingers.
  - With the tool sloping in from the shoulder side, all 13 seam points are reachable. But the fingers sink up to 50 mm into the monkey's shoulder (frames 468–631).
  - Approaches from above or along the skin normal can't be reached: 0 of 13 seam points.
- **Carry forearms:** the new carry grip puts the left forearm 36 mm into body B (frames 232–272) and the right forearm 33 mm into body A (frames 209–232).

## Next step
- Hand-key the stitching arm interactively. Alternatively, restage the stitch on the side of the neck facing the surgeon, with the monkey's seat turned 30–40° toward him.
- Raise the carry so the forearms clear the monkey bodies.

## Seat-rotation restage (director-approved): audit not clean, so I stopped
Changes in this pass:
- Recipient B, its seat and its backrest turned 35° toward the surgeon. The neck seam now faces him.
- The head slerps into the new orientation during the carry.
- The lift is raised to 6 cm for forearm clearance.
- Note: these WIP copies sit one folder deeper than `scripts/`. To run them, copy them back into `scripts/`; that's how I ran them. From here, their path to `pipeline/` and to `camera_keys.json` is wrong.

Audit results (every frame):
- **Stitching (450–580):** the ring-grip fingers are still up to 50 mm inside body B. Rotating the seat didn't help; the posed hand still ends up on the shoulder.
- **Carry:** fingertips are inside the head at frames 282–291 (up to 26 mm). The right forearm is up to 22 mm inside body A at frames 212–223.
- **Beat 7 (1108–1310):** the hand on the shoulder has fingers inside the rotated body, up to 40 mm.
