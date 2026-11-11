# DrunkTrain_v001: checkpoint C (polish)

- Sheets: `review/C_polish_0.2s_part1.jpg` … (0.2 s steps, 270×480, 8 samples, no motion blur; every still in the film).
- Audit: `review/C_audit.txt` from `scripts/04_audit.py` (every 6 frames, 345 frames sampled).

## Audit summary (numeric penetration check: BVH overlap of the real meshes)
| check | frames flagged | notes |
|---|---|---|
| Lad vs train (loco, plough, wheelsets) | **0** | was 29: he now tumbles between the rails, limbs clamped clear of the wheels and under the chassis |
| people vs people | **0** | the running witnesses are offset in lanes |
| hard hat vs head | **0** | hat on the head bone, hair hidden under it, scratching hand moved off the hat |
| camera inside geometry | **0** | the platform pass at 15.6 s and the plough pass at 11.5 s are fixed |
| head on rail | 4 | only the 0.15 s landing bounce (2.7–3.0 s); the resting head is within 2 cm of the railhead |
| foot sink / hover | 50 / 31 | mostly an audit artefact: its ground model was 2–3 cm off the ballast mesh at the shoulder and the grass. Real ones: two walk plants at 2.0–2.1 s and the crawl's first knee plant (19.8 s). Fixing these for D. |

## Changes since B (director's fixes)
1. **Rail shots (5.5–8.5 s):** wide and low on the whole body. The cheek is on the rail, the arm is flopped over beside his head, and his chest breathes with a snore jaw. No isolated-head framing.
2. **Under the train (11–14.5 s):** he tumbles between the rails under the chassis. The model's wheel "drums" were rebuilt as real wheelsets (flanged discs and an axle). The plough has a realistic gap, and his limbs are clamped clear of the wheels. The camera rides low between the rails ahead of him, with sparks and darkness. The train was re-timed to 14 m/s so it stops with a wheelset gap over him, and he crawls out through it.
3. **Ballast:** grey angular crushed stone, 3–6 cm with tonal variation, and weeds between the sleepers.
4. **X-ray:** the CC-BY "Male Body Muscular System" model is fitted to his body and skinned to his rig. It has red striated SSS fibres with a rim glow, in a deeper cyan-to-navy studio, framed big. The ghost train is translucent cyan with a fresnel rim, and the force arrows are bolder.
5. **Locomotive:** rust streaks, oily grime and dust up from the rails; headlight glow; a horn exhaust and dust kick; camera rumble that grows as it nears and jolts at the impact.
6. **Faces:**
   - eyes shut and a snoring mouth while passed out
   - the witnesses' jaws drop in horror (hands to mouth, hands on head)
   - a stunned blink as he comes round
   - a dazed grin at the end
   - the 23 s framing now shows his face and chest
7. Also:
   - the fingers grip the bottle
   - birds lift off the fence
   - grip and drop of the bottle at the trip
   - the tee print is removed
   - textures use box projection (no stretched stripes on the rails)

## Known issues
- The trees use Poly Haven's geometry-nodes version: much lighter, slightly sparser leaves.
- The grin is subtle at 270 px.
