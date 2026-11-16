# MomLiftsCar_v002b (B14): Mom lifts a car off her son

Vertical explainer, 1080×1920, 60 fps, 1577 frames (26.3 s), built to the client's VO (`MomLiftsCar_v002b_VO.mp3`).
Source scripts: `scripts/` (sets 02, animation 03, VO layout 04, single-camera bake 05). Plan: `../MomLiftsCar_v001/PLAN.md`.

## Shots on the VO (beats.json)
| Frames | Words | Shot |
|---|---|---|
| 1–96 | In 1964, | Top-down over the car's rear: Mom crouches at the bumper, the son lies beside the car |
| 97–245 | a woman supposedly lifted a car | Side wide: she drives up out of the squat, the car's rear rises |
| 246–319 | off her trapped son | Low 3/4 rear: the car held up, the son on his back, legs under it |
| 320–401 | completely by herself. | Mom's face over the trunk lid, straining, looks down to her son |
| 402–486 | This is often described as | The son's face at ground level beside the raised car |
| 487–600 | hysterical strength. | Mom in profile holding the car |
| 601–712 | During extreme stress, the body | Kidneys and adrenal glands (clean anatomy, sky gradient) |
| 713–839 | releases huge amounts of adrenaline, | Close on a gland: it glows and releases amber adrenaline droplets |
| 840–917 | increasing blood flow and | Cut-open arteries: red cells and green oxygen dots rush through the split |
| 918–1019 | energy to the muscles. | A muscle fills with green energy dots and contracts |
| 1020–1140 | For a very short time, this can | Park: a man (yellow tee, our logo) steps up and squats beside a fallen trunk |
| 1141–1219 | allow someone to produce | Second angle: he heaves the trunk's thick end up |
| 1220–1308 | levels of strength they normally | He holds it at his hips, straining |
| 1309–1399 | couldn't access, letting the | Closer on him holding it (logo on his chest) |
| 1400–1488 | body perform something that | He lets go, the trunk drops, arms go up |
| 1489–1577 | would usually seem impossible. | Front: arms up in triumph |

Clips were animated at 1× and only **shifted** onto the VO (never time-stretched). Camera moves were re-windowed to the shot lengths.
Logo: DA KRAS FILMS on the man's T-shirt only (1220–1577).

## Checks (on this exact package)
- `body_prop_cross` frames 1–1577, every 3rd frame, props = car (3 meshes), jack, trunk (+stubs, cut faces); rigs Mom, Son, Man: **0 visible crossings**.
- `clip_scan`: the one bad range of the first build (1027–1075, the man's hands passing through his thighs on the way to the trunk) is fixed by an extra hand key; re-scan of 1020–1240: **0**.
- `qa_check`: CAMJUMP = the 15 planned hard cuts only; PROPMOVE = anatomy particles (blood cells, oxygen/adrenaline dots), no hands involved; EMPTY = the anatomy shots 601–1019 (no character, by design) and car-filled frames in 1b/1c/1e (the car is the story subject); BACKHEAD frame 1 = the top-down opener (Mom from above, as in the reference).
- `limb_check` (shoulder points excluded): Son "arm inside own torso" 1–485 and Man 1437–1577 (3 pts, raised arms). The son lies on his back with his arms out at 45° on the ground; the render `review/son_arms_top_and_side_f200.jpg` shows both arms clear of the body (the test's nearest-normal inside check misfires on a body lying flat). The man's points are at the armpit with arms raised; the preview shows clean arms.
- Preview `review/preview.mp4` (every 5th frame, 270×480, Cycles 4 + OIDN, with the VO), rendered from this package; frames 246–319 and 1021–1141 re-rendered after the two fixes and spliced in. All 7 contact pages watched.

## v002b changes (director notes on v002)
1. Park (1021–1577): every blob tree replaced by the real Poly Haven tree (tree_small_02, LOD1 meshes, 18 linked copies, 4.4–6 m); hedges, benches and lamps kept.
2. Shot 2a (487–600): the camera is now a wider profile (24 mm) aimed at the rear bumper, so Mom's hands are seen under the bumper with the car's rear in frame.
3. The blank number plate is now a deeper box, so the model's original plate texture can't show from side angles (it showed in the new 2a angle).
Preview: frames 1–600 and 1021–1577 re-rendered from this package and spliced into the v002 preview (601–1020 unchanged).
Checks on v002b: body_prop_cross 1–1577 = 0 visible crossings; clip_scan 1–600 = 0; clip_scan 1020–1577 = one sampled frame (1410, the man's self-contact as he lets go of the trunk; the preview frame 1411 shows clean hands).
