# EscapeArtist v009b: director v007 review round: short shots with clean cuts (Connect34)

v009b = v008 plus the fixes from the director's v008 review (06:56 UTC, 13 items plus small ones). The camera is now short shots with clean cuts (the director allowed cuts), faces show on every beat, and the risky actions are re-staged simpler. DOF is at f/11. Story-beat start frames are unchanged (`beats.json` is identical), and no VO is added.

- `EscapeArtist_v009b_60fps.blend`: packed and compressed, plain git (no LFS), frames 0–3750 at 60 fps. See SETTINGS.md.
- `review/preview.mp4`: the moving preview of **this exact file** (270×480, every 5th frame, played at 12 fps = real speed, frame numbers burned in).
- `review/pages/`: contact pages of every preview frame (50 per page).
- `review/REVIEW_v009b.md`: the director's v007 list, its fix, the check results and the remaining known items.
- `review/qa_v009b.json`, `review/bpc_fence.json`, `review/bpc_bars.json`: outputs of `qa_check.py` and `body_prop_cross.py`.
- Rebuild: `../EscapeArtist_v001/scripts/`. The steps are:
  1. 01 humans
  2. 02 scene
  3. 03 animate
  4. `pipeline/anim_look.py --no-sky`
  5. 05 aimfix
  6. **06_fix_v009b**
  7. 04 package
