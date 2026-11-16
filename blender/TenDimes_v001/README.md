# B26 TenDimes v001 (Phase 1 checkpoint)

Phase 1 build (no VO yet): characters, five sets, 22 shots as 1x clips (~30% longer than the expected beats), one camera per shot.
See `PLAN.md` for the shot table, staging choices and open questions. Not a delivery package.

## Rebuild (Blender 5.2.2, headless, CPU)
```
B=/opt/blender/blender-5.2.2-linux-x64/blender
$B -b --factory-startup --python scripts/01_chars.py          # -> build/chars.blend
$B -b build/chars.blend --python scripts/02_sets.py           # -> build/sets.blend
$B -b build/sets.blend --python scripts/03_anim.py [-- timing.json]   # -> build/anim.blend
$B -b build/anim.blend --python ../pipeline/anim_look.py -- build/look.blend
$B -b build/look.blend --python scripts/shotstills.py -- stills 540 8   # first/mid/last per shot
python3 scripts/sheet.py stills review/P1_sheet.jpg
```
Assets (CC-BY GLBs, Poly Haven) are fetched with `pipeline/find_models.py` / `pipeline/fetch_polyhaven.py` (uids in CREDITS.md); `scripts/common.py` holds the paths.

## Review
- `review/P1_sheet_p*.jpg`: 3 frames per shot (first, middle, last), 540x960, Cycles 8 samples.
- `review/BODY_PROP_CROSS.md`: body_prop_cross on every held/touched prop and set piece.
