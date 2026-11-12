# EscapeArtist — Connect34

A vertical true-story short (1080×1920, 60 fps, 62.5 s), one continuous camera.

## Files
- `PLAN.md`: beat table, camera plan, assets.
- `beats.json`: beat start frames for `pipeline/retime_to_vo.py`. Built to the brief's target times; no VO has been supplied yet.
- `scripts/`: rebuild from scratch, in order:
  1. `01_build_humans.py`: 10 MPFB2 characters (CC0 MakeHuman assets).
  2. `02_build_scene.py <assets_dir> <out>`: cell block (corridor, 5 cells, barred windows, brick exterior), yard with chain-link and razor-wire fence, memory house (workshop, armchair, phone, police-light window) and court. The assets dir holds `ph/` (Poly Haven via `fetch_polyhaven.py`) and `models/` (Sketchfab via `find_models.py`; ids in `assets/sketchfab_credits.json`).
  3. `03_animate.py`: all 15 beats, props, lights and the camera spline; writes `beats.json`.
  4. `audit.py`: hover, sink, hand/head penetration and camera-inside checks.
  5. `04_package.py <out> <tmp>`: 1K JPEG textures, purge, then `pipeline/package_for_farm.py`.
- `stills/`: review sheets (B 1 s; C 0.2 s per beat).
- `CREDITS.md`, `SETTINGS.md`.

## Sets reused
| Set | Beats |
|---|---|
| Hero cell (bars door, solitary steel panel, barred window, tally wall) | 2, 3, 9, 10, 12, 13, 15 |
| Corridor (+ gate) | 1, 3, 7, 11 |
| Yard and fence | 8, 14, 15 |
| Memory house | 4, 5, 6 |
| Court | 7 |
