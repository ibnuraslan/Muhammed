# GoatOwner: credits

## Required attribution (CC BY 4.0)
Paste this block into the video description:

```
3D models (CC BY 4.0, via Sketchfab):
Goat by hendrikReyneke · Countryside Home in USA by deerdesign.vn · Backyard Utility Shed by jimbogies · Pile of Old Tires and Abandoned Storage Shed by Abandoned Scans · Funny pickup by kreems · woodfence by pasquill · Wooden Crate by YadroGames · Wood Stick 04 by 3dhdscan
```

| Asset | Author | Source |
|---|---|---|
| Goat | hendrikReyneke | https://sketchfab.com/3d-models/2624ac2ce2364930ba2d5f70eb7aa1ea |
| Countryside Home in USA | deerdesign.vn | https://sketchfab.com/3d-models/6b456f3c136a462ba1b4147dde93df2a |
| Backyard Utility Shed | jimbogies | https://sketchfab.com/3d-models/70154ba65c7d4ba0b5f081fd0eb35f68 |
| Pile of Old Tires and Abandoned Storage Shed | Abandoned Scans | https://sketchfab.com/3d-models/2a28b29867b24980b19aa6b97defc3b2 |
| Funny pickup (stake truck; texture cleaned, see note) | kreems | https://sketchfab.com/3d-models/3bbd05212b314aca83e96158280a6b26 |
| woodfence | pasquill | https://sketchfab.com/3d-models/8fa9a06380df4268b549e345cf103696 |
| Wooden Crate | YadroGames | https://sketchfab.com/3d-models/e12fde1101b84b6da40056336a7b309d |
| Wood Stick 04 (stick, tether post, tape posts, catch pole) | 3dhdscan | https://sketchfab.com/3d-models/b7fe8a4a3c2f4f038662ae47cfbfa6a7 |

All of these were obtained through Objaverse (allenai/objaverse on Hugging Face); the machine-readable list is `objaverse_credits.json`.
- The goat was rigged with `scripts/rig_quadruped.py` (IK hooves); the three pasture goats are copies of it.
- **Truck texture note:** the source texture had a joke logo on the doors, a word on the licence plate and cartoon eyes on the lamps. These were painted out (`scripts/tools/clean_truck_tex.py`), so no text or logo appears on screen.

## CC0 assets (no attribution required; listed for provenance)
| Asset | Author | Source |
|---|---|---|
| HDRI: Kloofendal 48d Partly Cloudy (Pure Sky) | Greg Zaal, Jarod Guest | polyhaven.com |
| Brown Mud Leaves 01 (yard dirt, dust clods) | Rob Tuytel | polyhaven.com |
| Aerial Grass Rock (fields) | Rob Tuytel | polyhaven.com |
| Wood Planks Grey (porch boards, ramp) | Rob Tuytel | polyhaven.com |
| Tree Small 02 | Rico Cilliers | polyhaven.com |
| Grass Medium 01 | Rob Tuytel, Rico Cilliers | polyhaven.com |
| Dry Branches Medium 01 | Rico Cilliers | polyhaven.com |
| Rock Moss Set 01 | Kless Gyzen | polyhaven.com |
| Owner, passer-by, two officials, rescuer: base mesh, rig, skins, hair, clothes, eyes, teeth | MakeHuman community | MakeHuman system assets (CC0), built with MPFB2 |

All characters are generic MakeHuman builds; none is the likeness of a real person.

## Script and voiceover
The narration script is our own wording (see `blender/briefs/32_GoatOwner.md`). The voiceover is to be supplied; `beats.json` is ready for `pipeline/retime_to_vo.py`.
