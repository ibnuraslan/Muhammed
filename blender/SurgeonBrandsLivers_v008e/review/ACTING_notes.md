# SurgeonBrandsLivers v008e: the director's 5 notes on v008d (38e3ea4) and the 4 simplify rules

v008e is the approved v008c plus `13_preview_fixes.py` and the camera keys in `04_camera.py`.
- Beat frames are unchanged (1/301/565/637/781/1045/1231/1501, end 1710). No VO.
- Frames below are my film frames (preview index n ≈ (f−1)/5).

| # | Note | v008e |
|---|---|---|
| 1 | Studio branding (f 135–275): blob glove, floating open glove, giant glove on the way in | **Re-staged simpler:** no hands and no pen in the studio at all. The liver sits alone in the light and the S, then the B, burn in (sparks + hot trail), like the accepted 1040–1200 shot. No hand appears anywhere without its arm. |
| 2 | Gavel floats (f 1501–1551) | From the pick-up (1484) to the end, the gavel's grip point sits in the judge's **evaluated palm on every frame**. It keeps its designed raise and strike rotation, and the head comes down on the block at 1538. |
| 3 | Surgeon2 low shot, arm across his face (f 1176–1186) | The camera no longer goes near his arm. It looks down at his gloved hands working at the incision (both arms entering from the frame top), then rises to his face at 1199. |
| 4 | Woman at home: "wing" elbow (f 646–656), hand at her groin (f 656–700) | Hands placed with `hand_poses.place_hand`. Mug: held low in front of her (no raised elbow) until she drops it; the mug rides in her hand on every frame. Then one palm on her right side under the ribs (the liver) and the other on her left thigh above the knee. clip_scan is clean at home. |
| 5 | Clerk: straight, over-long arm; hair over her whole face (f 1650–1686) | Her left hand rests flat on the desk beside the licence, with the elbow down and bent (elbow pole keyed). Head and neck tilt up, so an eye, the nose and the mouth read. |

## Director rules 1–4 (Nov 14 17:26), on every preview frame (watched start to finish)
1. **Risky hand/prop actions simplified:** the studio pen and gloves are gone (liver alone). The gavel is locked to the palm. The mug is in hand or falling after the drop. The clerk's hand is flat on the desk.
2. **No arm crosses another person's body or face on screen.** The Surgeon2 shot is re-staged.
3. **No camera move passes through or brushes a body, arm, cap or wall.**
   - The four studio transitions are clean cuts (133, 275, 1057, 1175).
   - The three wall passes are now clean cuts too: calendar→home 637, home→OR 776, OR→hearing 1238.
   - The whip past the anaesthetist's drape is removed; the camera holds on Surgeon2 until the cut.
4. **No hand without its arm.** The studio has no hands. Surgeon2's hands come with arms from the frame top. Every other hand is on a visible body.

## Checks on the packed file
- clip_scan: **0 bad ranges.**
- limb_check: ARMBODY 833 (shoulder-joint false positives and torso-hugging arms, checked in renders), PROPHEAD 228 (the anaesthesia mask on her face and the towel round her neck, intended), ARMBACK 1 (transit frame).
- qa_check:
  - CLAW 3 and HOVER 14: the patient's hands under the drape, not visible.
  - CAMJUMP 8: the clean cuts above.
  - PROPMOVE 42: the burn sparks (effects) and the dropped mug falling.
  - EMPTY 40: the liver-alone studio shots.
  - ATTACH 37: masks sit about 2 cm off the skin, as fitted since v002.
- Preview: `v008e_preview_every5th_270x480.mp4`, every 5th frame, 270×480, Cycles 4 samples + denoise, 342 frames, all watched.
