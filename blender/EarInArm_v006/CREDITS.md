# EarInArm_v006: credits

## Required attribution (CC BY 4.0)
Paste this block into the video description:

```
3D models (CC BY 4.0, via Sketchfab):
Human Ear Model by ssavish274 · Thorax by Team Skeleton Wars · Scalpel - Bisturi by centronina3d ·
Operating room lamps by House Doctor · Metal Tray by Silver Shield ·
IV Stand and Bag by Somar52 · Doctors Chair by Giimann
```

| Asset | Author | Source |
|---|---|---|
| Human Ear Model | ssavish274 | https://sketchfab.com/3d-models/e1f0f4b6fae54d59bdc3c6b2534eb411 |
| Thorax | Team Skeleton Wars | https://sketchfab.com/3d-models/83d435a04aa945898161eae1a2a9cf04 |
| Scalpel - Bisturi | centronina3d | https://sketchfab.com/3d-models/8e1d854692234e50b927e2383d0ae520 |
| Operating room lamps | House Doctor | https://sketchfab.com/3d-models/04a8ddf6e47141289ce0372e9e842167 |
| Metal Tray | Silver Shield | https://sketchfab.com/3d-models/baf3242c524f4e4483d7f6df5f0d9848 |
| IV Stand and Bag | Somar52 | https://sketchfab.com/3d-models/a93a8e70ecd2459c99e7812c6e09b88c |
| Doctors Chair (stool) | Giimann | https://sketchfab.com/3d-models/6b8335348bc74cd3b560047940048572 |

All of these came through Objaverse (allenai/objaverse on Hugging Face). Our changes:
- The ear was re-materialled as cartilage and as skin, and scaled.
- The thorax was re-materialled as bone and rotated. Its costal-cartilage mesh keeps a cartilage material, and one piece of it is cut out as the harvested cartilage.

## CC0 assets (no attribution required; listed for provenance)
| Asset | Author | Source |
|---|---|---|
| HDRI: Surgery | Oliksiy Yakovlyev | polyhaven.com |
| Floor Tiles 02 | Rob Tuytel | polyhaven.com |
| Grey Plaster | Rob Tuytel | polyhaven.com |
| Stretch Poplin (scrubs weave) | colormass, Rico Cilliers | polyhaven.com |
| Leather White (chair vinyl) | Rob Tuytel | polyhaven.com |
| Patient, surgeon (two instances), nurse: base mesh, rig, skins, hair, clothes, eyes, teeth, expression targets | MakeHuman community | MakeHuman system assets (CC0), built with MPFB2 |

The MakeHuman tee texture had a printed logo, so a cleaned copy (`EarInArm_v001/assets/tee_plain_diffuse.png`) is used instead.
- Every other prop is procedural and was built in our scripts: the chair, arm board, trolley, monitor, IV stand, forceps, needle holder, stitches, vessels, cartilage block, skin pocket and studio cycloramas.

## Voiceover
None yet. When the client's mp3 arrives, retime with `blender/pipeline/retime_to_vo.py` using `EarInArm_v001/beats.json`.
