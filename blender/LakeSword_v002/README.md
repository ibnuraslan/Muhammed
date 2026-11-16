# LakeSword_v002: synced to the voiceover (Phase 2)

Film B34 "She Found A 1,500-Year-Old Sword In A Lake", built by ConnectB34. Vertical 1080×1920, 60 fps, Cycles.
It follows the reference still sheet's shot order (hard cuts) and is cut to the words of `LakeSword_v002_VO.mp3`.

- **File:** `LakeSword_v002_60fps.blend` (61 MB): compressed, every texture and the VO packed, opens in factory-startup Blender 5.2.2.
- **Frames 1–1826** at 60 fps (30.4 s). The last word ends at 29.92 s; the film holds 0.5 s after it.
- **Camera:** one camera, `CAM_Film`. The 17 hard cuts are baked into its keys (every frame); there are no markers.
- Settings: `SETTINGS.md`. Credits: `CREDITS.md`. Beat frames: `beats.json`. Moving preview: `review/preview.mp4` (every 5th frame, with the VO).

## How it was synced
- The VO was transcribed with `pipeline/transcribe.py` (`LakeSword_v002_VO.words.json`). Each shot starts at `1 + round(seconds × 60)` of its first word.
- The Phase-1 build (`LakeSword_v001/scripts`, 01_chars → 02_sets → 03_shots → 04_bake_camera) was re-run with the VO layout
  (`shots.json`). Every action keeps its 1× timing; walks keep their speed and simply cover less ground in a shorter shot. Nothing is time-stretched.
- Phase-1 shots 01 (wade) and 03b (looking down) are not used: the VO has no words for them.

## Shots on the VO
| Shot | Frames | Length | Words | Picture |
|---|---|---|---|---|
| 02 | 1–97 | 1.62 s | A girl stepped on something hard | Girl steps; her foot comes down beside the hilt in the sand |
| 03a | 98–220 | 2.05 s | while playing in shallow water. | Playing in the shallows, two kicks |
| 04 | 221–359 | 2.32 s | At first, she thought it was just a stick, | She bends and closes her hand on the hilt under the water |
| 05 | 360–450 | 1.52 s | but when she pulled it out, | She pulls the 'stick' out (face and rising blade; her fist below frame) |
| 06 | 451–594 | 2.40 s | she realized she was holding a sword. | She holds it upright at her side and looks up: a sword |
| 07 | 595–708 | 1.90 s | It looked rusty and damaged, | Close: crusted, damaged blade beside her face |
| 08 | 709–766 | 0.97 s | but her father thought it | Dad kneels; the sword lies on the grass between them |
| 09 | 767–833 | 1.12 s | might be important, | Dad holds it upright beside his face |
| 10 | 834–966 | 2.22 s | so they brought it to a museum. | Museum wide, sword on the felt, logo banner |
| 11 | 967–1060 | 1.57 s | Experts examined it and discovered the | Expert holds it low over the table; colleague leans in |
| 12 | 1061–1217 | 2.62 s | sword was more than a thousand years old. | Experts look at each other and nod; sword on the felt |
| 13 | 1218–1290 | 1.22 s | What looked like rust was | Macro: the crusted blade on sky blue |
| 14 | 1291–1452 | 2.70 s | actually part of an ancient leather sheath. | Macro: the crust becomes an old leather sheath |
| 15 | 1453–1546 | 1.57 s | The weapon dated back to before | Camp long ago: the warrior walks, sword sheathed on his belt |
| 16 | 1547–1615 | 1.15 s | the Viking Age and | Wide camp: warrior looks over the lake |
| 17 | 1616–1775 | 2.67 s | had somehow remained hidden in the city (Whisper's reading; the picture shows the lake). | The sheathed sword drops into the lake and settles on the bed |
| 18 | 1776–1826 | 0.85 s | She found it. | Today: the girl wades along the shallows |

## Logo
DA KRAS FILMS, white on the red museum banner (shots 10–12) and dark on the museum crate (shot 10). Nowhere else.

## Checks on this exact package (frames 1–1826)
| Check | Result |
|---|---|
| `clip_scan` (step 6) | 0 bad ranges |
| `body_prop_cross` (step 3, every sword copy and sheath, felt, table) | 0 visible crossings, **except shot 05 (f360–450, 26 sampled frames)**: fingertips 3–4 of her right fist inside the grip, and her forearm grazing the pommel during the pull |
| `limb_check` (step 4) | ARMBODY only, all "arm.R inside own torso, 2–3 pts" on relaxed hanging arms (08–11, 15): the known upper-arm-at-the-shoulder false positive (LESSONS §4); watched, no arm through a body |
| `qa_check` (step 6) | EMPTY on the macro (13–14) and sinking-sword (17) shots, which have no people by design; INSIDE on 13–14 (camera inside the sky dome, by design); CAMJUMP = one per hard cut; PROPMOVE in 17 = the falling sword; CLAW/FAN at a few grip frames (04, 11), watched, read as fists |

Watched: every page of `review/preview.mp4` (`review/p01–p08.jpg`). Fixed after the first watch: 05 showed no sword, 15 arm flip on its
last frame, 17 empty lake bed and a thick ripple ring, 18 girl leaving frame. Known soft spot: 10 is a slow push-in on a mostly still group (2.2 s).
