# Fix recipes for batch 1 (use these exact solutions; do not invent new ones)

Every batch 1 fault comes from the same few causes. Pick the matching recipe and use it as written.
The goal is a clean film in ONE build pass, under a small budget.

## Process (mandatory)
1. Read your film's section in `BATCH1_FAULTS_05-35.md` (or `BATCH1_FAULTS_01-03.md`) and `RECURRING_FAULTS.md`.
2. Write a short plan: map each fault to a recipe below. Then build ONCE.
3. Make ONE preview from the exact package.
   - Check every 5th frame for the whole film.
   - Check EVERY frame in contact shots, meaning any shot where hands touch bodies or props, or bodies touch furniture.
4. All clean: push and report. Anything left: report the exact frames and STOP. No looping and no extra passes without the director's OK.

## Recipes
- **R1 Clothing (balloons, stumps, onesies, sleeve gaps, nudity reads)**
  - Use one joined garment mesh per outfit, made by shrinkwrapping a duplicate of the body at an offset of 0.6–1 cm, then a solidify modifier.
  - Use long sleeves and long trousers.
  - Hide the body skin under the garment.
  - Use dark or contrasting colours.
  - Never use loose box tops, short sleeves on a raised arm, or jackets with shoulder pads.
- **R2 Hands on surfaces (through tables, chairs, bodies)**
  - Use an IK target empty placed ON the surface, found by raycasting, plus 0.5 cm.
  - Lock the hand with a Child Of constraint for the whole hold.
  - Prefer poses where the hands rest on the edge of the surface, not into it.
- **R3 Seated or lying people (legs through chairs, sinking into beds)**
  - Snap the pelvis to the seat or mattress top surface.
  - Put the feet on the floor with IK.
  - Keep the knees bent at 90°.
  - Run the clip_scan check on every frame.
- **R4 Props (floating, popping, flipping, wrong object)**
  - Use ONE prop object, parented with a Child Of constraint to the hand bone while held.
  - Switch the constraint influence on the release frame so the prop stays on the surface.
  - Never swap meshes between shots, and never hide or show a prop mid-shot.
- **R5 Story beat (ear growing, lego in the nose, monkey stitched)**
  - Use ONE shape-key or scale animation over the full beat, in one continuous close shot, with nothing covering it.
  - No pop-in.
- **R6 Twisted limbs and helicopter wrists**
  - Set rotation limits on the forearm and wrist bones (twist ±40°).
  - Hand-key the wrist instead of letting IK spin it.
- **R7 Stiff people**
  - Keep the elbows bent at 15–30°, add arm swing on walks and add a breathing loop.
  - Never use a T- or A-pose. Keep holds under 1 s.
- **R8 Framing**
  - Frame faces from mid-chest up.
  - Put a close-up insert ONLY where the action is clean in every frame. When in doubt, frame wider and hide the hands.
  - Nobody is cut by the frame edge.
- **R9 Continuity**
  - Characters keep the same chair, pose side, wardrobe and props across cuts.
  - End on a held, complete gesture and never cut mid-motion.
- **R10 Hard problem? Simplify it, don't patch it.**
  - If a contact keeps failing, change the staging so the contact isn't on screen: cut away, move the camera or reverse the angle.
