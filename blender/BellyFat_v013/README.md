# BellyFat_v013

This build fixes the director's 12-point review of v012. v010–v012 are left untouched. It keeps the same VO, timing and frame range: **frames 1–1273 at 60 fps**, with the VO (21.0 s) packed.

## Files
- `BellyFat_v013_60fps.blend`: the render file, 74 MB, everything packed. `SETTINGS.md` is the render sheet and shot table.
- `review/preview.mp4`: the one small preview, rendered with `pipeline/preview.py` from the exact package (every 5th frame, 270×480, 4 samples, with the VO). `review/pages/` holds the contact pages; I watched every page.
- `review/*.json`, `review/audit_hands.txt`: the check results for the package.
- `beats.json`, `CREDITS.md` (CC-BY intestine credit), `scripts/` (full rebuild).

## The 12 points
1. **Window (0–0.8 s).** A long lens shoots down the aisle from inside the shop. The shop window shatters behind her (a crack star across the glass, shards), and the street outside reads as daylit facades. She is in frame and startles: her head snaps up and her arms jolt. Held 0.8 s.
2. **Box and arm.** The box sits on her left palm, and the hand-pose preset curls her fingers round its edge. Her hand rides with her chest frame by frame, so the box never cuts into her forearm. Her free right arm hangs relaxed with the elbow bent.
3. **Copper sphere.** Gone. The bullet is never shown in the store, only its impact on the shirt (dimple, ripple, hole).
4. **Hit reaction.** She flinches and staggers a step back; her left foot moves. The box stays in her grip through the hit. The basket stays put. The background shoppers idle (breathing, weight, head turns), turn to the noise, then watch her.
5. **Framing.** The hit shot holds her face and belly together. There is no crotch-centred frame and no box in the lens.
6. **Nose-first bullet.** The cross-section bullet has a pointed ogive nose and a flat base. It travels fast, nose-first, into the shirt and skin against a dark tissue background.
7. **Story.** The bullet slows and **stops inside the fat** at about 2.4 units (the muscle starts at 4.5), with the fat compressing and rebounding around it. The cross-section lasts 4.0 s (181–420).
8. **No jump cuts in the cross-section.** It is one continuous push that follows the bullet in and eases to a stop.
9. **Line artefacts.** The capillary curves and the blue backdrop are removed, and the background is dark tissue.
10. **Hands and expression (16.8–19.1 s).** Both hands rest on her shirt: placed with `place_hand`, settled out of the cloth, then given a few mm of air. She has a pained expression (lowered upper lids, raised lower lids, mouth corners down), blinks every 1–1.5 s and breathes heavily, with no static hold.
11. **Wrist and fingers (19.5–20.3 s).** There is no palm-check pose. Her hand rests on her belly with the fingers together (presets at spread 0), and the wrist checks report 0 bends.
12. **Ending.** She straightens and breathes out, her mouth corners lift and her eyes soften, she looks at the helper and nods. The catchlight is on the camera (8 W, glossy only). The end frame holds for the last 0.4 s.

Logo: DA KRAS FILMS is on the box she holds (S2/S3, about 2 s) and on a box on the shelf behind her (S2, S3, R2, P; over 6 s), flat to camera, at about 20 % of frame width.

## Checks (on the package)
- `clip_scan`: no bad ranges.
- `audit_hands`: 0 in every category (hand-in-hand, body, clothes, other, wrist bend).
- `body_prop_cross`: only 1-point grazes between her left forearm and the held box.
- `qa_check`: every flag is expected:
  - CAMJUMP: the 6 hard cuts.
  - EMPTY, FILL and ROLL: the cross-section, which has no character and no horizon.
  - PROPMOVE: the box carried in her hand and the glass shards.
  - BACKHEAD: the opening, where she faces the window.
- `limb_check` ARMBODY: the shoulder-joint false positive on this rig.

## Known issues
- In the opening shot she is seen from behind, because she faces the window as it shatters. Her face is seen from the next shot on.
- The relief smile is subtle; this rig has no full smile controls.
- No full-resolution frame was rendered here, per the studio rule.
