# SodaMouse_v002: checks on the packed file `SodaMouse_v002_60fps.blend`

| Check | Result |
|---|---|
| `body_prop_cross` (props: Beaker, SodaCan, Spatula, Plate), **step 1, frames 1–1702** | **0 crossings** |
| `clip_scan` (step 6) | 1 frame: **571**, Scientist self-intersection (S07, his right arm rising behind the table edge). Not visible on camera (checked at 540×960, frames 565/571/577). |
| `limb_check` (step 2) | ARMBODY "2 pts": known shoulder false positives (upperarm points 0–2). S01 frames 23–77, SodaMan arm.R 4–6 pts: the drinking arm's upper arm at the armpit, on the far side of his body from the camera; not visible. |
| `qa_check` (step 6) | **EMPTY** 79–163 (S02 can macro), 343–397 (S06 mouse close-up), 949–1195 (S11/S12 jelly): prop-only shots of the thing the VO names, by design. **PROPMOVE** at cut frames 79, 169, 277, 949, 1435: props reset at hard cuts. **FAN** 301–337 and 595–643: the index-finger "point" pose (S05, S07), visually clean. **CAMJUMP** at the 18 marker cuts: intended hard cuts. |

**Tool note.** `qa_check.py`, `limb_check.py` and `clip_scan.py` read `cam = sc.camera` once at load. In a film with marker-switched hard cuts, that judges every frame through the first camera, giving false FILL/EMPTY results. I ran copies that re-read `sc.camera` after every `frame_set`. The shared pipeline is unchanged; the director may want to patch it.

**Preview.** `review/preview.mp4`: every 5th frame, 270×480, Cycles 4 samples + OIDN, with the VO. Rendered from this exact package: the full film, then frames 401–941 and 1436–1556 re-rendered after the last fixes and spliced in. I watched all 7 contact pages (341 frames).
