# Thumbnail: "The Ship That Came Back Without Its Crew"

Blender 5.2 Cycles scenes for the YouTube thumbnail (no text in the image). They reuse `mary_celeste_3d/lib`
(ship, sea, grade) through `scenes/tcommon.py`.

| Concept | Scene | Idea |
|---|---|---|
| (a) | `scenes/thumb_a_ghostship.py` | The Mary Celeste alone, low angle, torn sails, a break in storm cloud, a shaft of light on her empty deck |
| (b) | `scenes/thumb_b_alone.py` | From high above: alone in a pool of light on a black Atlantic; empty deck, empty boat chocks (the yawl is gone) |
| (c) | `scenes/thumb_c_cabin.py` | The cabin table: log slate, lit lantern, Sophia's china doll; the rolling sea through the porthole |

    PREVIEW=0.5 SPP=160 blender -b --python scenes/thumb_a_ghostship.py     # 960x540 preview -> out/
    blender -b --python scenes/thumb_a_ghostship.py                          # 1920x1080 master

Credits: Poly Haven (CC0) skies belfast_sunset_puresky, kloofendal_overcast_puresky, textures dark_wooden_planks,
model wooden_lantern_01. Sketchfab (CC-BY 4.0): "China Doll - toy" by CMBC
(https://sketchfab.com/3d-models/7c6f3f614592486e9124b0d84e1fde08).
