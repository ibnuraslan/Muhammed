# EscapeArtist v004: acting pass (Connect34)

v006b = v006 with AimFix as Track To (world up, level horizon) and a runner aim at 30 s from `blender/briefs/ACTING_FIX_04-10.md`. Story-beat start frames are unchanged (`beats.json` is identical to v003), ready for the director's VO re-sync. No VO is added.

- `EscapeArtist_v006b_60fps.blend`: packed, 58 MB, normal git (no LFS); opens in factory Blender with 0 unpacked images, one camera, frames 0–3750. See SETTINGS.md.
- `review/ACTING_notes.md`: every problem found on the v003 half-second sheet, and the fix for each.
- `review/before_v003_half.jpg` / `review/after_v004_half.jpg`: half-second sheets (every 30 frames, 270×480, 8 samples).
- `review/hand_closeups_v004*.jpg`: 270×480 close-ups of every hand contact.
- `review/clip_scan_v004.json`: director `clip_scan.py`, run per cast window: 0 bad ranges.
- Rebuild: `../EscapeArtist_v001/scripts/` (01 humans → 02 scene → 03 animate → `pipeline/anim_look.py --no-sky` → 04 package).
