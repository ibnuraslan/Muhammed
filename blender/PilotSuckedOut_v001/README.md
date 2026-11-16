# PilotSuckedOut_v001 (B17): Phase 1 checkpoint (P1)

No VO yet. Shots are provisional-length 1× clips (`scripts/shots.py`); Phase 2 sets the VO frames and re-runs `03_shots.py`.

- `PLAN.md`: shot table, cast, sets, logo, risky-shot staging.
- `review/P1_sheet_540.jpg`: first, middle and last frame of all 23 shots, 540×960, Cycles 8 samples + OIDN.
- `review/bpc.json`, `review/clip.json`: body_prop_cross (B17 copy with window mask + occlusion) and clip_scan results.

Rebuild (all sources are in the repo; the draft .blend is not pushed at P1). 02_sets.py also needs Poly Haven island_tree_01 + shrub_01 (fetch_polyhaven.py /home/user/work17/ph 1k ...):
```
B=/opt/blender/blender-5.2.2-linux-x64/blender
$B -b blender/NoPilotPlane_v011/NoPilotPlane_v011_60fps.blend --python blender/PilotSuckedOut_v001/scripts/01_base.py -- base.blend
$B -b base.blend --python blender/PilotSuckedOut_v001/scripts/02_sets.py -- sets.blend      # needs van.glb (find_models.py get ... van=c07ae5e9ed614152a72acbed1026ffb9)
$B -b sets.blend --python blender/PilotSuckedOut_v001/scripts/03_shots.py -- p1.blend
$B -b p1.blend --python blender/PilotSuckedOut_v001/scripts/shot_frames.py -- frames 540 8
```
Assets reused from READY packages: NoPilotPlane_v011 (cockpit set, captain, first officer, sky/ground), ShoeBomber_v008
(plain-white 737, flight attendant). New: "Low Poly White Van" by AirStudios (CC BY 4.0, Sketchfab via Objaverse).
