# HeadsetBullet_v002: credits

## Required attribution (CC BY 4.0)
Paste this block into the video description:

```
3D models (CC BY 4.0, via Sketchfab):
Gaming Chair by Vashishtha Dubey · Computer Monitor Lowpoly Model by Marco Zakaria ·
RGB Keyboard and Mouse by LeyJames
```

| Asset | Author | Source |
|---|---|---|
| Gaming Chair | Vashishtha Dubey | https://sketchfab.com/3d-models/7f0c2f402d90406dacfb0cdf90dbe0f5 |
| Computer Monitor Lowpoly Model (screen replaced with our own panning landscape) | Marco Zakaria | https://sketchfab.com/3d-models/1d4ee42eda804b02b05b63721921c1d7 |
| RGB Keyboard and Mouse | LeyJames | https://sketchfab.com/3d-models/df00ce3e66dc4b75a5f9b49c2e6b1406 |

All three were obtained through Objaverse (allenai/objaverse on Hugging Face) with `pipeline/find_models.py`. None carries a logo; we checked each in a turntable render. A second chair we downloaded had a brand logo, so we did not use it.

## CC0 assets (no attribution required; listed for provenance)
| Asset | Author | Source |
|---|---|---|
| HDRI: Kloofendal 48d Partly Cloudy (Pure Sky); also the panorama on the monitor | Greg Zaal, Jarod Guest | polyhaven.com |
| Clay Roof Tiles | Amal Kumar | polyhaven.com |
| Painted Plaster Wall (exterior and room walls) | Amal Kumar | polyhaven.com |
| White Plaster 02 (ceiling) | Rob Tuytel | polyhaven.com |
| Laminate Floor 02 | Dario Barresi, Charlotte Baglioni | polyhaven.com |
| Leafy Grass (lawn) | Charlotte Baglioni | polyhaven.com |
| Asphalt 02 | Rob Tuytel | polyhaven.com |
| Concrete Floor 02 (sidewalk, path, driveway) | Rob Tuytel | polyhaven.com |
| Tree Small 02 | Rico Cilliers | polyhaven.com |
| Shrub 01, Shrub 02 | Rico Cilliers | polyhaven.com |
| Potted Plant 01 | Rico Cilliers | polyhaven.com |
| Wooden Bookshelf Worn | Ulan Cabanilla | polyhaven.com |
| Desk Lamp Arm 01 | Yann Kervran, Kuutti Siitonen | polyhaven.com |
| The teen: base mesh, rig, skin, short hair, tee and jeans, shoes, eyes, brows | MakeHuman community | MakeHuman system assets (CC0), built with MPFB2. The print/logo was removed from the tee texture by `scripts/00_plain_shirt.py`. |

## Made in our scripts (no third-party assets)
The bullet (a plain copper projectile only: no cartridge and no weapon), the headset (shell, foam padding, steel frame ring and yoke, cushions, RGB rings, and a band with a bend shape key), the house shell and room, the window and its 183 glass shards, the crack shader, debris, sparks, dust, bullet hole, posters (abstract procedural art with no text), birds, sprinkler, leaves, car body, fence, mailbox, desk, PC tower, bed and shelf props.

## Voiceover
None yet. We built the film to the brief's target beat times. When the client's mp3 arrives, retime it with `pipeline/retime_to_vo.py` using `beats.json`.
