# Changes since B (checkpoint C)

## Look (client note at 22:45; STYLE_ANIMATED.md)
- Ran `pipeline/anim_look.py`, then `scripts/05_look.py`:
  - sky-blue gradient void
  - blue scan point cloud, green reference beak, orange CAD half, blue ghost bird, cream PLA lattice
  - brighter clinic (fill light, panels ×1.8)
  - brighter zoo (sun 6, sky fill, greener ground)

## Toucan
- Added a feather fibre layer.
- Fixed the plumage material (sheen tint).

## Beat 8
- Rebuilt the cutaway as a real gyroid infill (per-column fill plus points-to-volume) inside the cut-away printed shell.

## Void
- The "new half" grows out of the stump instead of using a boolean on the non-manifold scan.
- Fixed the reference-beak parenting.
- The void front face is camera-visible only while the camera is inside (no blank frames on entry).

## Camera
- New opening framings.
- Hollow-beak shots now view the cut face.
- Moved the macro keys off the gloves.
- Added a clearance key over the table at frame 689 (was inside VetB at 673/687).

## Enclosure
- Fence moved behind the enclosure.
- Bird on the feeding platform.
- Fig pick-up, toss, catch and swallow animated.
- Sky fill light.

## Hands rule (client note at 23:00)
- Limit Rotation on every finger, thumb and wrist.
- Relaxed curled default.
- Tool grips are solved from the handle (`grip_key`).
- Settle loops push hands out of the bird and the held prosthetic.
- Glue, pin and scanner hand-offs are sequenced so the hands never cross.
- New close-up pass: `stills/hands_closeups.jpg`.

## Faces
- Focused brows and lids, blinks, and relief at the end of the repair (MPFB face bones).

## Fixes
- `box()` was baking location into meshes, which hid the scanner 40 m underground.
- The fig twig is now vertical.
- Glue ring is thinner.
- The prosthetic is now its own object. A shared action had made the original upper beak float at 30–32 s in the C sheet; this is fixed in the current build.

## Still open, for D
- 25.0–25.4 s: the whip from the printer back to the screen shows plain wall for about 0.3 s.
- The jungle trunks read a little stake-like.
