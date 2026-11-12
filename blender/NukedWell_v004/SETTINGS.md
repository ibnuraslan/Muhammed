# NukedWell_v004: farm render sheet

These values are read back from `NukedWell_v004_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `NukedWell_v004_60fps.blend`: compressed, with every image packed. Stored with Git LFS. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2160**, step 1 (36.0 s) |
| Camera | One camera, `CAM_Film`, in one continuous move. It uses a Track To constraint on `CAM_Target`, and both are keyed on every frame. There are no camera cuts or camera markers. The lens is animated. DOF is off. |
| Samples | 48 with adaptive sampling, noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 16. Caustics off. Persistent data on. |
| Volumes | Step rate 2.0, max 256 steps. The fire, smoke, steam and dust are procedural volume shaders; there are no caches. |
| World | Camera rays see a keyed sky-blue gradient (`anim_look_v1`): day cyan to white, night deep blue. Lighting comes from three Poly Haven sky HDRIs mixed by keys (noon, dusk and night). |
| Motion blur | Off (the client's animated look, `pipeline/anim_look.py`) |
| Colour | Display sRGB. View AgX with the look "AgX - Punchy" (the animated look of Nov 11, 22:45). **Exposure is keyframed** for the night, the rewind and the detonation flash, so do not override it. |
| Output | PNG, RGB, 8-bit, written to `//render/NukedWell_v004_####.png` |
| Audio | None yet. There is no voiceover for this film. When the VO arrives, retime with `pipeline/retime_to_vo.py` using `beats.json`. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. Embers are keyframed objects. |
| Add-ons | None needed. MPFB2 only built the characters. |

## Test frames before the full job
- **700**: fire column by day, with volume fire, smoke and embers
- **780**: night, lit by the fire only
- **960**: hose crew with water arcs and steam
- **1594**: detonation flash underground, with the blast sphere and point light
- **1760**: the squeezed strata and pinched casing
- **2030**: the crew cheering, a close framing with MPFB skin SSS

If the volumes are noisy at night (frames 740–840), raise the samples to 96 for that range only.

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change the exposure, the world or the sun; all three are animated (day and night, rewind).
