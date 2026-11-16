# B05 LoveCanal: Phase 1 checkpoint notes

- Still sheet: `review/P1_still_sheet_3frames_540.jpg`: first, middle and last frame of all 22 shots at 540×960 (Cycles 8 spp, after the anim_look pass), reference timing. The older 1-frame sheet `P1_still_sheet_540.jpg` is superseded.
- Contact check: `review/body_prop_cross.json` (step 3, every frame range), summary in `review/body_prop_cross_summary.txt`.
- Build: `scripts/01_chars.py` → `02_sets.py` (+`02b_sets.py`) → `03_anim.py` (+`03a…03d`). The whole film rebuilds in about 4 min. Phase 2 passes a timing JSON of VO seconds per shot; actions are keyed at 1× from each shot start and run 30% past the planned length.
- Every shot's first and last frames were checked at 216 px (stills not committed).

## Deviations
- **Characters:** the MakeHuman CC0 asset host was down (HTTP 502 all session), so the 6 MPFB characters are appended from earlier studio packages (EscapeArtist, StanleyCup, BellyFat). They are stripped of animation and film-only constraints, re-dressed in new colours, and given the eye fix, elbow/wrist limits and hand limits.
- **Box truck:** the first truck model had foreign lettering in its texture, so it was replaced with a clean white one (LCT 3000, CC-BY).
- **S19:** the truck's back doors are modelled closed, so Dad2 carries his box toward the truck instead of lifting it in.
- **S20:** Dad2 is shown in profile, not from behind as in the reference, so his face reads.

## Director notes applied (Nov 15–16)
- Logo kept on the truck's back doors (S19, S21).
- Dense drum heap: one throwaway drop sim settles 504 drums into a mound in the pit. Each drum is then keyed flying in on an arc from the truck side into its slot, lowest first. Nothing passes through the heap, nothing comes near a lens, and all drums land before S14. In S14 the dozer works at the heap, and drums are buried as the dirt wave reaches them.
- S2: her hand stays about 6 cm in front of her nose.
- S9/S10: the worker wears blue-grey coveralls, dark boots, work gloves and a yellow hard hat. His face shows, and his palms rest on top of the rolling drum.
- S6/S17: the brown house's windows were my curtain-glass material rendering black. It now shows curtains behind glass that reflects the sky.
- S5: push-in on Father (coughing into his hand) at the counter, with the kitchen units, fridge, oven and a new back window behind. The son stands at the counter end, Mother is at the left with her hand to her chest.
- S22: medium two-shot from above the bed. The father's face is on the pillow and the son stands at the bedside (moved from the armchair, which kept cutting into his legs), his palm on his father's hand on his chest. The blanket is draped from the body shape (arms excluded) and is a darker blue with folds.
- anim_look pass applied (AgX Punchy, `--no-sky` to keep the HDRI clouds).
- Expressions: oculi offsets below -0.002 bared the eye whites and lids past -12 closed the eyes, so `face()` clamps to a gentle squint (blinks unaffected).

## Remaining body/prop contacts (frames on the reference timing)
- S1 f1–118: the boy's thighs touch the saddle and his fingers wrap the grips. This is normal riding contact, and the rear camera hides both behind his body.
- S19 f2161–2218: the flat palms hold the box sides and the fingertips press 2–5 mm into the cardboard. In close-up it reads as holding.
- S9 f1057–1078: right fingertips touch the drum top as it rolls under the palm (a few mm).
- S4 f460–478: the thumb base touches the glass for 5 sampled frames during the lowering.
- All other shots: 0.

## Build bugs found and fixed
- A one-off rebuild crash meant one crossing check ran on a stale file; it was re-run.
- Hand targets computed while a rig was parked off-set leaked into the last frame of a shot (the S3 lid vanished). Rigs now stay placed through their overrun, and actions end at the cut when the next shot reuses the character.

## Director round 2 (Nov 16) applied
1. S19: the box stays in his hands to the cut. Every stepped keying loop now lands its last key ON the cut frame (`frs()`), so nothing interpolates toward the next shot.
2. S5: lower camera at the front-right of the island. Father, Mother and son are whole in frame.
3. S4: the glass stays in his hand at chest height to the cut.
4. Tan house: the black gable and porch were duplicate coincident faces shadowing each other. Duplicates are removed, normals face outward, and it has painted tan lap siding (procedural, no UVs).
5. S7: the cut-away blocks are 18 m deep and the camera is framed lower, so there's no empty grey under them.
6. S10: the camera pushes in. The worker walks toward it, stops, turns and waves the right-hand truck back.
7. S12: heap drums that sank into the ground (81) or overlapped another drum (65) are left out, leaving 358 drums with no sliced wedges.
8. S22: camera at the son's eye line. The son stands by his father's chest (above the blanket edge), and both faces read with the hand-on-hand kept.
Crossing check on this build (`body_prop_cross.json`, S5 and S22 re-checked after their last camera tweak: 0) has only the accepted S1, S4, S9 and S19 contacts.
