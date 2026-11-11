# DrunkTrain_v001: checkpoint B (blocking)

- Sheet: `review/B_blocking_1s.jpg` (1 still per second, 270×480, 8 samples, no motion blur). 35 stills, 0–34 s.
- Timing: built to the brief's target beat times; `beats.json` lists the start frame of each beat for `retime_to_vo.py`.
- Scripts: `scripts/01_build_people.py` → `02_build_scene.py` → `03_animate.py` (runs `03b_fx_camera.py`).

## Camera path (one camera `CAM_Film`, one Catmull-Rom spline through these framings, aim + lens animated too)
| s | framing |
|---|---|
| 0–2 | front-left at hip height, weaving with him across the tracks, drifting right and dropping low as he trips |
| 2.5–4 | orbits round him as he stumbles and sits, then swings round to the track side |
| 4.5–5.5 | low along the rail on his head on the railhead |
| 6–8.5 | rail-level, rack focus down the rail to the locomotive's headlights; pulls back low as it grows |
| 9–11 | impact, then the camera speeds along with his spinning body beside the plough |
| 11–14 | skims low beside him under the loco side, between wheels and sparks |
| 14.5–17 | low at the locking wheels, pulls out along the train, cranes high over the stopped train and the running witnesses |
| 17–19.5 | cranes down into the witnesses, past their faces, pushes to the gap under the train |
| 19.5–21 | low at the gap as he crawls out, rises with him |
| 21–23.5 | whips round his head (flash-back, warm light, bottle swig), pushes into his chest |
| 23.5–26.5 | comes out of the chest in the x-ray studio, orbits the translucent body, macro on loose arm muscles |
| 26.5–31 | wide on the slow-motion replay (ghost train, force arrows), tracks with his flowing body, orbits; whip back out |
| 31–34.5 | behind him walking off along the platform, swings to the front, close on his palm, tilts up to his face |

## Known issues (for C)
- Tee: a very faint ghost of the stock print is still visible in close-ups; will flatten it.
- 13 s: a flung arm brushes an axle box under the loco; limbs need a clearance pass.
- 22 s: the swig is framed on his face more than the bottle; reframe.
- Eyes stay open while passed out; eyelids, snore mouth and the final grin are still to come (face bones exist).
- Dust and sparks are placeholders; the x-ray muscles are stylised bundles.
- 31 s: the whip back out of the studio is a mostly-white frame.
