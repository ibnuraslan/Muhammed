# AIAsleep v004b

The same as the approved v004 (`blender/AIAsleep_v004/README.md`), with one camera polish (director, Nov 12 18:13 UTC):

- **CAMJUMP fix:** at f947 (132° in one frame) and f252–253 (61°), the aim swung from his face (behind the camera) to the dash HUD (in front) and passed straight under the camera. That flipped the Track To roll and read as a hard cut.
- The aim is now routed sideways through the passenger side at f252 and f944, so both moves are continuous whip-pans across the passenger window.
- The largest per-frame turn in the film is now 15.9° (`AIAsleep_v001/scripts/cam_turn.py`, full rotation incl. roll), and qa_check CAMJUMP is 0 (`qa_v004b.json`).
- Nothing else changed: beats.json and all other camera keys, acting, look and hands are identical.
- qa_check flags EMPTY on five more samples (241, 247, 253, 937, 943). Those are the mid-pan frames of the two whip-pans, about 0.2 s each, showing the passenger window.
