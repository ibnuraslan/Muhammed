# StanleyCup_v007d: farm package (v007c plus the director's b7569ee review items; story-beat frames unchanged)

The full 25.5 s film at 1080×1920 and 60 fps, on the same 1530-frame timeline as v007. No render has been submitted.

- `StanleyCup_v007d_60fps.blend`: a self-contained scene (65 MB, normal Git file). All textures are packed, and it opens in factory-startup Blender 5.2.2 with no add-ons.
- `review/StanleyCup_v007d_preview.mp4`: moving preview of the whole film (every 5th frame, 270×480, Cycles 4 samples + denoise, 12 fps).
- `review/FIXES_v007d.md`: the 6 items and their fixes, the blur check, and the check results.
- `review/director_items_before_after.jpg`: before/after for each item.
- Checks: `review/rules_check.py` + `rules_v007d.json`, `review/sharpness_check.py` + `sharpness_v007d.txt`, `qa_v007d.json`, `clip_v007d.json`, `limb_v007d.json`, `limb_points_v007d.json`, `audit.txt`, `hand_audit.txt`.
- Camera: one camera with eleven hard cuts (see SETTINGS.md).
- Earlier passes are written up in `../StanleyCup_v007c/review/FIXES_v007c.md` and `../StanleyCup_v007b/review/FIXES_v007b.md`.

Source: `../StanleyCup_v001/scripts`. Since v007c: `03c_camera.py` (framings and cuts) and `05_anim_look_fixes.py` (exposure at the f150 cut).
