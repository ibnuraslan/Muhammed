# SurgeonBrandsLivers v008f: the director's 2 notes on v008e (9df6d99)

1. **Mug at her groin, then the sideways drop (f 641–661):** the mug is removed. Her left arm hangs relaxed: it mirrors her hanging right arm, with the elbow pole keyed down. From 685 her left palm rests on the OUTSIDE of her left thigh; nothing is near the groin.
2. **Surgeon2 arms spread wide (f 1021–1031):** elbows bent, both hands flat on the drape edge in front of him (hand_poses place_hand + flat_palm) until he works at the window.

Nothing else changed. clip_scan: 0 bad ranges. qa_check and limb_check flags are as in v008e (see below). Preview `v008f_preview_every5th_270x480.mp4`: 342 frames, all watched. Director rules 1–4 hold on every frame.

## Checks on the packed file
- clip_scan: **0 bad ranges.**
- limb_check: ARMBODY 833 (shoulder-joint false positives and torso-hugging arms, checked in renders), PROPHEAD 228 (the anaesthesia mask on her face and the towel round her neck, intended), ARMBACK 1 (transit frame).
- qa_check:
  - CLAW 3 and HOVER 14: the patient's hands under the drape, not visible.
  - CAMJUMP 8: the clean cuts above.
  - PROPMOVE 42: the burn sparks (effects) and the dropped mug falling.
  - EMPTY 40: the liver-alone studio shots.
  - ATTACH 37: masks sit about 2 cm off the skin, as fitted since v002.
- Preview: `v008f_preview_every5th_270x480.mp4`, every 5th frame, 270×480, Cycles 4 samples + denoise, 342 frames, all watched.
