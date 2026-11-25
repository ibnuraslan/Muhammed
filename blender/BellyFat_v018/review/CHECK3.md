# v018 check 3 (after fix round 2): FAIL. Stopped here per FIX_RECIPES (2 rounds max); awaiting director OK for round 3
Preview: `review/preview.mp4` (exact package, every 5th frame, 270x480, VO). I watched all 6 contact pages; a fresh reviewer graded all 11 time-stamped pages.

## Clean now (fixed in rounds 1–2)
- Window opening reads clearly: colourful facade, blue shutters, the woman visible inside, and the bullet cracks the glass at f30. No stile blocker.
- Chase f60–110: the bullet streaks in with a short trail toward her belly, with her startled face and the logo in frame. No jeans/crotch framing.
- One bullet object throughout. It touches the fabric when it comes out of the flash; the cross-section reads (pierces skin, slows through the fascia sheets, stops at the muscle with the bowel below).
- Ending: her hand rests flat on her belly beside the hole, and the hole reads. No eye-closing wink; the face is warmer.
- Checks: clip_scan 0 bad ranges. limb_check ARMBODY is only upperarm01 points 0–1 at the shoulder (documented false positive). body_prop_cross: one bullet-into-shirt contact at f136 (intended impact, inside the flash). qa_check: EMPTY/FILL in the character-free cross-section, INSIDE/CAMJUMP only inside the two full flashes (f133–147, f1135–1139), PROPMOVE = the bullet in flight. All by design.

## Remaining (exact frames, film timeline) with the planned fix
1. **f60–100 and f1196–1273: the brass pendant lamp sits on top of her head in the background** (it reads as a hat). Fix: move `HM_Pendant` about 0.9 m sideways (x 0 to 0.9).
2. **The logo's "D" wraps round the torso side at some angles** ("IA KRAS"). The full logo reads at f1196–1273 (about 1.3 s) plus f60–100. Fix: shift and scale the tee print about 12 % toward the chest centre (`00_shirt_texture.py`, LX/scale), and hold the end framing frontal from f1180.
3. **f1157–1162: the top of her head is cut during the pull-back; f1240–1273: the head touches the top edge** (the lamp makes it worse). Fix: aim 4 cm lower in SEG_B.
4. **f1250–1273: the right fingers bend slightly** (the reviewer reads it as semi-clawed at 270 px). Fix: key the flat_palm with spread 0 at the end keys and check at 540x960.
5. **f700–830: a long, similar cross-section composition** (the reviewer calls it near-static; the bullet is slowing by design). Fix: a slightly larger orbit arc in the 715–829 keys.
6. Minor: f134–146, the bullet is seen base-first inside the flash (a cup look).
Each is a one-line change. Round 3 would be: re-package, then preview only the changed ranges (f40–110, f700–830, f1140–1273) and splice.
