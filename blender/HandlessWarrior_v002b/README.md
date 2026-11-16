# HandlessWarrior_v002b (B23): built to the client VO

## What changed from v002 (director notes; v002 is untouched)
1. **Soldier wardrobe** (every soldier: SoldierA, SoldierB + guard ring, the officer, SoldierC + the army): no more one-colour
   suits. Each soldier now wears a doublet (red, or blue for SoldierB) over **contrasting breeches** (buff, grey for the blue
   ones), a dark leather **belt**, knee **boots** and the steel (officer: brass) breastplate and morion. One material per suit
   (`kit()` in `01_chars.py`), banded on the rest-pose height so it never slides when they move.
2. **S05 hut (246–356)**: the camera starts wide on all five and pushes in to the warrior and the elder. The woman puts her
   hand to her mouth, the two men turn to each other and back, then the far man takes a step back; the elder lifts his
   open palm. Villagers re-placed so nobody hides behind anyone.
3. **S14 fight (997–1146)**: over the warrior's right shoulder, both men waist-up. The officer walks in, winds up and cuts
   (the blade passes beside him); the warrior sways, cocks his right blade, lunges with his right foot and THRUSTS (stops
   short of the cuirass, spark at f1083); the officer RECOILS (head snaps back, sword arm flung up, two steps back, hand to
   his chest).

Only those ranges were re-rendered for the preview (all soldier shots S01–S03, S13–S14, S16–S17, plus S05) and spliced
into the v002 preview frames.


- `HandlessWarrior_v002b_60fps.blend`: 1080×1920, 60 fps, Cycles, frames **1–1615**, every image and the VO packed (88 MB).
- `HandlessWarrior_v002b_VO.mp3` + `HandlessWarrior_v002b_VO.words.json` (faster-whisper word times).
- `beats.json`: shot start frames = 1 + round(word seconds × 60).
- `review/preview.mp4`: the full moving preview (every 5th frame, 270×480, Cycles 4 + OIDN) from this exact file, with the VO.
- `review/CHECKS.md`: the four checks on this file and how each flag was resolved.
- `SETTINGS.md`, `CREDITS.md`, `PLAN.md` (shots and staging; S04 is not used in the VO cut, S03 carries the walk-off).

How it was built (`scripts/`): 01_chars → 02_sets → 03_anim (each shot animated at 1× as its own clip, P1 timeline) →
05_vo (each shot's clip is TRIMMED to its VO window and SHIFTED onto the word frames: no time scaling anywhere) → 04_pack.
`timing.py` holds the P1 clip lengths, the VO beat table and the trim offsets.

| Shot | VO words | Frames |
|---|---|---|
| S01 | They cut off both of his hands | 1–90 |
| S02 | as punishment | 91–154 |
| S03 | then sent him back to his people | 155–245 |
| S05 | with orders to surrender | 246–356 |
| S06 | But instead, the warrior convinced them | 357–480 |
| S07 | to keep fighting | 481–564 |
| S08 | He sealed the wounds | 565–614 |
| S09 | with hot metal | 615–689 |
| S10 | then strapped knives | 690–744 |
| S11 | onto his wrists | 745–824 |
| S12 | When the battle began | 825–892 |
| S13 | he charged straight into the enemy | 893–996 |
| S14 | and even killed the general's second-in-command | 997–1146 |
| S15 | Eventually | 1147–1214 |
| S16 | his people were defeated | 1215–1273 |
| S17 | But despite losing both hands, the warrior continued fighting until the very end | 1274–1615 |

## Known points
- S03: the soldier stands half-turned toward the village so his pointing arm stays in front of him; the warrior's face carries the beat.
- S08, S10, S15 are prop/insert shots (forge, knives on the table, the flag) with no character, as in the reference.
- The DA KRAS FILMS logo is shown once, on the supply crate in S07 (whole, flat to camera, ~1.4 s).
