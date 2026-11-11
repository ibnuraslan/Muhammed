# SurgeonBrandsLivers_v002 — farm render sheet

These values were read back from `SurgeonBrandsLivers_v002_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `SurgeonBrandsLivers_v002_60fps.blend`: 116 MB, compressed. All 90 images are packed (max 2K; most 1K). There are no linked libraries. Stored as two plain-git parts (LFS host blocked); rejoin with `cat` (see README). |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1710**, step 1 (28.5 s) |
| Camera | One camera, `CAM_Film`, in one continuous move. There are no camera cuts or timeline markers. The lens and the f-stop are animated (macro f/8 in the studio, f/3.2–4 elsewhere). Sensor fit is Auto (36 mm). DOF is on, focused on `CAM_Film_Aim`. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | On, shutter 0.5 (180° at 60 fps). The camera dives and wall fly-throughs rely on it. |
| Colour | Display sRGB. View AgX with the look "AgX - Medium High Contrast". Exposure 0, gamma 1. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/SurgeonBrandsLivers_v002_####.png` |
| Audio | None yet. There is no voiceover. The film is built to the beat-table target times; see `beats.json`. When the VO arrives, retime with `pipeline/retime_to_vo.py`, which swaps in the VO strip. |
| Caches / sims | None: no simulations, particles, Alembic or drivers. Sparks and smoke are keyframed objects. The smoke is six tiny volume puffs (frames 168–324 only). |
| Add-ons | None needed. MPFB2 only built the people. |

## Measured cost
Not measured. Studio rules allow no full-resolution renders here, so the only check is `package_check_f1128_lowres.png`: 20 %, 4 samples, from the packed file in factory Blender, which took about 6 s. For scale, GoatRescue2 took 125 s per full frame on this 4-core CPU. This scene has similar complexity (nine people, closed rooms), so expect about 1.5–2.5 min per frame on CPU, about 60 h for 1710 frames locally. A farm GPU node will be far faster.

Before approving the whole job, run these test frames:
- **220**: studio macro. The pen writes the S, with sparks, smoke volume, a tip light and DOF f/8.
- **540**: close-up of surgeon 1's smirk after the mask comes down: skin SSS, eyes, cap.
- **700**: living room. She doubles over, and the x-ray liver glows through her shirt.
- **1128**: the gloved hands lift the branded liver.
- **1300**: hearing room. The translucent ghost livers are transparent and emissive.
- **1545**: the gavel strike, with motion blur.

If the studio frames (150–300, 1065–1185) are noisy around the smoke, raise samples to 96 for those ranges only.

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not turn off motion blur. Without it, the four ≤0.3 s transit frames (dives into and out of the abdomen, and the wall fly-throughs) read as plain dark frames.
