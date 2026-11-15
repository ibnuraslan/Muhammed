# ShoeBomber_v006e: v006d plus the director's v006d review (8 items, Nov 15)

- `ShoeBomber_v006e_60fps.blend` is a self-contained scene: every texture is packed, and it's a plain git file at 60 fps, **frames 1–1446** (24.1 s).
  - The camera is `CAM_Film`. Shots are joined by **clean hard cuts**; there are no wipes, no black frames and no grey frames.
  - Beat frames are in `beats.json`. Beats 1–7 haven't moved (1, 199, 373, 481, 655, 769, 1069). Beat 8 (sky) is now 1159 and beat 9 (airport) is now 1219.
- `review/ShoeBomber_v006e_preview.mp4` is the moving preview, **rendered from this exact package file**: every 5th frame, 270×480, Cycles 4 samples + denoise, at 12 fps, so it plays at real speed.
- `review/FIXES_v006e.md` lists each item with its fix, the check results and the four-rule confirmation.

Build order (the scripts are in `../ShoeBomber_v001/scripts/`):
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
11. **`07_retime.py`**: shortens the sky to 1 s and brings the airport in after it, baking every curve after 1158 to per-frame constant keys.
12. `05_shrink_textures.py`
13. `pipeline/package_for_farm.py`

Checks: `cam_speed_check.py`, `cam_turn_check.py`, `cam_inside_check.py`, `head_check.py`, `pipeline/qa_check.py`, `pipeline/limb_check.py` and `pipeline/clip_scan.py`. All of them are run on the packaged file.
