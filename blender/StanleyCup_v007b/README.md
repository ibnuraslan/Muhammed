# StanleyCup_v007b: farm package (v007 with the v008-hold fixes; story-beat frames unchanged)

The full 25.5 s film at 1080×1920 and 60 fps on the same 1530-frame timeline as v007. The director's VO warp (v007 to v008) applies
to it unchanged. No render has been submitted.

- `StanleyCup_v007b_60fps.blend`: the self-contained scene, a normal Git file. Every texture is packed, and it opens in
  factory-startup Blender 5.2.2 with no add-ons.
- `review/StanleyCup_v007b_preview.mp4`: the moving preview of the whole film (every 5th frame, 270×480, Cycles 4 samples + denoise,
  12 fps, so it runs at real speed). `review/hold_fixes_before_after.jpg`: v007 and v007b at the flagged v008 times.
- `review/FIXES_v007b.md`: each fault and its fix, the check results, and why the remaining limb_check flags are left.
- `review/qa_v007b.json`, `review/clip_v007b.json`, `review/limb_v007b.json`, `review/limb_points_v007b.json`, `audit.txt`, `hand_audit.txt`.
- `beats.json`, `SETTINGS.md`, `CREDITS.md`: as in v007; only the file name changes.

Source: `../StanleyCup_v001/scripts`. Only `03d_acting.py` (acting, hands, cup) and `03c_camera.py` (framings) changed since v007.
The build order is unchanged (see `../StanleyCup_v007/README.md`). `pipeline/limb_check.py` (director, 9a0a692) is committed alongside.
