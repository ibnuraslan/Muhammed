# DonationBin_v002: farm package

This is the full 41.5 s film at 1080×1920 and 60 fps, frames 1–2490, ready for RenderStreet. No render has been submitted.

- `DonationBin_v002_60fps.blend`: the self-contained scene. Every texture is packed. It opens in factory-startup Blender 5.2.2 with no add-ons.
- `beats.json`: the start frame of each of the 11 beats at the brief's target times, for `pipeline/retime_to_vo.py` once the voiceover exists.
- `SETTINGS.md`: render settings and suggested test frames. `CREDITS.md`: provenance (everything is CC0 or ours, so no CC-BY block is needed).
- `package_check_lowres.jpg`: a 270×480, 8-sample frame (f2045) rendered from the packed file in factory Blender. It shows the package works; it is not a quality reference.
- `review/`: the 0.2 s polish contact sheets and the contact audit.

**No voiceover yet.** The film is built to the brief's target beat times (frame = 1 + t·60). When the VO arrives:
1. Run `transcribe.py` to get word times.
2. Write anchors from `beats.json`: the old frame, plus the second each beat's first words are spoken.
3. Run `blender -b DonationBin_v002_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 out.blend`.

The source is `../DonationBin_v001/scripts`. Build order: `01_build_humans.py`, then `02_build_scene.py`, then `03_animate.py` (it runs `03b_fx_camera.py`), then `audit.py`, then `04_package_prep.py` (texture trim) and `pipeline/package_for_farm.py`. The assets come from `/opt/assets/ph` (Poly Haven, fetched by `pipeline/fetch_polyhaven.py`) and MPFB2.

## Known issues
- **No VO:** the film is built to the brief's target times, so it needs a retime once the narration exists.
- **Planned fly-throughs:** the camera passes through steel 5 times: into the chute (f268–290), out through the right wall (f500–545), back in (f955–975), out through the flap (f1395–1412) and back in through the slot (f1560–1590). Each lasts 0.2–0.4 s and reads as a dark or solid-colour smear. The x-ray fade makes the f500 pass mostly clean.
- **Finger tips:** they touch the bin walls with up to 4 mm of penetration during the wall pats and the jump (f1177–1303), and when the passer-by knocks (f1925–1957). Not visible at these framings.
- **One foot sink:** 3.1 cm for a single frame at f1167, before the jump crouch.
- **Firefighter A** cuts with his back mostly to camera; the action reads through the sparks, the cutter and the glowing cut line.
- **Simple hand poses:** fingers use a single curl value, so there are no individual finger grips on the cutter or the panel edge.
- **Keyframed acting:** the fall and tumble through the chute are keyed, not simulated. Clothes, bags and the blanket do not simulate either: the bags squash on her landing via scale keys, and the blanket is a skin-following shell.
- **The woman's outfit** is the MPFB `female_sportsuit01` crop top and leggings. The default MPFB tee was rejected because its texture has a logo.
- **Bin row:** the three bins in the final reveal are linked duplicates of the hero bin.
- **Background sign:** the HDRI background contains a generic blue "P" parking sign, with no brand.
