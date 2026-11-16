# FridgeTenYears_v002: built to the voiceover

**B11, "Stuck behind a fridge for ten years".** This is a vertical 1080×1920 film at 60 fps, frames **1–1651**. The shots are cut on the words of `FridgeTenYears_v002_VO.mp3`, which runs 0–27.0 s. `beats.json` lists each shot's first and last frame and its words.

- **Built from:** `FridgeTenYears_v001/scripts` (`build_all.sh` + `03_anim.py -- timing.json`, then `bake_cam.py` and `pipeline/package_for_farm.py`). Each shot's action is authored at its VO length; no keyframes are time-stretched.
- **Preview:** `review/preview.mp4` is every 5th frame at 270×480 with the VO, rendered from this exact file. The contact pages are in `review/pages/`.
- **Checks on this file:**
  - clip_scan: 0 bad ranges.
  - body_prop_cross: 0 visible crossings, apart from the masked MPFB hip-helper cube (never rendered; see `review/CHECKS.md`).
  - qa_check and limb_check: every flag is explained in `review/CHECKS.md`.
- **Logo:** DA KRAS FILMS on the contractor's orange back, shot S16 (frames 1298–1354, flat-on).
