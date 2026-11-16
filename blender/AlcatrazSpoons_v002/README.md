# AlcatrazSpoons_v002: synced to the voiceover (Phase 2)

Film B07 "Escaping Prison With Spoons" (Alcatraz, 1962), built by ConnectB07. Vertical 1080×1920, 60 fps, Cycles.
It follows the reference still sheet shot for shot (24 hard-cut shots) and is cut to the words of `B07_AlcatrazSpoons_VO.mp3`.

- **File:** `AlcatrazSpoons_v002_60fps.blend`. It is compressed, with every texture and the VO packed, and opens in factory-startup Blender 5.2.2.
- **Frames 1–2007** at 60 fps (33.4 s). The last word ends at 32.94 s, and the film holds for 0.5 s after it.
- **Camera:** one camera, `CAM_Film`. The 24 hard cuts are baked into its keys; there are no markers.
- Settings: `SETTINGS.md`. Credits: `CREDITS.md`. Beat frames: `beats.json`. Moving preview: `review/preview.mp4`.

## How it was synced
- The VO was transcribed with `pipeline/transcribe.py` (output in `VO.words.json`). Each shot starts at `1 + round(seconds × 60)` of its first word.
- Each Phase-1 clip (P1 passed, `AlcatrazSpoons_v001`) was **trimmed** to its VO slot at 1× speed: a window of the clip starting at `in` is
  moved unchanged onto the VO frames (`trim_to_vo` in `scripts/03_shots.py`). Nothing is time-stretched. The table is in `shots.json`.
- Change from v001 requested by the director: in **2a**, P1's face is lifted and turned 3/4 toward the camera while he scrapes.

## Shots on the VO
| Shot | Frames | Length | Words |
|---|---|---|---|
| 1a | 1–107 | 1.78 s | Three prisoners used spoons |
| 1b | 108–209 | 1.70 s | to slowly dig through the walls |
| 1c | 210–294 | 1.42 s | of their Alcatraz cells. |
| 2a | 295–365 | 1.18 s | Every night, |
| 2b | 366–413 | 0.80 s | they scraped away |
| 2c | 414–527 | 1.90 s | the concrete around their air vents, |
| 2d | 528–680 | 2.55 s | making the holes larger and larger. |
| 3a | 681–755 | 1.25 s | They even built a homemade |
| 3b | 756–829 | 1.23 s | drill from a vacuum |
| 3c | 830–887 | 0.97 s | cleaner and created |
| 4a | 888–932 | 0.75 s | fake heads |
| 4b | 933–1000 | 1.13 s | to fool guards during |
| 4c | 1001–1068 | 1.13 s | bed checks. |
| 5a | 1069–1121 | 0.88 s | After months of |
| 5b | 1122–1190 | 1.15 s | digging, they finally |
| 5c | 1191–1253 | 1.05 s | crawled through the wall |
| 5d | 1254–1358 | 1.75 s | into a service corridor. |
| 6a | 1359–1483 | 2.08 s | From there, they climbed onto the roof, |
| 6b | 1484–1549 | 1.10 s | slid down a pipe, |
| 7a | 1550–1656 | 1.78 s | and reached the shore. Then, |
| 7b | 1657–1716 | 1.00 s | they escaped on a raft |
| 7c | 1717–1813 | 1.62 s | made from raincoats. |
| 8a | 1814–1928 | 1.92 s | Despite a massive manhunt, |
| 8b | 1929–2007 | 1.32 s | they were never found. |

## Build
`scripts/01_chars.py` → `02_sets.py` → `03_shots.py -- film2.blend ../shots.json` → `04_bake_camera.py -- VO.mp3 baked.blend` →
`pipeline/package_for_farm.py`.

## Checks on this exact file (ConnectB07)
- **Moving preview** (`review/preview.mp4`, every 5th frame at 270×480, with the VO; contact pages `review/p01–p09.jpg`) watched start to finish.
- **2a** frames 295–365: P1's face reads 3/4 toward the camera while he scrapes (head yaw +35°; −35° turned it away, so it was rejected).
- `body_prop_cross` (every 6th frame, all props, including the four spoons): **0 visible crossings**. The only on-screen flags are the hidden MPFB "root" helper
  shell the checker exposes by switching masks off (a known false positive). Other flags (the guard's feet and flashlight in 4b, P3's foot in 3c) are off-screen.
- `clip_scan` and `limb_check`: hits are fingertips resting on thighs/knees (1c, 2a, 5c, raft) and arms bent at the body. They were checked in 540×960 renders
  (frames 241, 1201, 1681) and look clean. `qa_check`: EMPTY/PROPMOVE flags are the intended no-character inserts (2d vent close-up, 3b drill, 4a/4c dummy head, 5a grille, 8a searchlight).
- Note: in 7a (around frame 1620) moonlight glints on the wave crests show as soft white patches at the lower left.
