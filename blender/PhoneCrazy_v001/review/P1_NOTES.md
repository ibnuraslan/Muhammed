# B18 PhoneCrazy: Phase 1 checkpoint notes

- Still sheet: `review/P1_still_sheet_3frames_540.jpg`: first, middle and last frame of all 22 shots at 540×960, Cycles 8 spp + OIDN, after the anim_look pass, reference timing (frames in `PLAN.md` seconds: frame = 1 + round(s × 60), END 2311).
- Contact check: `review/body_prop_cross.json`: Case + Phone, every 3rd frame of the whole film: **0 crossings** (nobody touches the phone or the case).
- Build: `scripts/build_all.sh` (00_screens → 01_chars → 02_sets → 03_anim + 03a_shots → anim_look --no-sky → 04_finish), ~3 min. Phase 2 passes `timing.json`.
- Every shot's first/mid/last frame was looked at on the sheet (and 270×480 iterations before it).

## Staging choices
- Phone never held: it lies face-up on an orange site case all film. Avoids every grip risk and shows "no one touching it" literally. The reference shows it held in a hand; a held variant is possible if the director wants it, at grip risk.
- Screens: drawn pictures only (no text, digits, app or brand logos). 911 = keypad keys in the 9-1-1 positions lighting, then a call screen.
- No "45,000 gallons" text: the draining pit carries it.
- Logo: white DA KRAS FILMS on the case front (S5 ≈ 20% frame width, flat to camera, 2 s; also S9).

## Known issues / unsure
- S11/S12: the whirlpool dip is a shallow cone in the water; from above it can read as a slight dome. I'd strengthen it with a darker centre in Phase 2 if the director agrees.
- S17: Foreman's fringe shows under the hat brim and touches one eyebrow at the last frame; eyes are readable. Will part it if flagged.
- S22: the crew is small (high wide across the pit, as in the reference's last shot); the drain hole sits at the lower left.
- S10 crew seen from behind (they face the pit); they are not the subject of that shot.
- S16 cross-section shows the excavator but no workers on top.
- Excavator dig cycle is continuous (4.4 s) so any VO cut lands mid-action; bucket bites into the pit wall in S2 and S15 at the reference timing.
