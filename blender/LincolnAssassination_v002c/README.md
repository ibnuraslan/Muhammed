# LincolnAssassination_v002c: S05A fix on v002b (director: everything else approved)

Changes from v002b (only S05A, f362–454, changed in picture; same beats.json, frame range and every other key):
- **S05A:** a real medium two-shot, about thigh-up. The camera is level with their faces, a 62 mm lens, a slow push-in. She is
  slightly nearer at frame left; he is just behind her shoulder at frame right. Both faces turn three-quarters toward the camera,
  with eyes clear: his fedora is hidden for this shot only, and both fringes are lifted off the eyes.
- They laugh with the body: the head tips back and bounces with the laugh, the mouth opens (jaw keyed), she puts her right
  hand on her chest, he puts his left hand on his, and each gestures toward the other with the free hand. Clip scan clean
  (palms on the shirt, not in the torso).
- The fringe lift is a rest-mesh edit on both actors' hair, so it applies in every shot. Frames 1–533 were re-rendered and
  diffed against the v002b package: identical (RMSE ≈0.003, the 4-sample noise floor) outside S05A.
- Preview: **every preview frame (1–1501, step 5) was re-rendered from this exact v002c package.** The v002b preview's f1–36 were
  stale; the package already showed the gun hand entering bottom-left from f1 (the gun rise in S01), which the old preview did not.

# v002b notes (director fix round on v002)

Changes from v002 (everything else identical, same beats.json and frame range):
- **Barn fire (f1131–1503):** the particle 'popcorn' fire is replaced by layered emissive flame cards (three rows on the back wall, two on each side wall, angled, noise-shaped flickering tongues: deep red edges, orange body, small yellow core) plus a dark smoke volume along the walls above the flames. All driven by keyed clocks (no Scene Time, no caches). Warm fire lights on his face unchanged.
- **S05A (f362–454):** new camera at stage level beyond the footlights: medium two-shot of the two actors laughing, faces readable, painted drawing-room backdrop (window flat) and the parlour table behind them.
- Preview: only those two ranges were re-rendered from the v002b package and spliced into the v002 preview.

# Original v002 notes

Vertical 1080×1920, 60 fps, Cycles, 17 shots with hard cuts, frames **1–1503** (VO 24.76 s; the last word ends at 24.54 s).
Built from Phase 1 (v001, director-passed at P1e) by putting the VO word frames into `scripts/timing.py` and rebuilding.
Every action plays at 1× from its word frame; nothing is time-stretched.

## Files
- `LincolnAssassination_v002c_60fps.blend`: the package (textures and VO packed, compressed, factory-startup clean).
- `LincolnAssassination_v002c_VO.mp3`: the client VO (also in the sequencer at frame 1).
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
| S05A | 362 | for a loud moment in the play | thigh-up two-shot of the two actors laughing (head back, hand on chest, gesturing), backdrop behind |
| S05 | 455 | and pulled the trigger | gun in profile at the hat; flash on "trigger" (f480), hard cut, small smoke wisps |
| S06 | 534 | After firing, | he lowers the gun, glances back, turns to the ledge |
| S07 | 589 | he jumped down onto the stage, | low angle: on the ledge, crouches, jumps |
| S08 | 687 | breaking his leg | lands on the stage, knee buckles |
| S09 | 750 | when he landed. | side close-up: kneeling leg with a small red crack flash, face in profile |
| S10 | 801 | But despite the injury, | stands and limps toward camera |
| S11 | 893 | he escaped the theater on | night street, gallops toward camera (moonlit rim) |
| S12 | 962 | horseback. | side gallop past the DA KRAS FILMS poster |
| S13 | 1025 | A massive manhunt followed, | three soldiers with torches jog toward camera (logo crate) |
| S14 | 1131 | and he managed to hide for 12 days before | close: he crouches hidden behind the hay bales, fire behind him, looks around |
| S14B | 1271 | authorities finally | barn from the doorway: soldiers with torches step in, he stands up |
| S15 | 1325 | found him hiding inside a barn and killed him. | medium on him, hands raised, fire behind; ends on a hard cut (no shooting shown) |

## Review done before delivery
- Watched the full moving preview twice (every 5th frame, all 7 pages) from the exact package; fixed everything found, re-rendered
  only the changed ranges (S06, S08, S12, S14 to S15) from the repacked file and spliced them in.
- Checks: `review/checks.md` (per-shot camera wrapper `scripts/per_shot_check.py`).
