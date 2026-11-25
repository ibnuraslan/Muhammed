# BellyFat_v018: farm render sheet

| Item | Value |
|---|---|
| File | `BellyFat_v018_60fps.blend`, about 65 MB, compressed. Everything is packed, including the VO. There are no linked libraries, no drivers and no Python. Background textures are 512–1024 px; her skin, hair and T-shirt are 2048 px. It is stored as a regular git file (no LFS). |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU; GPU also works, and no special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1273**, step 1 (21.2 s). Built to the client's VO from the start (the v017 timing), so no retime. |
| Camera | One camera, `CAM_Film`, keyed on every frame, in **one continuous move with no cuts and no camera markers**. DOF is off, so everything is sharp. Clip start is 4 mm, for the real-scale cross-section. |
| Samples | 64 max, adaptive sampling on, noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 6, diffuse 3, glossy 3, transmission 6, transparent 16. Caustics off. Persistent data on. Simplify: subdivision 2, texture limit 2048. |
| Motion blur | Off (animated look) |
| Colour | Display sRGB. View **Filmic**, look **High Contrast**, exposure −0.6. |
| Output | PNG, RGB, 8-bit, to `//render/BellyFat_v018_####.png` |
| Audio | `BellyFat_v018_VO.mp3` (21.0 s) is packed as the sound strip `VO` at frame 1. The same mp3 sits next to the .blend for encoding. |
| Caches and sims | None: no simulations, particles, Alembic or baked data. All motion is keyframes, plus two geometry-nodes modifiers on the cross-section (`GN_Wound_cut`, `GN_Wound_top`). They read the keyed empties `TipCtl` (the bullet nose) and `WoundCtl` (energy, ripple phase, entry). They never read the scene clock. Do not delete either empty. |
| Add-ons | None needed. MPFB2 was used only to build the character. |
| Animated visibility | Constant `hide_render` + `hide_viewport` keys switch the two sets: the HOME collection renders in frames 1–139 and 1137–1273, and the MACRO collection in 140–1136. Both switches happen inside a full-frame impact flash. Do not use any "render visible only" override. |

## The one move
| Frames | Time | What the camera sees |
|---|---|---|
| 1–30 | 0.0–0.5 s | Outside on the sunny terrace. The French window is open on one side, with blue shutters and an orange facade. She stands inside in the teal living room, looking out. The bullet streaks in and cracks the closed pane (f30). |
| 30–60 | 0.5–1.0 s | The camera glides in through the open door leaf. She turns to the crack, startled. |
| 60–128 | 1.0–2.1 s | The bullet in slow motion in the foreground, flying at her belly. Her face and the logo are behind it. It hits her shirt (f128). |
| 128–157 | 2.1–2.6 s | Close on the bullet denting the shirt, then a warm impact flash around the bullet. The same bullet comes out of the flash in the cross-section (set switch at f140, inside the flash). |
| 157–451 | 2.6–7.5 s | The cross-section: the bullet pierces the shirt and skin (f165–192) and pushes into the yellow fat. The wound track forms behind it, and the fat squeezes and ripples ahead of its nose. |
| 451–715 | 7.5–11.9 s | "Layer by layer": the bullet bows and breaks the fascia sheets. It slows down, and the ripples fade. |
| 715–985 | 11.9–16.4 s | The red muscle comes into view. The bullet crawls and stops with its nose in the muscle surface (about f960), while the camera orbits it. |
| 985–1100 | 16.4–18.3 s | The camera pulls back: the stopped bullet, with the untouched bowel loops below ("before it hit any organs"). |
| 1100–1147 | 18.3–19.1 s | The camera rises up the wound track to the shirt, through a short flash (set switch at f1137), to the hole in her shirt. |
| 1147–1273 | 19.1–21.2 s | It pulls out to her face. Her right hand rests flat on her belly beside the hole. She looks down, looks up, gives a long exhale with her eyes closed, then a small relieved smile. |

## Logo
DA KRAS FILMS is printed on her T-shirt (white on magenta). It reads in full in **f40–100** and **f1165–1273** (about 1 s and 1.8 s).

## Suggested test frames before the full job
- **20**: the window from outside, with her inside
- **84**: the bullet in the foreground, with her face and the logo
- **300**: the bullet in the fat
- **960**: the bullet stopped at the muscle
- **1060**: the bullet with the bowel loops below
- **1240**: her face, the hand on her belly, the hole and the logo
