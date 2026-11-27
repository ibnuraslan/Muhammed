# RooseveltSpeech_v012: farm render sheet

| Item | Value |
|---|---|
| File | `RooseveltSpeech_v012_60fps.blend`, 52 MB, compressed. Everything is packed, including the VO. It has no linked libraries, no drivers and no Python. It is stored as a regular git file (no LFS). |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU; GPU also works. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1307**, step 1 (21.8 s). Built to the client's VO from the start (the v011 timing), so no retime is needed. |
| Camera | One camera, `CAM_Film`, keyed on every frame, in one continuous move with no camera markers. DOF is off. Clip start is 3 mm, for the real-scale cutaway. |
| Samples | 64 max, adaptive sampling on, noise threshold 0.05, OpenImageDenoise |
| Light paths | Max 6, diffuse 3, glossy 3, transmission 6, transparent 16. Caustics off. Persistent data on. Simplify: subdivision 2, texture limit 2048. |
| Motion blur | Off |
| Colour | AgX, look "Punchy", exposure +0.3 |
| Output | PNG, RGB, 8-bit, to `//render/RooseveltSpeech_v012_####.png` |
| Audio | `RooseveltSpeech_v012_VO.mp3` is packed as the sound strip `VO` at frame 1. |
| Sims | None: all motion is keyframed. The cutaway layers use geometry-nodes modifiers (`GN_Cut_*`) that read the keyed empty `TipCtl`, never the scene clock. Do not delete `TipCtl`. The flags use Wave modifiers. |
| Sets | STREET is at the origin, MACRO at x=+40 and HALL at y=+60. The camera switches set on a hard match: frame 390 is the coat hole into the bullet in the pages, and frame 1028 is the cutaway into the holed speech in his hand. |

## The move
| Frames | Time | What the camera sees |
|---|---|---|
| 1–40 | 0–0.7 s | Over the gunman's shoulder: Roosevelt waves in front of his car, with onlookers around him. The muzzle flash comes at f40. |
| 40–128 | 0.7–2.1 s | It chases the slow-motion bullet into his chest. |
| 128–264 | 2.1–4.4 s | He jolts, feels for the wound, then steadies. The hotel sign carries the logo. |
| 265–389 | 4.4–6.5 s | The camera glides to his face, then pushes into the bullet hole in his coat. |
| 390–736 | 6.5–12.3 s | The cutaway: the bullet tears through the folded, inked speech, with the steel glasses case (spectacles inside) below it. |
| 737–1027 | 12.3–17.1 s | Through the case, then shirt, skin and fat. It stops in the chest muscle above the ribs and lung, and the camera pulls back. |
| 1028–1139 | 17.1–19.0 s | The hall: the holed speech in his raised hand, pulling out to his face. |
| 1139–1307 | 19.0–21.8 s | Fist raised, speaking. The camera cranes up and back over the cheering crowd. The flags, bunting and spinning clock are in view, and the lectern carries the logo. |

## Logo
DA KRAS FILMS is on the hotel sign (f141–206), the car door panel (f1–60) and the lectern front (f1131–1246).
