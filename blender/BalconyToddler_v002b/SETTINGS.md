# BalconyToddler_v002b: farm render sheet

Values read back from `BalconyToddler_v002b_60fps.blend` in factory-startup Blender 5.2.2 (no add-ons).

| Item | Value |
|---|---|
| File | `BalconyToddler_v002b_60fps.blend`: 49 MB, compressed. All images and the VO are packed; no linked libraries, no drivers. |
| Blender | 5.2.2 LTS |
| Engine | Cycles, device saved as CPU (GPU is fine). |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1751**, step 1 (29.2 s at 60 fps; built to the voiceover `BalconyToddler_v002b_VO.mp3`) |
| Cameras | 22 cameras, one per shot, switched by 22 timeline markers (hard cuts). Keep the markers: they are the edit. |
| Samples | 48, adaptive, noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 12, diffuse 4, glossy 4, transmission 12, transparent 8 |
| Motion blur | Off |
| Colour | AgX, look "AgX - Punchy", exposure 0 |
| Output | PNG to `//render/BalconyToddler_v002b_####.png` |
| Audio | The VO is packed on the sequencer as a timing reference; "Sequencer" is off for the render (3D scene only). Join the frames at 60 fps and lay the VO from frame 1. |
| Caches / sims | None: all motion is keyframes. |

## Shots (film frames)
| Shot | First | Last | VO words |
|---|---|---|---|
| S01 | 1 | 56 | A toddler slipped |
| S02 | 57 | 126 | between the bars |
| S03 | 127 | 223 | of a second-floor balcony. |
| S05 | 224 | 313 | His body fell through, |
| S07 | 314 | 368 | but his head |
| S08 | 369 | 420 | became trapped, |
| S09 | 421 | 553 | leaving him hanging above the ground. |
| S10 | 554 | 632 | People on the street saw |
| S11 | 633 | 691 | what happened and quickly |
| S12 | 692 | 742 | stacked chairs |
| S13 | 743 | 806 | beneath him. |
| S16 | 807 | 870 | One man climbed up |
| S17 | 871 | 914 | and grabbed |
| S18 | 915 | 1015 | the boy's legs, holding his weight |
| S19 | 1016 | 1146 | so the bars wouldn't crush his neck. |
| S20 | 1147 | 1255 | He stayed like that for several minutes |
| S21 | 1256 | 1306 | until the child's |
| S22 | 1307 | 1352 | grandmother got |
| S23 | 1353 | 1404 | inside the apartment |
| S24 | 1405 | 1496 | and pulled him back through the railing. |
| S25 | 1497 | 1580 | Somehow, |
| S26 | 1581 | 1751 | the toddler escaped completely unharmed. |

## Suggested test frames
- **300**: the boy's head resting between the floor bars (front).
- **960**: the man on the chair tower holding the boy's legs.
- **1700**: grandma and the boy, end shot.
