# Checkpoint C: polish notes

## Sheets
- `C_polish_0.2s_00-12s.jpg` and `C_polish_0.2s_12-25s.jpg`: stills every 0.2 s at 270×480, 8 samples.
  - These were rendered before the manuscript-grasp fix.
- `C_closeups.jpg`: the clipping pass, with a 270×480 close-up of every contact moment.
- `C_grasp_fix_f1212_1240_1262.jpg`: the pocket grasp and the lift after the fix.

## Audit (`audit_C.json`, every 5th frame, frames 1–1500)

| Check | Count |
|---|---|
| Feet hover or sink (more than 1.5 cm) | 0 |
| Planted-foot slide | 0. The right foot's step back at frames 200–222 is a deliberate step. |
| BVH penetration: hands against props | 2 (left fingers into the brass rail by under 4 mm while gripping) |
| BVH penetration: feet against car | 0 |
| BVH penetration: head items against face/body | 0 |
| Camera inside geometry, outside the x-ray dome | 0 |

Grip gaps, as the closest finger point to the held surface:

| Grip | Gap |
|---|---|
| Rail | 0 mm |
| Podium | 3 mm |
| Hat | 1 mm |
| Manuscript | 6 mm before the fix; now snapped into the fist, 4 mm |

## Changed since B
- **Moustache:** now real particle-hair strands, coloured brown, rather than the black mesh slug. Spectacle arms were moved clear of the head (0 overlaps).
- **Contacts:**
  - Feet raised 1.5 cm, since the shoe soles sank.
  - The rail and podium hand targets were raised so the fingers wrap the rail or rest on top.
  - The hat offset was fixed.
- **Manuscript grasp:**
  - The fingers land on the top edge inside the pocket, with the IK target corrected against the finger bones.
  - The hand-off is solved one frame early, so the paper sits in the fist.
  - The lift eases in, with no wrist-orientation snap.
- **Set swap:** the street is hidden at frame 506 and the hall shown at frame 1165, both behind the opaque dome. No car or rail shows inside the cutaway any more. The smoke volume is hidden after the swap.
- **Look:**
  - Night grade, with dimmer windows, HDRI and moon.
  - Crowd clothing tinted to period wool tones, with no modern denim and no printed T-shirt.
  - The hero is heavier and older.
- **Cutaway:**
  - Framings reworked.
  - Pencil-line marks show on the sheets.
  - A warm highlight glow comes up on the manuscript (beat 4) and the steel case (beat 5).
  - Smaller muscle patch, shorter bullet streak, darker steel.
  - Only the rib cage is kept from the skeleton.
- **Hall:** bunting on the side walls and back wall, striped banners, pilasters and a larger wall clock (2.4 m) with spinning hands.
- **Camera:** extra framing at the start; the 3 s framing is higher (no longer under the legs).

## Known issues and next steps
- The opening 0–1.2 s wide is still fairly slow. I'll speed it up.
- At 8.0–8.4 s the camera comes very close to the paper and the frame is almost all white. I'll pull back.
- The feet close-ups inside the car footwell are too dark to judge; the numeric audit is clean.
