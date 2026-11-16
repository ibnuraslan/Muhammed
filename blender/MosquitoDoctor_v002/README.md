# B22 MosquitoDoctor v002 — built to the client VO

Vertical 1080×1920, 60 fps, Cycles, 35.2 s (frames 1–2113), 25 hard-cut shots timed to the VO words (`beats.json`).
A mosquito bites a sick boy → a doctor traps it in a glass vial and lets it bite his own hand → fever, yellow eyes, sick over a
basin (stain only) → organ cut-away → death off-screen (empty desk) → colleagues with his notes and the vial → a ward under
mosquito nets.

- `MosquitoDoctor_v002_60fps.blend` — the farm package (see SETTINGS.md).
- `MosquitoDoctor_v002_VO.mp3` + `.words.json` — the client VO and its word timestamps (faster-whisper).
- `beats.json` — every shot's VO start/end frame, the master-timeline frame it is cut from, and its first words.
- `review/preview.mp4` — every 5th frame at 270×480 with the VO, rendered from this exact package.
- `review/checks_summary.txt` — clip_scan, qa_check, limb_check and body_prop_cross on this package.
- Logo frames: ~1919–1990 (the crate in the ward, whole and flat to camera for ~1.2 s).

Built from `../MosquitoDoctor_v001/scripts` (`build_all.sh`, then `05_edit.py` cuts the 1× master timeline to the VO
frames with no time-stretch, `06_bake_cam.py` bakes the shot cameras into one camera, `pipeline/package_for_farm.py`).
DA KRAS FILMS logo: one placement, the supply crate in the ward (frames ~1919–1980).
