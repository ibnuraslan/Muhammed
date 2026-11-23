# BellyFat_v017

This is the clean build after the director's v013 review (10 items) and the FIX_RECIPES passes (v015–v017). v010–v016 are left untouched. It keeps the same VO, timing and frame range: **frames 1–1273 at 60 fps**, with the VO (21.0 s) packed.

## Files
- `BellyFat_v017_60fps.blend`: the render file, 71 MB, everything packed. `SETTINGS.md` is the render sheet and shot table.
- `review/preview.mp4`: the one small preview, rendered with `pipeline/preview.py` from the exact package (every 5th frame, 270×480, 4 samples, with the VO). `review/pages/` holds its contact pages; I watched every page.
- `review/*.json`, `review/audit_hands.txt`: the checks on the package. clip_scan, audit_hands and body_prop_cross ran on **every frame**.
- `beats.json`, `CREDITS.md`, `scripts/` (the full rebuild).

## The 10 items (v013 review)
1. **Opening.** A medium shot of the shop window from inside: it cracks and shatters as the bullet streak flies through. Then a cut to her startled face.
2. **Impact.** The bullet streaks into her shirt at f72. The shirt dents at twice the v015 depth, peaking at f76, with a ripple, her body jolts and she staggers. Her right arm is flung out to the side, clear of her body.
3. **Box.** The jolt shakes the box out of her left hand, and you see it tumble to the floor (f74–105). It lies there afterwards.
4. **Fat shot.** One continuous push. The bullet stops in the fat at f278, and the fat jiggles while the camera keeps pushing until the cut at f330, a 0.9 s hold.
5. **Extras.** Their elbows are bent and none stands in an A-pose. A shopper reacts behind her in R1, and the male shopper walks over to her in R3. No hand-to-mouth or hand-to-body poses.
6. **Two-shot (R3).** Sharper and tighter, with both faces fully in frame and the basket moved out of the lower left.
7. **Hands on her belly.** Only her right hand is on her belly: an open flat palm, placed on the shirt and settled out of it by BVH ray tests. Her left hand hangs relaxed at her side. No fingertips sink into her body.
8. **Left arm.** Never hanging straight or splayed. It is relaxed with the elbow bent.
9. **Bullet hole.** The hole shows on the shirt in every shot after the hit.
10. **Payoff.**
    - She pulls the bullet out off screen while we hold on her wincing face.
    - An insert shows the bullet held up between her fingertips, with her eyes on it.
    - Relief: a long exhale (her body sinks, head back), eyes close and reopen, and a small smile from two sculpted mouth-corner shape keys.
    - The end is held.

Logo: DA KRAS FILMS is on the box she holds (f1–74) and on the shelf box behind her in several store shots.

## Checks (on the package, every frame for contacts)
- `audit_hands`: HAND_IN_HAND 0, HAND_IN_BODY 0, HAND_IN_CLOTHES 0, HAND_IN_OTHER 0. WRIST_BEND 75–90° at f1180–1186. Through f1185 her right hand is off screen (the face shot); f1186 is the first insert frame, at 75°.
- `clip_scan`: one frame, f117: her own arm and body self-intersect as her right hand swings round in front of her. It is not visible in the f116 and f121 preview frames.
- `body_prop_cross`: the held bullet touches her thumb and index tips (17–22 points, f1186–1216). It reads as a pinch at every size.
- `qa_check` flags are all by design:
  - CAMJUMP: hard cuts.
  - EMPTY, FILL and ROLL: the macro set, which has no character, no horizon and the skin at the top of the frame.
  - PROPMOVE: the bullet, the shards and the falling box.

## Known issues
- The relief smile is small; this rig's face controls are limited, so the relief is carried mostly by the exhale and the eyes.
- No full-resolution frame was rendered here (studio rule).
