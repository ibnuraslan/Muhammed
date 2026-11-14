# StanleyCup_v007b: farm package (v007 with the v008-hold fixes; story-beat frames unchanged)

The full 25.5 s film at 1080×1920 and 60 fps on the same 1530-frame timeline as v007. The director's VO warp (v007 to v008) applies
to it unchanged. No render has been submitted.

- `StanleyCup_v007b_60fps.blend`: the self-contained scene, a normal Git file. Every texture is packed, and it opens in
  factory-startup Blender 5.2.2 with no add-ons.
- `review/StanleyCup_v007b_preview.mp4`: the moving preview of the whole film (every 5th frame, 270×480, Cycles 4 samples + denoise,
  12 fps, so it runs at real speed). `review/hold_fixes_before_after.jpg`: v007 and v007b at the flagged v008 times.
- `review/FIXES_v007b.md`: each fault and its fix, the director rules 1–4 pass (17:27), the check results, and why the remaining limb_check flags are left.
- `review/rules_check.py` + `review/rules_v007b.json`: per-frame check for rules 2–4 (arm across the other person, hand without its arm, camera brushing a body, lid or wall). The final build has 0 flags.
- Two hard cuts: f200 (outside → inside the room, so the camera never enters the wall) and f1401 (floor → two-shot).
- `review/qa_v007b.json`, `review/clip_v007b.json`, `review/limb_v007b.json`, `review/limb_points_v007b.json`, `audit.txt`, `hand_audit.txt`.
- `beats.json`, `SETTINGS.md`, `CREDITS.md`: as in v007; only the file name changes.

Source: `../StanleyCup_v001/scripts`. Changed since v007: `03d_acting.py` (acting, hands, cup), `03c_camera.py` (framings, cuts) and `05_anim_look_fixes.py` (exposure switches at the f200 cut).
The build order is unchanged (see `../StanleyCup_v007/README.md`). `pipeline/limb_check.py` (director, 9a0a692) is committed alongside.
