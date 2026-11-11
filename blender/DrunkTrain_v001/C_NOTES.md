# DrunkTrain_v001: checkpoint C (polish)

- Sheets: `review/C_polish_0.2s_part1.jpg` … (0.2 s steps, 270×480, 8 samples, no motion blur; every still in the film).
- Audit: `review/C_audit.txt` from `scripts/04_audit.py` (every 6 frames, 345 frames sampled).

## Audit summary (numeric penetration check: BVH overlap of the real meshes)
| check | frames flagged (of 345 sampled) | notes |
|---|---|---|
| Lad vs train (loco, wheelsets) | **5** | was 29 at the first pass. He tumbles between the rails under the GP18. The remaining 5 are brief contacts: his head grazing the under-gear at 11.1 s and 12.6–12.7 s, and his left upper arm against the truck side as he crawls out (19.6–19.7 s). |
| people vs people | **0** | the running witnesses are offset in lanes |
| hard hat vs head | **0** | the hat is on the head bone, his hair is hidden under it, and the scratching hand is moved off the hat |
| camera inside geometry | **1** | 13.7 s: the camera passes 6 mm from the loco's under-frame as it leaves from under the train (no black frame left) |
| head on rail | 4 | only the 0.15 s landing bounce (2.7–3.0 s); the resting head is within 2 cm of the railhead |
| foot sink / hover | 13 / 76 | the hovers are mostly his heels resting about 3.5 cm above the flat ballast plane while he lies there (the stones cover it). The real ones are his feet in the air during the sit and flop (3.8–5.0 s). |

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

## Realism pass (client note, 21:00)
- **Locomotive:** now the CC-BY "EMD GP18", detailed real geometry, with weathered maroon paint, rust streaks, oil and dust. Our own spinning wheelsets sit on its 4 axles, its headlights are on the real nose, and there is no livery or text.
- **Houses:** three real CC-BY house models in place of the boxes.
- **Platform:** rebuilt with a brick face, separate coping slabs, pavers, a worn edge line and real street-lamp models. The box bench, shelter and signal are removed, and the poles are now round timber.
- **Tee:** the stock print, which was also baked into the AO and normal maps, is fully removed; the tee is now split from the shorts by position.

## Known issues
- The sheets show a thin white band at the tee hem: the hem hangs below the waist split. Fixed for the package build in D.
- 30.6–31.0 s: the whip out of the studio passes 3 sparse cyan frames.
- The trees use Poly Haven's geometry-nodes version: much lighter, slightly sparser leaves.
- The grin is subtle at 270 px.
