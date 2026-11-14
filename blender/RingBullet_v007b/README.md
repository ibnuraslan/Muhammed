# RingBullet v007b: farm package (director fixes on v007)

| | |
|---|---|
| File | `RingBullet_v007b_60fps.blend` (58 MB, packed, compressed; a normal git file, no LFS) |
| Format | 1080×1920, 60 fps, frames 1–1410 (23.5 s), Cycles CPU, 48 samples + OIDN |
| Camera | one camera (`Cam`) on one continuous move, no cuts, no markers |
| Output | `//render/RingBullet_v007b_####.png` |
| Beats | `beats.json`, identical to v006 and v007 |
| Preview | `../RingBullet_v001/review/v007b_preview/preview.mp4` (`pipeline/preview.py` step 5, then `watch_pages.sh`), plus contact pages |

## What changed from v007 (director review of 63e021c). Nothing else was touched.
1. **No black mouth.** Each human has a small warm fill light inside the mouth. It is parented to the head bone, invisible to the camera, at 0.012 W. The tongue is now a lit red-brown and the teeth ivory, so open mouths read as a red-pink interior with the teeth showing, not a black hole. Checked at 540×960 at f300 and f1006: `../RingBullet_v001/review/v007b_mouth_f300_f1006_540x960.jpg`.
2. **Impact macro f516–546.** The impact camera key is pulled back from 10 cm to 18 cm (lens 60 → 50 mm), so the ring, the bullet and the fingertip read together through the impact. The fingertip never fills the frame: `../RingBullet_v001/review/v007b_impact_f506_f571.jpg`.

Everything else is as v007: see `../RingBullet_v007/README.md` and `../RingBullet_v001/review/ACTING_notes.md`.
