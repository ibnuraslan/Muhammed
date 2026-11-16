# Checks on the packed file (LincolnAssassination_v002b_60fps.blend)

The pipeline checkers read `cam = sc.camera` once at load. This film switches cameras with 17 timeline markers, so a single run
judges every frame through CAM_S01 (it reported 102 false EMPTY frames from f895 on). `scripts/per_shot_check.py` runs each
checker once per shot with that shot's camera; the shared pipeline is unchanged. body_prop_cross already follows `sc.camera`.

## limb_check (step 4): 0 visible faults except a known false positive
- ARMBODY "Soldier2/3 arm.R inside own torso (2 pts)" in S13 (f1025–1129) and S14B (f1279–1323): a constant 2 points at the
  shoulder end of the torch arm (the documented upperarm01 false positive within 4 cm of the shoulder). The torch arm is in
  front of the chest in every frame (see preview p05/p06).

## clip_scan (step 6, depth 2 cm): no bad ranges
- S06 f570 (gun hand into hip while lowering) and S08 f711 (hands into knees on landing) were real: fixed (low gun position
  moved out, landing hands wider), re-checked at step 2: S06 clean, S08 no bad range (max 10 points at f727, hand on knee).
- President "self" 9–13 points in S01/S03/S05: his hands resting on his thighs, hidden behind the armchair back (seen from behind).

## qa_check (step 6, beats.json)
- BACKHEAD President (S01): the story beat is the back of his head; by design (the president's face is never shown).
- BACKHEAD Gunman (S03): over-his-arm shot toward the top hat; his face is in S02 and S04 on either side.
- BACKHEAD Soldier2 (S14B): soldier in the foreground from the doorway; the gunman faces camera in the same frame.
- ATTACH "President_TopHat 10.8 cm off skin": a stovepipe hat stands above the hair; bone-parented, moves with the head.
- ATTACH "BoxColumnCap": the theatre box's column capitals (name match), not worn items.
- FAN "Gunman.R fingers fanned 37–45°": the index finger lies straight along the pistol frame (trigger finger) while the other
  fingers wrap the grip; this is the correct pistol grip.
- PROPMOVE Smoke0–2 (S05): smoke wisps after the shot (effect, not a held prop).
- EMPTY S12 f1022–1024 (3 frames): the horse's hindquarters are still in frame as it exits right; the rider has left
  the frame and the checker counts only MPFB characters.

## body_prop_cross (step 6): mean visible-crossing edges per checked frame
| Shot | Crossings | Reason |
|---|---|---|
| S01/S03/S05 | Pistol ~150, BoxChair ~37 | fingers closed on the grip; president pressed into the cushion behind the chair back (director accepted in P1) |
| S02, S06 | Pistol ~150 | grip contact (accepted) |
| S07 | BoxLedge 14 | shoe soles standing on the ledge |
| S01/S03/S05A/S05/S08/S10 | StageFloor 3–8 | actors' and gunman's soles on the boards |
| S11, S12 | Horse_body ~110 | rider's legs on the saddle flaps (accepted in P1) |
| S13, S14B | Torch ~42 | palm on the torch stick (accepted in P1) |
| S04, S09, S14, S15 | 0 | |
