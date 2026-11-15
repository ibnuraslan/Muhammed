# LincolnAssassination_v001: Phase 1 (pre-VO build)

Status: **Phase 1 checkpoint, not a delivery.** Timing is the reference pacing +30% (2214 frames); Phase 2 retimes by
editing `scripts/timing.py` to the VO beat frames and rebuilding (no time-stretch).

- `PLAN.md`: shots, staging, logo placement, risky-shot staging.
- `LincolnAssassination_v001_P1_60fps.blend`: the Phase-1 scene (textures packed, compressed, factory-startup clean). 1080×1920, 60 fps, Cycles, frames 1–2214, one camera per shot bound by markers.
- `review/P1b_stills_3perShot_540x960.jpg`: first / middle / last frame of every shot at 540×960, Cycles 8 samples.
- `review/P1b_body_prop_cross.txt`: body_prop_cross result (every 6th frame) on every held or touched prop.
- `review/model_credits.json`: Sketchfab/Objaverse CC-BY credits for the downloaded models.

## Rebuild
Models: `pipeline/find_models.py get` with the UIDs in `review/model_credits.json` into `$B04_GLB`; textures:
`pipeline/fetch_polyhaven.py $B04_PH 1k brown_planks_05 brown_planks_09 cobblestone_floor_08 wood_floor_deck`.
```
blender -b --factory-startup --python scripts/01_chars.py -- chars.blend   # cast from WW1Assassination_v007
blender -b chars.blend --python scripts/02_sets.py -- sets.blend
blender -b sets.blend  --python scripts/03_anim.py -- anim.blend
blender -b anim.blend  --python scripts/shot_stills.py -- out_dir mid 540 8
```

## Credits (CC0 / CC-BY)
Poly Haven (CC0): Brown Planks 05/09, Cobblestone Floor 08 (Rob Tuytel), Wood Floor Deck (Dimitrios Savva).
Sketchfab CC-BY: Flintlock pistol (Cyril43), Top Hat (Robin Butler), Victorian armchair, hay bale, wooden crate, Medieval torch (vadim92.34; not used on screen),
Old English Street Lamp (rhcreations), Lavenham Half-timbered House / Troyes House 2 / Angers Shop 1 (Lost Gecko), Curtains (daedaljs). Full list with authors and links in `review/model_credits.json`.
Characters and horse: our WW1Assassination_v007 package (MPFB2 / MakeHuman CC0; horse CC-BY as credited there).
