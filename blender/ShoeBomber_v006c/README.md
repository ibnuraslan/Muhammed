# ShoeBomber_v006c: v006 with ONE continuous camera

- `ShoeBomber_v006c_60fps.blend`: a self-contained scene with every texture packed. It's a normal git file (no LFS), 60 fps, frames 1–1620. The beat frames haven't changed (see `beats.json`), and there's no VO.
- `review/ACTING_notes.md` lists the problems found in v004, with frames, plus the v006 fix list, the clip_scan notes and the QA exceptions.
- `review/BEFORE_v004_0p5s.jpg` and `review/AFTER_v006_0p5s.jpg` are the half-second sheets (270×480, 8 samples).
- `review/hand_closeups.jpg` holds a 270×480 close-up of every hand contact.
- `review/clip_scan_v006.json` is the output of `pipeline/clip_scan.py`. `review/qa_v006.json` is the output of `pipeline/qa_check.py`.

The scripts are in `../ShoeBomber_v001/scripts/`. Build order:
1. `03_animate.py`: animation. Fingers come from `pipeline/hand_poses.py`.
2. `03b_hand_pushout.py`: the hand/body contact pass.
3. `04_fx_camera.py`: the camera, one continuous move; the `cam_search.py` framings are key poses joined by 20–40 f moves over the seat backs
4. `04b_contact_snap.py`: hand-to-prop contact
5. `03b_hand_pushout.py -- <out> 400 1068 3`: the body push-out, run again after the snap
6. `pipeline/anim_look.py -- --no-sky`
7. `06_v003_look.py`
8. `05_shrink_textures.py`
9. `pipeline/package_for_farm.py`

