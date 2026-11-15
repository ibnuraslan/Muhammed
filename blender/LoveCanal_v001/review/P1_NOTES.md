# B05 LoveCanal: Phase 1 checkpoint notes

- Still sheet: `review/P1_still_sheet_540.jpg`: one 540×960 frame per shot (Cycles 8 spp, 60% into each shot), reference timing.
- Build: `scripts/01_chars.py` → `02_sets.py` (+`02b_sets.py`) → `03_anim.py` (+`03a…03d`). The whole film rebuilds in about 4 min. Phase 2 passes a timing JSON of VO seconds per shot; actions are keyed at 1× from each shot start and run 30% past the planned length.
- Every shot's first and last frames were checked at 216 px (stills not committed).

## Deviations
- **Characters:** the MakeHuman CC0 asset host was down (HTTP 502 all session), so the 6 MPFB characters are appended from earlier studio packages (EscapeArtist, StanleyCup, BellyFat). They are stripped of animation and film-only constraints, re-dressed in new colours, and given the eye fix, elbow/wrist limits and hand limits.
- **Box truck:** the first truck model had foreign lettering in its texture, so it was replaced with a clean white one (LCT 3000, CC-BY).
- **S19:** the truck's back doors are modelled closed, so Dad2 carries his box toward the truck instead of lifting it in.
- **S20:** Dad2 is shown in profile, not from behind as in the reference, so his face reads.

## Known issues I'll fix before Phase 2 (frame numbers on the reference timing)
1. S8 (f841–1020): the cave walls read as crumpled green paper. Plan: smoother rock and darker walls, keeping the green glow.
2. S12–S13 (f1261–1500): the drums scatter more than they pile; one falling drum passes close to the S13 lens (top-left, ~f1452). Plan: tighter spawn and a camera offset.
3. S14 (f1501–1620): the dirt wave is a grey lump and there is a dark edge on the fill. Plan: brown lumpy dirt and a sloped fill edge.
4. S20 (f2221–2340): Dad2's right hand drifts out toward the truck cab. Plan: hands back at his sides.
5. S22 (f2401–2610): the blanket shows lumps and darker patches over the legs. Plan: smoother drape.
6. No `anim_look.py` pass yet (AgX Punchy is set). The leaf tint is applied.

## Questions for the director
- **Logo:** DA KRAS FILMS (dark) is on the truck's back doors in S19 (f2161–2220) and stays readable small in S21. The reference has its own logo on the same truck. Is a moving truck during the evacuation beat acceptable, or should it move to the box Dad2 carries, or be dropped?
- **Drum pile:** is a top-down "drums tumbling into the pit" look fine for S11–S12, or do you want a dense heap like reference seconds 21–24?
