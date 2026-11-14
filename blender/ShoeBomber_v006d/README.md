# ShoeBomber_v006d: v006c plus the director's preview faults (moving-preview review, Nov 14)

- `ShoeBomber_v006d_60fps.blend`: a self-contained scene with every texture packed. It's a plain git file, 60 fps, frames 1–1620. The beat frames haven't changed (`beats.json`). There's one continuous camera, and the only jumps are inside the covered wipes.
- `review/ShoeBomber_v006d_preview.mp4` is the moving preview: every 5th frame, 270×480, Cycles 4 samples + denoise, played at 12 fps, so it runs at real speed. `review/AFTER_v006d_0p5s.jpg` is the half-second sheet.
- `review/FIXES_v006d.md` has the fault-by-fault fix list, the check results and the four-rule confirmation.

Build order (scripts are in `../ShoeBomber_v001/scripts/`):
1. `03_animate.py`
2. `03b_hand_pushout.py`
3. `03c_head_separate.py -- <out> 460 1068 3`, then the same with step 1
4. `04_fx_camera.py`
5. `04b_contact_snap.py`
6. `03b_hand_pushout.py -- <out> 400 1068 3`
7. `04c_arm_pushout.py`
8. `03b_hand_pushout.py -- <out> 400 1068 3`
9. `pipeline/anim_look.py --no-sky`
10. `06_v003_look.py`
11. `05_shrink_textures.py`
12. `pipeline/package_for_farm.py`

Checks: `cam_speed_check.py`, `cam_turn_check.py`, `cam_inside_check.py`, `head_check.py`, `pipeline/qa_check.py`, `pipeline/limb_check.py`, `pipeline/clip_scan.py`.
