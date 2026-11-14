# StanleyCup_v007c: farm package (v007b plus the director's 5 review items; story-beat frames unchanged)

The full 25.5 s film at 1080×1920 and 60 fps, on the same 1530-frame timeline as v007 and v007b. No render has been submitted.

- `StanleyCup_v007c_60fps.blend`: a self-contained scene (66 MB, normal Git file). All textures are packed, and it opens in factory-startup Blender 5.2.2 with no add-ons.
- `review/StanleyCup_v007c_preview.mp4`: moving preview of the whole film (every 5th frame, 270×480, Cycles 4 samples + denoise, 12 fps).
- `review/FIXES_v007c.md`: the 5 items and their fixes, the blur check, and the check results.
- `review/director_items_before_after.jpg`: before/after for each item.
- Checks: `review/rules_check.py` + `rules_v007c.json`, `review/sharpness_check.py` + `sharpness_v007c.txt`, `qa_v007c.json`, `clip_v007c.json`, `limb_v007c.json`, `limb_points_v007c.json`, `audit.txt`, `hand_audit.txt`.
- Camera: one camera with five hard cuts, at f254, f455, f790, f1292 and f1401.
- The earlier passes are written up in `../StanleyCup_v007b/review/FIXES_v007b.md`.

Source: `../StanleyCup_v001/scripts`. Since v007b: `03c_camera.py` (framings, cuts, f-stops), `03b_fx.py` (x-ray off) and `05_anim_look_fixes.py` (exposure at the f254 cut).
