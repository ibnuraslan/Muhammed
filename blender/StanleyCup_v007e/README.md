# StanleyCup_v007e: farm package (v007d plus the director's v007d review; beats unchanged)

The full 25.5 s film at 1080×1920 and 60 fps (1530 frames). No render has been submitted.
- `StanleyCup_v007e_60fps.blend`: a self-contained scene (65 MB). All textures are packed, and it opens in factory-startup Blender 5.2.2 with no add-ons.
- `review/StanleyCup_v007e_preview.mp4`: the preview, rendered from this exact build.
- `review/FIXES_v007e.md`: the items and the checks.
- Checks: `review/rules_check.py`, `review/sharpness_check.py`, and their outputs, `qa_v007e.json`, `clip_v007e.json`, `limb_v007e.json`, `limb_points_v007e.json`, `audit.txt`, `hand_audit.txt`.
- Camera: one camera with 13 hard cuts (see SETTINGS.md).
- Earlier passes: `../StanleyCup_v007d`, `../StanleyCup_v007c` and `../StanleyCup_v007b` (each has `review/FIXES_*.md`).

Source: `../StanleyCup_v001/scripts` (since v007d, only `03c_camera.py` changed).
