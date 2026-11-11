# WaterTubes (Connect33)

A man rings his house with water-filled tubes; the flood hits the barrier and flows around it, and his house stays dry. 33.5 s, 1080×1920 at 60 fps, one continuous camera.

## Folder
- `PLAN.md`: beat table, camera plan, assets, tricky shots (checkpoint A).
- `beats.json`: beat start frames for the VO retime (`pipeline/retime_to_vo.py`).
- `scripts/`: the full build, run in order:
  1. `00_prep_assets.py`: import the CC-BY GLBs, clean them (edge lines, pads, dome, badges) and scale them to real size.
  2. `01_build_people.py`: three MPFB2 characters.
  3. `02_build_set.py`: street, houses, vegetation, the tube ring (GN fill front), the flood surface (GN), the cutaway section, arrows, hose, world and lights.
  4. `03_animate.py`: characters (IK feet and hands, finger grips, face bones), flood timeline, debris, cutaway swaps, explainer, camera.
  5. `04_fx.py`: rain, slam spray and surge spray (deterministic GN, no caches); the licence plate is blanked.
  6. `audit.py`: contact audit (feet hover/sink, shoe/scene overlap, grip gap, camera inside geometry).
  7. `05_package.py`: texture downsizing, purge, pack, then `pipeline/package_for_farm.py`.
- `assets/`: the patched no-print shirt textures and the Sketchfab credits JSON.
- `stills/`: review sheets (B: 1 per s, C: every 0.2 s) and the camera path.

## Rebuild
```
S=<scratch>   # holds models/ (find_models.py get ...), ph/ (fetch_polyhaven.py ...), assets.blend, people.blend
blender -b --factory-startup --python 00_prep_assets.py -- $S/models $S/assets.blend
blender -b --python 01_build_people.py -- $S/people.blend
blender -b --factory-startup --python 02_build_set.py -- $S $S/set.blend
blender -b $S/set.blend --python 03_animate.py -- $S/people.blend $S/anim.blend
blender -b $S/anim.blend --python 04_fx.py -- $S/fx.blend
blender -b $S/fx.blend --python 05_package.py -- ../WaterTubes_v002/WaterTubes_v002_60fps.blend
```
