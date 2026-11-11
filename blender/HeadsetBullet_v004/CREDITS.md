# HeadsetBullet_v004: credits

## Required attribution (CC BY 4.0)
Paste this block into the video description:

```
3D models (CC BY 4.0, via Sketchfab):
Gaming Chair by Vashishtha Dubey · Computer Monitor Lowpoly Model by Marco Zakaria ·
RGB Keyboard and Mouse by LeyJames · Sedan car covered with a gray car cloth 3D scan by Alben Tan ·
GAMING PC FREE DOWNLOAD by Fred Drabble · Soda can by Ya · Single wooden bed by franckross ·
Simple Mailbox by Blender3D · Surburban Starter House by novusod · Wheeler House by Sea Land Air
```

| Asset | Author | Source |
|---|---|---|
| Gaming Chair | Vashishtha Dubey | https://sketchfab.com/3d-models/7f0c2f402d90406dacfb0cdf90dbe0f5 |
| Computer Monitor Lowpoly Model (screen replaced with our own panning landscape) | Marco Zakaria | https://sketchfab.com/3d-models/1d4ee42eda804b02b05b63721921c1d7 |
| RGB Keyboard and Mouse | LeyJames | https://sketchfab.com/3d-models/df00ce3e66dc4b75a5f9b49c2e6b1406 |
| Sedan car covered with a gray car cloth 3D scan | Alben Tan | https://sketchfab.com/3d-models/5818270ead0649498ab6120604b19f7f |
| GAMING PC FREE DOWNLOAD | Fred Drabble | https://sketchfab.com/3d-models/dbf9c15333814afa88345312b521ddab |
| Soda can (plain aluminium; repainted, no label) | Ya | https://sketchfab.com/3d-models/f28f781755a84a4e83e56e36d06c624f |
| Single wooden bed | franckross | https://sketchfab.com/3d-models/c7bea79b8c7a4b7c9ec5eadfa2529b9a |
| Simple Mailbox | Blender3D | https://sketchfab.com/3d-models/d3768223323e4462bbe6c048c9b400ab |
| Surburban Starter House (neighbour) | novusod | https://sketchfab.com/3d-models/13a17971271d402886c164628afd50c7 |
| Wheeler House (neighbour) | Sea Land Air | https://sketchfab.com/3d-models/b9ec496c621346d7ba66f555a09ab8a7 |

All of these were obtained through Objaverse (allenai/objaverse on Hugging Face) with `pipeline/find_models.py`. None carries a logo; we checked each in a turntable render. A second chair we downloaded had a brand logo, so we did not use it.

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
| Metal Office Desk | Poly Haven | polyhaven.com |
| Modern Ceiling Lamp 01, Carved Wooden Elephant, Wooden Candlestick, Brass Candleholders | Poly Haven artists (see polyhaven.com) | polyhaven.com |
| Dirty Carpet (rug) | Rohit Seervi | polyhaven.com |
| The teen: base mesh, rig, skin, short hair, tee and jeans, shoes, eyes, brows | MakeHuman community | MakeHuman system assets (CC0), built with MPFB2. The print/logo was removed from the tee texture by `scripts/00_plain_shirt.py`. |

## Made in our scripts (no third-party assets)
The bullet (a plain copper projectile only: no cartridge and no weapon), the headset (kept procedural so it can crack and be cut away) (shell, foam padding, steel frame ring and yoke, cushions, RGB rings, and a band with a bend shape key), the house shell and room, the window and its 183 glass shards, the crack shader, debris, sparks, dust, bullet hole, posters and the framed print (abstract procedural art with no text), birds, sprinkler, leaves, fence and the wall shelves.

## Voiceover
None yet. We built the film to the brief's target beat times. When the client's mp3 arrives, retime it with `pipeline/retime_to_vo.py` using `beats.json`.
