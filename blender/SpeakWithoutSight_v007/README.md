# SpeakWithoutSight_v007: the from-scratch rebuild (batch 1, film 19)

**Status: ON HOLD. FAILED the fresh review after 2 fix rounds and the director's final restage round; do not render.** The .blend is not pushed (the render check was not reached).
Watch `review/preview.mp4`; the faults with exact frames are in `review/CHECK_FINAL.md`.

One parlour, one girl and one teacher (one MPFB model each), one continuous camera, built to the v006 VO timing (frames 1-1645, `beats.json`).
Scripts: `scripts/01_build.py` (the set and characters), `02_animate.py` (seating, acting, contacts, skin ripples, pulse dots, camera, lights),
`03_package.py`. Rebuild: `01_build.py -- <polyhaven_dir> a.blend`, then `02_animate.py -- VO.mp3 b.blend`, then `03_package.py -- <pkg>`.
