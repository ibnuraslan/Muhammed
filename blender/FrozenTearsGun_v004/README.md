# FrozenTearsGun_v004: farm package

This supersedes v002. It is the full 35.0 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `FrozenTearsGun_v004_60fps.blend` (69 MB, compressed, normal git file, no LFS): the self-contained scene. Every texture is packed. It opens and renders in factory-startup Blender 5.2.2.
- `SETTINGS.md`: render settings and test frames.
- `CREDITS.md`: all assets are CC0, so no attribution is required.
- `package_check_f1420_lowres.png`: a 20 %, 4-sample frame rendered from the packed file in factory Blender. It shows the package works; it is not a quality reference.

## Source and rebuild
The source is `../FrozenTearsGun_v001/`: `PLAN.md`, `beats.json` and `scripts/`.

To rebuild, run `scripts/build_all.sh` from that folder. It runs:
1. `01_build_humans.py`: MPFB2
2. `02_build_scene.py`: sets, the procedural gun and props, lights, render settings
3. `03_animate.py`: all animation and the camera

Then run `scripts/shrink_for_farm.py` (textures to 1K, 2K for her face skin, a 1K HDRI, opaque maps re-encoded to JPEG, orphans purged), and package with `pipeline/package_for_farm.py`. The review tools are `scripts/stills_at.py`, `scripts/audit.py` and `scripts/camera_path_dump.py` / `camera_path_plot.py`.

## Voiceover
No VO was supplied. The film is built to the target beat times in `beats.json` (13 beats; frame = 1 + round(t × 60)). When the VO arrives:
1. Get word times with `pipeline/transcribe.py`.
2. Write the anchors (old frame from `beats.json` → second of each beat's first word).
3. Run `pipeline/retime_to_vo.py`. It warps every keyframe, including the camera and the exposure flashes, and lays the VO strip at frame 1.

## Changes since v002
- **Mentor's finale arms.** A natural brace replaces the T-pose: elbows bent, palms open, chin tucked. On the hit he flinches, then laughs and pats his chest.
- **Lecture.** He slaps the desk at 21 s and the papers jump. The camera drops into a low-angle push-in on him at 20.4 s.
- **Office dressing.** A city view outside the window (a cropped Poly Haven HDRI), a desk lamp with warm light, a second bookshelf and more books.
- **Realism pass.** The CO2 canister is now a lathed shape with a brushed finish; the workshop door is panelled with a knob; the pegboard has holes; the posters carry a blueprint grid. Box props are bevelled.
- **Clipping fixes.**
  - The funnel sits 16 mm off the cheek, and is still bone-parented to the head.
  - Grip fingers no longer sink into the wood.
  - The left hand arcs around the gun on its way to the valve.
  - The T-shirt and suit are pushed 3 mm out, so skin no longer pokes through at the shoulders.
  - At 25.4 s the camera no longer passes through her ponytail.
- **Audit** (`../FrozenTearsGun_v001/review/audit_v004.txt`, every 3 frames):
  - feet and camera clean
  - funnel 0 vertices inside the face
  - 3 single-frame fingertip contacts with gun parts (frames 340, 466 and 910, worst 9 mm, during fast hand moves)

## Known issues
- **Render cost.** The CO2 gas frames (about 7.4–12.6 s) are the most expensive, because of the small volume spheres seen through glass. A full gas frame (560) took 936 s (about 15.6 min) on this 4-core CPU, against an estimated 5–7 min for a typical frame. Test on the farm first (see SETTINGS.md).
- **Time-lapse (28.3–31.2 s).** Her pose snaps between three working poses on purpose (sketch, file at the vice, assemble), with no walking in between.
- **Crying face.** It uses the default rig's face bones (lids, brows, mouth corners, jaw). The ARKit expression pack isn't installed, so it is subtle rather than fully sculpted.
- **Hands and fingers.**
  - The fingers on the gun grip and the valve wheel are posed procedurally. They read correctly in the macro shots, but are not individually sculpted around every surface.
  - At the valve, one chamber drop sits 0.2 mm inside a fingertip at frame 349, which is not visible.
- **Mentor in the office (19.4–21 s).** The camera now drops into a low-angle push-in on him at 20.4 s.
- **Explainer backdrop.** This is the cyan gradient card behind the gun from 4.5 to 15 s. It sits just behind the gun, so the edge of the workbench shows in front of it in a few valve frames (6–7 s).
