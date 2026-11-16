# LakeSword_v003: second director fix round (on v002b, kept unchanged)

Film B34 "She Found A 1,500-Year-Old Sword In A Lake", built by ConnectB34. Fix round on `LakeSword_v002` (kept unchanged). Vertical 1080×1920, 60 fps, Cycles.
It follows the reference still sheet's shot order (hard cuts) and is cut to the words of `LakeSword_v003_VO.mp3`.

- **File:** `LakeSword_v003_60fps.blend` (61 MB): compressed, every texture and the VO packed, opens in factory-startup Blender 5.2.2.
- **Frames 1–1826** at 60 fps (30.4 s). The last word ends at 29.92 s; the film holds 0.5 s after it.
- **Camera:** one camera, `CAM_Film`. The 17 hard cuts are baked into its keys (every frame); there are no markers.
- Settings: `SETTINGS.md`. Credits: `CREDITS.md`. Beat frames: `beats.json`. Moving preview: `review/preview.mp4` (every 5th frame, with the VO).

## How it was synced
- The VO was transcribed with `pipeline/transcribe.py` (`LakeSword_v003_VO.words.json`). Each shot starts at `1 + round(seconds × 60)` of its first word.
- The build (`LakeSword_v003/scripts`, 01_chars → 02_sets → 03_shots → 04_bake_camera) was re-run with the VO layout
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
| 08 | 709–766 | 0.97 s | but her father thought it | Side view: dad kneels on the grass; the sword lies between them |
| 09 | 767–833 | 1.12 s | might be important, | Dad holds it upright beside his face |
| 10 | 834–966 | 2.22 s | so they brought it to a museum. | Museum wide, sword on the felt, logo banner |
| 11 | 967–1060 | 1.57 s | Experts examined it and discovered the | Expert holds it low over the table; colleague leans in |
| 12 | 1061–1217 | 2.62 s | sword was more than a thousand years old. | Experts look at each other and nod; sword on the felt |
| 13 | 1218–1290 | 1.22 s | What looked like rust was | Macro: the crusted blade lying on the lakeshore, lake and trees behind |
| 14 | 1291–1452 | 2.70 s | actually part of an ancient leather sheath. | Macro: the crust becomes dark tooled leather; slow orbit |
| 15 | 1453–1546 | 1.57 s | The weapon dated back to before | Camp long ago: the warrior walks up to the fire, arms swinging, sword sheathed on his belt |
| 16 | 1547–1615 | 1.15 s | the Viking Age and | At the fire: he warms his hands (bent elbows), looks into the flames and out to the lake |
| 17 | 1616–1775 | 2.67 s | had somehow remained hidden in the city (Whisper's reading; the picture shows the lake). | The sheathed sword drops into the lake and settles on the bed |
| 18 | 1776–1826 | 0.85 s | She found it. | Today: the girl wades along the shallows |

## Logo
DA KRAS FILMS, white on the red museum banner (shots 10–12) and dark on the museum crate (shot 10). Nowhere else.

## What changed from v002 (director notes)
1. **Wardrobe and framing:** the girl now wears loose, straight dark-denim jeans with folds (cloth pushed out, smoothed, crease bump),
   not leggings. 06 is full body with her feet in frame; 07 is waist-up with the blade beside her face.
2. **Tiny static wides:** 03a, 10 and 18 are closer (she fills about half the frame height); in 10 Expert M leans in and out and
   Expert F turns to him.
3. **08:** a side angle, so dad's knees on the grass read as kneeling.
4. **Macro 13–14:** the sword lies on the lakeshore with the lake and trees behind, f/16, slow orbit; the crust is low-relief
   corroded green-brown; the "leather" is dark tooled leather (no lumpy orange).
5. **Warrior 15–16:** he walks up to the fire with a full arm swing, then warms his hands over it with bent elbows, head turning.

## v002c changes (director notes on v002b)
1. 03a (f98–220): arms relaxed by her thighs with soft elbows, a weight shift, a look down at the hilt and a small step toward it.
2. 06 (f451–594): knees-up framing with a slow push (she fills about half the frame height).
3. 13–14 (f1218–1452): camera above at about 40°, the blade runs diagonally through the frame, slow push along it.
4. 15 (f1453–1546): the warrior walks all the way to the fire (arm swing, head turning) and arrives at the cut to 16.

## Checks and preview
- `review/preview.mp4`: the v002b preview with these four ranges re-rendered from this exact package and spliced in
  (f101–220, f451–594, f1221–1452, f1456–1546).
- On those ranges: body_prop_cross 0, clip_scan 0 (03a's hands were first 2 cm into the thighs and were moved out),
  limb_check only the known shoulder false positive on the warrior's right arm. The rest of the film is unchanged from v002b.
