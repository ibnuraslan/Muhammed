# GoatOwner_v001: working folder (Connect32)

This folder holds the source scripts, the plan, the beat timings and the review sheets for the GoatOwner film. The film is 36.5 s long, 1080×1920 at 60 fps, frames 1–2190, shot with one continuous camera. The farm package is in `../GoatOwner_v002/`.

| File | What |
|---|---|
| `PLAN.md` | Checkpoint A: beat table, camera plan, assets, tricky shots |
| `beats.json` | Beat start frames and first words, ready for `pipeline/retime_to_vo.py` once the VO arrives |
| `CREDITS.md`, `objaverse_credits.json` | CC-BY block for the video description, plus CC0 provenance |
| `review/` | B 1/s sheet, camera path, C 0.2 s sheets, contact close-ups and audit reports |
| `scripts/` | The full build, described below |

## Build order (`scripts/05_package.sh` runs all of it)
1. `rig_quadruped.py`: rigs the CC-BY goat GLB with IK hooves.
2. `01_build_humans.py`: builds 5 MPFB2 humans (owner, passer-by, two officials, rescuer).
3. `02_build_scene.py`: render settings, sky, ground, farmhouse, porch, shed, truck, ramp, tape, trees, grass, dust pool and the camera.
4. `03_animate.py`: all character, prop, dust, light and camera animation.
5. `04_shrink.py`: textures down to ≤1K (JPEG unless alpha) so the package stays under 95 MB with no LFS.
6. `pipeline/package_for_farm.py`: packs everything and saves compressed.

Run `audit.py` for the contact/penetration audit and `contact_closeups.py` for the clipping-check stills.

Assets come from `pipeline/fetch_polyhaven.py` (CC0) and `pipeline/find_models.py` (CC-BY via Objaverse).
- The truck's base-colour texture is cleaned with `scripts/tools/clean_truck_tex.py`. It removes a joke logo, a plate word and cartoon eyes.
- The cleaned copy is saved as `objv/truck_base_clean.png`.

## Sensitive content handling (brief)
- **Abuse:** shown only as the raised stick, the goat flinching and backing away on its rope, and his shadow. There is no downswing and no contact.
- **Attack:** a slow-motion charge to his midsection with a dust burst; he doubles over. No blood or wounds.
- **Death:** he falls from the porch and lies still, face down, seen from a distance as the camera cranes away.
