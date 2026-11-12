"""Review only: the cast side by side in neutral light (costume / age check)."""
import math
import bpy
from mathutils import Vector
from kit import *
import house as H

KINDS = ["philip", "helen", "friend", "neighbour_w", "neighbour_m", "nurse"]
DUR = {"lineup": 1.0}
VARIANT_FOR = {"lineup": "lineup"}


def build(variant=None):
    world_flat((0.5, 0.5, 0.5), 0.8)
    bpy.context.scene.view_settings.exposure = 0.3
    box("Floor", (0, 0, -0.02), (12, 6, 0.04), H.mat("oak"))
    box("Back", (0, 1.5, 1.5), (12, 0.1, 3), H.mat("paper"))
    H.point((0, -2.5, 2.6), 300, (1.0, 0.9, 0.8), 1.0)
    c = {"cast": []}
    for k, kind in enumerate(KINDS):
        h = H.person("C%d" % k, kind); H.stand_at(h, (-2.5 + k, 0, 0), math.radians(0)); c["cast"].append(h)
    return c


DUR["heads"] = 1.0; VARIANT_FOR["heads"] = "lineup"
MOVES = {"heads": dict(kind="anim", dof=None, far=30, anim=lambda c, t: None,
                       cam=lambda c, t: (Vector((0, -3.2, 1.55)), Vector((0, 0, 1.45)), 50)),
         "lineup": dict(kind="anim", dof=None, far=30, anim=lambda c, t: None,
                        cam=lambda c, t: (Vector((0, -6.5, 1.3)), Vector((0, 0, 1.0)), 32))}
