# EscapeArtist v007: moving-preview fix round (Connect34)

v007 = v006b plus the fixes from watching v006b as a **moving preview** (`pipeline/preview.py`, every 5th frame). This round followed the director's 2026-11-14 brief. Story-beat start frames are unchanged (`beats.json` is identical), and no VO is added.

- `EscapeArtist_v007_60fps.blend`: packed and compressed, plain git (no LFS), frames 0–3750 at 60 fps. See SETTINGS.md.
- `review/preview.mp4`: the moving preview of **this exact file** (270×480, every 5th frame, played at 12 fps = real speed, frame numbers burned in).
- `review/pages/`: contact pages of every preview frame (50 per page).
- `review/REVIEW_v007.md`: every fault found in the v006b preview, its fix, the check results and the remaining known items.
- `review/qa_v007.json`, `review/bpc_fence.json`, `review/bpc_bars.json`: outputs of `qa_check.py` and `body_prop_cross.py`.
- Rebuild: `../EscapeArtist_v001/scripts/`. The steps are:
  1. 01 humans
  2. 02 scene
  3. 03 animate
  4. `pipeline/anim_look.py --no-sky`
  5. 05 aimfix
  6. **06_fix_v007**
  7. 04 package
