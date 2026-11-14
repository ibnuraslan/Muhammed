# NukedWell_v008: farm render sheet

These values are read back from `NukedWell_v008_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `NukedWell_v008_60fps.blend`: compressed, with every image packed. Committed as a normal git file (no LFS). |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1541**, step 1 (25.7 s at 60 fps; synced to the voiceover) |
| Camera | One camera, `CAM_Film`, in one continuous move. It uses a Track To constraint on `CAM_Target`, and both are keyed on every frame. There are no camera cuts or camera markers. The lens is animated. DOF is off. |
| Samples | 48 with adaptive sampling, noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 16. Caustics off. Persistent data on. |
| Volumes | **None.** The fire, smoke, steam and dust are procedural surface shaders on animated cones and spheres (transparent mix, emission or diffuse); they are not volumes and there are no caches. Transparent bounces are 16. |
| World | Camera rays see a keyed sky-blue gradient (`anim_look_v1`): day cyan to white, night deep blue. Lighting comes from three Poly Haven sky HDRIs mixed by keys (noon, dusk and night). |
| Motion blur | Off (the client's animated look, `pipeline/anim_look.py`) |
| Colour | Display sRGB. View AgX with the look "AgX - Punchy" (the animated look of Nov 11, 22:45). **Exposure is keyframed** for the detonation flash, so do not override it. |
| Output | PNG, RGB, 8-bit, written to `//render/NukedWell_v008_####.png` |
| Audio | Your voiceover `NukedWell_v008_VO.mp3` is packed as a sound strip from frame 1; add the mp3 at frame 1 when you encode at 60 fps. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. Embers are keyframed objects. |
| Add-ons | None needed. MPFB2 only built the characters. |

## Test frames before the full job
- **700**: fire column by day, with the surface fire, smoke and embers
- **780**: the fire column behind hose crew A
- **960**: hose crew with water arcs and steam
- **1594**: detonation flash underground, with the blast sphere and point light
- **1760**: the squeezed strata and pinched casing
- **2030**: the crew cheering, a close framing with MPFB skin SSS

**Cost estimate:** f700 takes 12.3 s and f1640 takes 20.0 s at 270×480 with 48 samples on a 4-core CPU, including about 4 s of scene sync per frame. Scaled to 1080×1920, that is roughly **2.3–4.3 min per frame on 4 CPU cores**. This is an extrapolation; no full-resolution frame was rendered. A many-core farm node or a GPU should be several times faster. The volume version cost about 30 s per frame even at 270×480 with 4 samples.

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change the exposure, the world or the sun; all three are animated (day and night, rewind).
