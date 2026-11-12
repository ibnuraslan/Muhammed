# ToucanBeak (Connect28)

A 37.5 s vertical short (1080×1920, 60 fps, 2250 frames) on one continuous camera, with no cuts. A keel-billed toucan's upper beak is smashed by a stick. Rescuers scan the stump, design the missing half on a computer, print it hollow, then glue and pin it on. The toucan eats again.

## Look
The animated-CG look follows `blender/STYLE_ANIMATED.md`: `pipeline/anim_look.py` plus `scripts/05_look.py`. That means bright high-key light, AgX Punchy, sky-blue gradient backdrops for the explainer beats, clean surfaces, and f-stop ≥ 5.6.

## Beats (`beats.json`, target times from the brief)
| # | frame | line | staging, all one camera |
|---|---|---|---|
| 1 | 1 | A stick swung down… | The toucan on a lichen branch at the jungle edge. The camera rides the slow-motion stick. |
| 2 | 103 | …right into the toucan's upper beak | Impact in slow motion: beak chips fly (no blood), the bird flinches and its wings flare. The camera orbits to a macro. |
| 3 | 283 | every time it tried to eat | Two lunges at a hanging fig: it slips off the stub and drops. Frustrated head shakes. |
| 4 | 535 | rescuers scanned the broken stump | The camera flies through foliage and the window into the clinic. A vet cradles the bird while a handheld 3D scanner's red laser line sweeps the stump. |
| 5 | 679 | compared it to another toucan's beak | Push through the monitor screen (a real portal) into the sky-gradient data space. The stump appears as a blue point cloud; a green reference beak glides on and aligns. |
| 6 | 847 | rebuild the missing half on a computer | The orange CAD half grows out of the stump. Orbit. |
| 7 | 1063 | couldn't be too heavy… | A blue ghost toucan: a heavy steel beak tips its head forward and the perch wobbles. The light beak swaps in and the head lifts. |
| 8 | 1351 | full-size, but almost hollow | A cream printed beak cut in half shows the gyroid honeycomb inside; the printer prints a beak. |
| 9 | 1513 | lined it up with the broken stump | The camera flies back out through the screen. Gloved hands slide the painted prosthetic onto the stump (macro). |
| 10 | 1705 | glued the base… fixed the rest with a pin | A syringe lays the glue bead; tweezers push a steel pin in. The vets' focused faces. |
| 11 | 1981 | …could pick up fruit again | The camera pulls out of the window to the enclosure. The toucan picks up a fig from the feeding platform, tosses it, catches it and swallows. Slow orbit, then it settles. |

## Rebuild
```
cd blender/ToucanBeak_v001
bash scripts/build_all.sh full    # bird, vets, sets, animation, look  ->  work/look.blend
blender -b work/look.blend -P ../pipeline/stills.py -- stills/C 0.2 270
blender -b work/look.blend -P scripts/audit.py -- audit_C.txt 2
blender -b work/look.blend -P scripts/06_package.py -- ../ToucanBeak_v002/ToucanBeak_v002_60fps.blend
```
Inputs: `assets/` (CC-BY GLBs plus `credits.json`, Poly Haven scans in `assets/ph`), MPFB2 with the MakeHuman assets.

## Audit (`scripts/audit.py`)
Toe hover/sink against the perch, towel and platform; glove-vs-bird overlaps; hands-rule BVH checks (hand vs hand, hand vs own torso/clothes/head, hand vs other characters); camera inside a mesh; the fig resting on the platform. No head-worn items are used.
