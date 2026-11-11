# RingBullet: work folder (v001)

A 23.5 s vertical true-story short (1080×1920, 60 fps, frames 1–1410). A robber fires at a man's head. The man throws his hands up and the bullet hits his wedding ring, glances off and splits in two. One fragment lodges in his finger and the other grazes his neck. He walks away with a dented ring, a bandage and a plaster.

There is **one camera** (`Cam`) on one continuous spline and no cuts. The beat start frames are in `beats.json`.

## Rebuild from scratch
```
blender -b --python scripts/01_build_humans.py -- humans.blend          # MPFB2 owner + robber
blender -b humans.blend --python scripts/02_build_scene.py -- scene.blend # set, props, lights, hero props, FX objects
blender -b scene.blend --python scripts/03_animate.py -- anim.blend       # IK rigs, acting, face, walk, ring/bandage fitting
blender -b anim.blend --python scripts/03b_fx_camera.py -- film.blend     # bullet, fragments, sparks, slow-mo world time, police lights, camera, beats.json
blender -b film.blend --python scripts/audit.py -- review/audit.txt 5     # contact / safety audit
blender -b film.blend --python ../pipeline/stills.py -- <dir> 0.2         # review stills
blender -b film.blend --python scripts/clip_closeups.py -- <dir>          # clipping close-ups at contact moments
```
Assets are fetched with `../pipeline/fetch_polyhaven.py` into `assets/`, which is ignored by git. The full list is in `CREDITS.md`.

## How the tricky parts work
- **Slow motion** is a keyed world-time property, `TimeCtl["wt"]`, that runs at real speed until frame 30, at 0.06× from frame 45 to 1000, then at real speed again. It drives the rain, dust, window drops, pendulum, wall-clock ticks, sparks and the ejected casing.
- **The bullet** is real size (9 mm). Its travel is a time-ramped position along the muzzle-to-ring line. The camera locks to it per frame in two windows: the ride at 1.25–2.95 s and the rack-focus macro at 6.6–7.4 s.
- **Ring fit:** the band is fitted to the finger's own skin vertices (by vertex group). Two more measures keep it from intersecting:
  - a vertex-group Displace "ring seat" presses the skin about 2 mm under the band
  - the middle finger and pinky are splayed a little off the band
- **Dent:** a shape key dents the outer surface only, so the band never cuts into the finger.
- **Injuries** are small, matte, dark marks with no blood. The bandage and the neck plaster swap in during the police-light flare at frame 1244.
- **Sensitive rules:** the robber is only seen from behind, the pistol is a detail-free silhouette, and the audit flags any frame where the gun is aimed at camera while in frame.

## Known issues
- In the macro frames (8–9 s, 13 s), skin fills most of the frame, with pore and normal detail.
- The bandaged hand is mostly hidden in the walk-out wide. The bandage reads at 20.8–21.2 s, before he turns.
