# LincolnAssassination_v002: built to the client VO

Vertical 1080×1920, 60 fps, Cycles, 16 shots with hard cuts, frames **1–1503** (VO 24.76 s; the last word ends at 24.54 s).
Built from Phase 1 (v001, director-passed at P1e) by putting the VO word frames into `scripts/timing.py` and rebuilding.
Every action plays at 1× from its word frame; nothing is time-stretched.

## Files
- `LincolnAssassination_v002_60fps.blend`: the package (textures and VO packed, compressed, factory-startup clean).
- `LincolnAssassination_v002_VO.mp3`: the client VO (also in the sequencer at frame 1).
- `beats.json`: shot start frames from the VO words (`1 + round(word_start × 60)`).
- `review/preview.mp4`: moving preview, every 5th frame at 270×480, Cycles 4 samples + OIDN, with the VO, rendered from this exact file.
- `review/checks.md`: clip_scan / qa_check / limb_check / body_prop_cross results with the reason for every remaining flag.
- `SETTINGS.md`, `CREDITS.md`, `scripts/` (build: 01_chars → 02_sets → 03_anim; see v001/README.md for the asset fetch).

## Shots (frame: words → picture)
| Shot | Frame | VO | Picture |
|---|---|---|---|
| S01 | 1 | He pulled out a small pistol | over the gunman's shoulder: the gun rises behind the president's top hat |
| S02 | 107 | and aimed it directly | side shot of the gunman aiming (face) |
| S03 | 174 | at the back of Lincoln's head | over his arm: gun hand behind the top hat, actors on stage |
| S04 | 285 | Then, he waited | close-up of the gunman's face |
| S05A | 362 | for a loud moment in the play | the actors' big laugh on stage |
| S05 | 455 | and pulled the trigger | gun in profile at the hat; flash on "trigger" (f480), hard cut, small smoke wisps |
| S06 | 534 | After firing, | he lowers the gun, glances back, turns to the ledge |
| S07 | 589 | he jumped down onto the stage, | low angle: on the ledge, crouches, jumps |
| S08 | 687 | breaking his leg | lands on the stage, knee buckles |
| S09 | 750 | when he landed. | side close-up: kneeling leg with a small red crack flash, face in profile |
| S10 | 801 | But despite the injury, | stands and limps toward camera |
| S11 | 893 | he escaped the theater on | night street, gallops toward camera (moonlit rim) |
| S12 | 962 | horseback. | side gallop past the DA KRAS FILMS poster |
| S13 | 1025 | A massive manhunt followed, | three soldiers with torches jog toward camera (logo crate) |
| S14 | 1131 | and he managed to hide for 12 days before authorities | barn from the doorway: he hides behind the hay; soldiers step in on "authorities" |
| S15 | 1325 | found him hiding inside a barn and killed him. | medium on him, hands raised, fire behind; ends on a hard cut (no shooting shown) |
