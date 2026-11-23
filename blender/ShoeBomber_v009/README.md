# ShoeBomber_v009: rebuild against the director's v008 review (25 items, Nov 21)

- `ShoeBomber_v009_60fps.blend` is a self-contained scene with every texture packed. It's a plain git file at 60 fps, **frames 1–1469** (24.5 s), with the same VO, timing and frame range as v008.
  - The camera is `CAM_Film`. Shots are joined by **hard cuts**, as the director decided on Nov 23. There are no wipes and no black end frames.
  - The film is built straight on the VO beat frames in `beats.json`: 1, 157, 289, 373, 505, 625, 871, 979 and 1135. The VO is `ShoeBomber_v009_VO.mp3`.
- `review/preview.mp4` is the one preview, **rendered from this exact package file**, muxed with the VO. It shows every 5th frame at 270×480, Cycles 4 samples + denoise, played at 12 fps so it runs at real speed.
- `review/FIXES_v009.md` lists all 25 items with what changed. Check results are in `review/qa_v009.json` and `review/clip_scan_v009.json`.
- `ShoeBomber_v008` (the director's sync) is untouched.

Build order (the scripts are in `../ShoeBomber_v001/scripts/`):
1. `01_build_humans.py`, which adds AirPaxA and AirPaxB
2. `03_animate.py`
3. `03b_hand_pushout.py`
4. `03c_head_separate.py -- <out> 460 1068 3`, then the same with step 1
5. `04_fx_camera.py`, which runs `04_airpax.py`
6. `04b_contact_snap.py`
7. `03b_hand_pushout.py -- <out> 400 1068 3`
8. `04c_arm_pushout.py`
9. `03b_hand_pushout.py -- <out> 400 1068 3`
10. `pipeline/anim_look.py --no-sky`
11. `06_v003_look.py`
12. `06b_eye_fix.py`
13. **`07_retime_vo.py`**: maps source frames onto the VO frames piecewise and bakes every curve to per-frame constant keys
14. `05_shrink_textures.py`
15. `pipeline/package_for_farm.py`

The checks were run on the packaged file: `pipeline/qa_check.py`, `pipeline/clip_scan.py`, `cam_inside_check.py` and `head_check.py`.
