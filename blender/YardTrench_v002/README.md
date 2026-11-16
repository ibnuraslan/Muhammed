# YardTrench_v002: "Turning your yard into a war trench" (B37)

A vertical 1080×1920, 60 fps Cycles short, built straight to the client's VO (`YardTrench_v002_VO.mp3`, 30.2 s).

## Contents
- `YardTrench_v002_60fps.blend`: the farm package (see SETTINGS.md).
- `YardTrench_v002_VO.mp3` and `YardTrench_v002_VO.words.json` (faster-whisper word timestamps).
- `beats.json`: shot starts at the VO word frames (`1 + round(seconds × 60)`).
- `timing_vo.json`: the shot start seconds fed to `scripts/03_anim.py`.
- `review/preview.mp4`: every 5th frame at 270×480 with the VO, rendered from the exact package.
- `review/`: check reports (qa_check, clip_scan, limb_check, body_prop_cross) and `CHECKS.md` with the explanation of every remaining flag.
- `scripts/`: the full build (`bash scripts/build.sh` inside this folder, about 1 min). Assets are fetched by `pipeline/find_models.py` / `fetch_polyhaven.py` into `assets_src/` (not in git; the uids are in `CREDITS.md`).

## Story (22 shots, hard cuts)
1. A boy walks the same line across the lawn every day. His feet crush the grass, and a cut-away block shows the soil packing down.
2. The strip goes bare, then dries hard and cracked (time-lapse).
3. Rain can't soak in. Puddles join and flow along the groove.
4. Storm after storm deepens it into a groove.
5. Decades later, the grown man walks it as it becomes a trench. Sandbags and a helmet give the playful "war trench" peek, and the last shot shows the depth: walls above his head.

There is no on-screen text. The DA KRAS FILMS logo appears once, printed on the man's white shirt (S17, S21).
