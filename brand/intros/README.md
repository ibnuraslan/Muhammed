# Seldom channel intros, concept round

- `seldom_intro_concepts.pdf`: page 1 has the 8 intro concepts (idea, key frame, sound note). Page 2 has the viewer-discretion opener (3 scripts, 3 ways to present it) and a note on the earlier intros.
- `keyframes/`: the concept renders, 1600x900 Cycles. The final intros will render at 2560x1440, 24 fps.
- `scenes/`: Blender 5.2 scripts, one per concept (`c1`..`c8`, plus `c9_telegram` for the discretion card). `logo_polys.json` is `brand/seldom_logo.png` traced into polygons (by `trace.py`), so the logo is a real extruded 3D object.
  Render with: `blender -b -P scenes/c1_searchlight.py -- out.png <samples>`

Nothing is animated yet. That waits for the pick.
