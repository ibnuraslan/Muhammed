# BeethovenDeaf_v009: credits

## Required attribution (CC BY 4.0)
Paste this block into the video description:

```
3D models (CC BY 4.0, via Sketchfab):
Old Wooden Grand Piano by Mikael H. · Human Skull Model (Plastic) by Yu ·
Ear (inner ear, ossicles and eardrum) by osuecampus · Candelabra by AndreiVNK ·
Piano Chair by conn0
```

| Asset | Author | Source | Used for |
|---|---|---|---|
| Old Wooden Grand Piano | Mikael H. | https://sketchfab.com/3d-models/c7c82e2445544191b541f2240ae8c4e7 | The piano. The maker's-name inlay on the fallboard is covered by a plain wood panel. |
| Human Skull Model (Plastic) | Yu | https://sketchfab.com/3d-models/017c6f4a760f40a0a03de8fae29b306b | The X-ray skull |
| Ear | osuecampus | https://sketchfab.com/3d-models/92d3fe7b76214170a59875a5d656d595 | Eardrum, malleus, incus, stapes, labyrinth and cochlea, and nerves. Its label plane and axis cube were removed. |
| Candelabra | AndreiVNK | https://sketchfab.com/3d-models/f00558f1fba44a9698a2df0d9feb0d59 | Three candelabras. The candles are ours. |
| Piano Chair (Free Download) | conn0 | https://sketchfab.com/3d-models/d6c16ede20974098899ad5b370e259d5 | The bench |

All of these were obtained through Objaverse (allenai/objaverse on Hugging Face).

## CC0 assets (no attribution required; listed for provenance)
| Asset | Author | Source |
|---|---|---|
| HDRI: Old Hall | Sergej Majboroda | polyhaven.com |
| Herringbone Parquet | Jenelle van Heerden, Sergej Majboroda | polyhaven.com |
| Plastered Wall 02 | Charlotte Baglioni | polyhaven.com |
| Dark Wooden Planks | Amal Kumar | polyhaven.com |
| Wood Table Worn | Dimitrios Savva, Rico Cilliers | polyhaven.com |
| Velour Velvet | colormass, Rico Cilliers | polyhaven.com |
| Composer: base mesh, rig, old-male skin, hair cap, suit, shoes, eyes, teeth | MakeHuman community | MakeHuman system assets (CC0), built with MPFB2 |

## Made for this film
These were all built procedurally by the scripts in `BeethovenDeaf_v001/scripts`:
- The room shell, panelling, window, curtains, paintings (abstract noise, no imagery) and bookcase.
- The side table, quill, inkwell, candles and flames, and the 88 hinged piano keys that replace the model's fused keys.
- The brass rod and bracket, the cravat, and the particle hair.
- The manuscript pages: generated staves and note heads, with no text or titles.
- The torn-eardrum shader, the rings and pulses, and the studio backdrop.

The composer is a generic MakeHuman face. It is not a likeness of any real person or portrait.

## Voiceover
None has been supplied yet. The film is timed to the brief's target beat times. Once the VO arrives, retime it with `pipeline/retime_to_vo.py` using `BeethovenDeaf_v001/beats.json`.
