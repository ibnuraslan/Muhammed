# B26 TenDimes v002b (Phase 2 fix round 1, built to the client VO)

Vertical explainer, 1080×1920, 60 fps, Cycles, frames 1–1868. Hard cuts between 20 shots, timed to the words of
`TenDimes_v002b_VO.mp3` (transcribed with `pipeline/transcribe.py`; `review/VO.words.json`).

- `TenDimes_v002b_60fps.blend`: the package (textures and VO packed). See SETTINGS.md.
- `beats.json`: shot → start frame → VO words. `timing.json`: shot cut-in / cut-out frames used by the build.
- `review/preview.mp4`: moving preview with the VO (every 5th frame, 270×480, Cycles 4 spp, from this exact package).
- `review/pages/`: contact pages of every preview frame. `review/CHECKS.md`: clip_scan, qa_check, limb_check, body_prop_cross.
- `PLAN.md`: shots and staging. CREDITS.md: CC-BY models (credit in the description).

Timing: every shot is its 1× clip trimmed to its beat (no time-stretch). S08 and S22 from Phase 1 are not used
(no room in the VO). S18 (on stage, "for the rest of his life") now plays before S17 (dimes, "he carried ten dimes
everywhere"), following the VO's wording.

## Rebuild
```
B=/opt/blender/blender-5.2.2-linux-x64/blender
$B -b --factory-startup --python scripts/01_chars.py
$B -b build/chars.blend --python scripts/02_sets.py
VO=TenDimes_v002b_VO.mp3 $B -b build/sets.blend --python scripts/03_anim.py -- timing.json
$B -b build/anim.blend --python ../pipeline/anim_look.py -- build/look.blend
$B -b build/look.blend --python scripts/04_shrink.py -- build/small.blend      # textures -> JPEG (alpha cards stay PNG)
$B -b build/small.blend --python ../pipeline/package_for_farm.py -- TenDimes_v002b_60fps.blend
```
