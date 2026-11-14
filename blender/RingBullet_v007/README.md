# RingBullet v007: farm package (VO-sync fixes)

| | |
|---|---|
| File | `RingBullet_v007_60fps.blend` (58 MB, packed, compressed; a normal git file, no LFS) |
| Format | 1080×1920, 60 fps, frames 1–1410 (23.5 s), Cycles CPU, 48 samples + OIDN |
| Camera | one camera (`Cam`) on one continuous move, no cuts, no markers |
| Output | `//render/RingBullet_v007_####.png` |
| Beats | `beats.json`, identical to v006 (every beat frame unchanged, for the VO re-sync) |
| Preview | `../RingBullet_v001/review/v007_preview/preview.mp4` (from `pipeline/preview.py` step 5, then `watch_pages.sh`), plus contact pages |
| Sources | `../RingBullet_v001/scripts/` (rebuild steps in `../RingBullet_v001/README.md`) |

## What changed from v006 (director notes after the VO sync, Nov 14)
1. **Bullet flight (~1.0–3.2 s):** the macro bullet ride is replaced by a chase about 42 cm behind and beside the bullet. The bullet is small and crisp, flying at his head height. He is sharp throughout: the animated look now uses f/22 everywhere.
2. **Ring approach (~5.7–8.2 s):** a medium shot of his face and the raised ring hand, then a single chase of about 1 s with the ring hand in front and his face behind it, all sharp.
3. **Dark frames (~7.8–8.1 s):** the dark side-profile key is replaced by a front-lit three-quarter view.
4. **After the impact (~11 s):** the camera pulls back so his face and hand read together.
5. **Looking at the dented ring (~18.5–19.5 s):** his elbow is bent, the hand is relaxed with curled fingers, and his face is in frame.
6. **Neck piece:** fragment B (slightly larger, with a hot-metal glint) visibly crosses in front of his chin and hits the side of his neck at f1003. Only after the hit does he flinch, with a head jerk and a wince, and his hand goes to his neck. No blood.

Also:
- the officer's resting hands are clear of his hips (newer `clip_scan`)
- the owner's lowered right hand is clear of his trousers (hand audit)

Notes and the check results are in `../RingBullet_v001/review/ACTING_notes.md` (v007 section).

Checks (reports in `../RingBullet_v001/review/*_v007.*`):
- `clip_scan`: **0 bad ranges**
- `qa_check`: BACKHEAD Robber at f1 only. That flag is intended, and the PROPMOVE flags on flying FX are intended and listed.
- `limb_check`: only the MPFB shoulder-joint points. A variant that skips only those 2 points reports 0.
- hand audit: 1 frame (f1271, same as v006)
- contact audit: 0
