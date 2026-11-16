# FridgeTenYears_v002: checks on the packed file (`FridgeTenYears_v002_60fps.blend`, frames 1–1651)

| Script | Result |
|---|---|
| clip_scan (step 6) | **0 bad ranges** |
| body_prop_cross (step 3, every rig in its own range, all cooler, wall, skeleton and box props) | **0 visible crossings** except the 4-edge MPFB hip-helper cube on the worker (masked, never renders: frames 1–115, while he is on the cooler top) |
| qa_check (step 6) | every flag explained below |
| limb_check (step 2) | ARMBODY: 2–3 points at the shoulder end of upperarm01 (indices 0–2). This is the known false positive in LESSONS §4. ARMBACK ×2 at S02 f ~130: the arms fly up as he tips back off the edge (watched, reads as a flail) |

## qa_check flags
- **CAMJUMP ×19** fall exactly on the 19 hard cuts (75, 163, 251, 348, 456, 511, 584, 685, 756, 885, 953, 1019, 1095, 1155, 1298, 1355, 1431, 1481, 1559). They are intended.
- **EMPTY:**
  - 103–347: the worker is small in the gap as seen from above (S02 end, S03 crane, S04). He is visible on every preview frame.
  - 456–583: S07/S08, the coolers and the condenser fan. The VO names "the noise from the coolers".
  - 1019–1093: S13, the abandoned store ("ten years later").
  - 1483–1555: S19, the skeleton alone ("the man's remains"; the skeleton is not an MPFB character).
- **BACKHEAD:**
  - 757 / 883 / 955: the detective's back in the two-shots where the manager's face is on camera (S10), and at the start of S12 before he turns to camera.
  - 1297 (ConB) and 1357 / 1429 (ConA): the S16/S17 logo shots from behind, at the director's request. Faces read in S14, S15, S18 and S20.
- **CLAW / FAN 1183–1291:** ConA's `point` pose in S15. The index finger is straight and the other fingers curled, which the script counts as a fanned hand.
- **ATTACH ×39:** the hard hats sit 6.9 cm off the skin because they rest on the hair. They are bone-parented to the head and move with it.
