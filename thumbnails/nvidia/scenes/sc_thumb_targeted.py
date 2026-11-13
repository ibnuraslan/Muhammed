"""Thumbnail set: the man in the black leather jacket at a table under one hard light, head bowed, hands at his head;
behind him in the dark, four women standing, dimly side-lit. No likeness is attempted."""
import math
import numpy as np
import bpy
from mathutils import Vector
from kit import *
from human import Human, add_asset, pose_sit, fingers_curl, reach, _world_verts
from people import man

EXPOSURE = 0.0


def _ground(h, z=0.0):
    bpy.context.view_layer.update()
    w = np.concatenate([_world_verts(o) for o in h.parts if o.type == 'MESH'])
    h.arm.location.z += z - w[:, 2].min(); bpy.context.view_layer.update()


def woman_standing(name, loc, rot, hair, suit, skin, years):
    h = Human(name, gender=0.0, years=years, muscle=0.45, weight=0.4, height=0.5,
              skin=skin, eyebrows="eyebrow001", eyelashes="eyelashes01")
    add_asset(h, "clothes", suit, hue=0.5, sat=0.1, val=0.09, rough=0.6, sheen=0.3)
    add_asset(h, "clothes", "shoes02", val=0.2, rough=0.3)
    add_asset(h, "hair", hair, val=0.3, rough=0.4)
    for sd, sg in (("L", 1), ("R", -1)):
        h.aim(f"upperarm01.{sd}", (0.16 * sg, 0.02, -1)); h.aim(f"upperarm02.{sd}", (0.16 * sg, 0.02, -1))
        h.aim(f"lowerarm01.{sd}", (0.06 * sg, -0.12, -1)); h.aim(f"lowerarm02.{sd}", (0.06 * sg, -0.12, -1))
        h.aim(f"wrist.{sd}", (0.02 * sg, -0.05, -1))
    fingers_curl(h, 20)
    h.arm.location = loc; h.arm.rotation_euler = (0, 0, rot)
    _ground(h)
    return h


def _recolor(h, tag, base, rough=None, coat=None):
    """Solid colour on one clothing asset (keeps its normal map / folds)."""
    for o in h.parts:
        for m in (o.data.materials if o.data else []):
            if m and tag in m.name:
                pb = m.node_tree.nodes["Principled BSDF"]
                for l in list(m.node_tree.links):
                    if l.to_socket == pb.inputs['Base Color']:
                        m.node_tree.links.remove(l)
                pb.inputs['Base Color'].default_value = (*base, 1)
                if rough is not None: pb.inputs['Roughness'].default_value = rough
                if coat is not None: pb.inputs['Coat Weight'].default_value = coat


def build(variant=None):
    import sc_boardroom
    ctx0 = sc_boardroom.build(None)                  # the film's boardroom: walnut table, glass wall, night city
    for o in bpy.data.objects:
        if o.name.startswith("Chair") or o.name in ("Folder", "Paper"):
            o.hide_render = True
    for m in bpy.data.materials:                     # dim the city so it stays a soft background
        if m.name.startswith(("Windows", "Streets")) and m.node_tree:
            p = m.node_tree.nodes.get("Principled BSDF")
            for l in m.node_tree.links:
                if p and l.to_socket == p.inputs['Emission Strength']:
                    l.from_node.inputs[1].default_value *= 0.22
    bpy.data.objects["Over"].data.energy = 18
    TABLE_END = 3.0                                  # the head end of the table (y), top at z = 0.77
    TOP = 0.77
    # the man at the head of the table, facing down it (-Y): seated at a normal height, leaning in, elbows on the table
    h = man()
    for o in h.parts:
        for m in o.data.materials:
            if m and "casualsuit05" in m.name:
                pb = m.node_tree.nodes["Principled BSDF"]
                for l in list(m.node_tree.links):
                    if l.to_socket == pb.inputs['Base Color']:
                        m.node_tree.links.remove(l)
                pb.inputs['Base Color'].default_value = (0.005, 0.005, 0.0055, 1)
                pb.inputs['Coat Weight'].default_value = 0.25; pb.inputs['Coat Roughness'].default_value = 0.18
                pb.inputs['Roughness'].default_value = 0.55; pb.inputs['Specular IOR Level'].default_value = 0.08
    pose_sit(h, lean=46)
    h.rot("neck01", (1, 0, 0), -8); h.rot("head", (1, 0, 0), -16)
    h.arm.location = (0, TABLE_END + 0.55, 0.0); bpy.context.view_layer.update()
    _ground(h, 0.0)                                  # feet on the floor: a normal seated height
    hd = h.bone_head("head"); ht = h.bone_tail("head")
    c = hd + (ht - hd) * 0.38
    for sd, sg in (("L", 1), ("R", -1)):
        reach(h, sd, c + Vector((0.088 * sg, 0.035, 0.0)), (0.15 * sg, -0.35, -1.0), hand_dir=(-0.5 * sg, 0.2, 0.85))
    fingers_curl(h, 32, thumb=5)
    bpy.context.view_layer.update()
    el = (h.bone_tail("upperarm02.L") + h.bone_tail("upperarm02.R")) / 2
    # slide him so the elbows are just over the table's end; then set the table so its top meets the sleeves
    h.arm.location.y += (TABLE_END - 0.22) - el.y; bpy.context.view_layer.update()
    el = (h.bone_tail("upperarm02.L") + h.bone_tail("upperarm02.R")) / 2
    top = el.z - 0.045
    print("[pose] elbow z", round(el.z, 3), "table top ->", round(top, 3), flush=True)
    dz = top - TOP
    for n in ("Table", "Pedestal", "Pedestal.001"):
        if n in bpy.data.objects:
            bpy.data.objects[n].location.z += dz
    c = hd + (ht - hd) * 0.38
    c = (h.bone_head("head") + (h.bone_tail("head") - h.bone_head("head")) * 0.38)
    # a chair behind him (scanned leather chair), mostly hidden by his body
    import ph
    ph.model("mid_century_lounge_chair", loc=(0, h.arm.location.y + 0.32, 0), rot_z=0.0)
    # four women behind him, between him and the glass, each dressed differently
    W = [((-1.15, 4.35, 0), 0.22, "long01", "female_elegantsuit01", "middleage_lightskinned_female_diffuse.png", 38, (0.09, 0.012, 0.018)),
         ((-0.42, 4.75, 0), 0.07, "bob02", "male_elegantsuit01", "young_lightskinned_female_diffuse.png", 31, (0.05, 0.05, 0.055)),
         ((0.45, 4.8, 0), -0.07, "ponytail01", "female_elegantsuit01", "middleage_lightskinned_female_diffuse2.png", 44, (0.012, 0.03, 0.06)),
         ((1.2, 4.4, 0), -0.22, "braid01", "male_elegantsuit01", "young_lightskinned_female_diffuse3.png", 34, (0.16, 0.11, 0.07))]
    women = []
    for k, (loc, rot, hair, suit, skin, yrs, col) in enumerate(W):
        w = woman_standing(f"W{k}", loc, rot, hair, suit, skin, yrs)
        _recolor(w, suit, col, rough=0.55)
        women.append(w)
    def spot(n, loc, tgt, e, col, deg, blend, soft):
        l = bpy.data.lights.new(n, 'SPOT'); l.energy = e; l.color = col; l.spot_size = math.radians(deg)
        l.spot_blend = blend; l.shadow_soft_size = soft
        o = bpy.data.objects.new(n, l); bpy.context.collection.objects.link(o); o.location = loc; point_at(o, tgt); return o
    hy = h.arm.location.y
    spot("Key", (0.35, hy - 0.4, 2.9), (0, hy - 0.2, 1.0), 700, (1.0, 0.93, 0.84), 26, 0.4, 0.08)
    spot("Face", c + Vector((0.55, -1.2, 0.05)), c, 70, (1.0, 0.9, 0.8), 14, 0.6, 0.15)   # side light: half his face
    spot("WomenSide", (-3.0, 4.2, 2.4), (0, 4.6, 1.4), 260, (0.62, 0.72, 0.9), 34, 0.7, 0.3)
    spot("WomenSide2", (3.0, 4.3, 2.2), (0.6, 4.7, 1.4), 90, (0.62, 0.72, 0.9), 34, 0.7, 0.3)
    # the accelerator module on the table in front of him: the one lime accent (its own small lime glow)
    from sc_gpu_module import build_module
    before = set(bpy.data.objects)
    build_module((0, 0, 0))
    mod = [o for o in bpy.data.objects if o not in before and o.parent is None]
    root = bpy.data.objects.new("Module", None); bpy.context.collection.objects.link(root)
    for o in mod:
        o.parent = root
    root.location = (0.05, TABLE_END - 0.62, top + 0.0); root.rotation_euler = (0, 0, math.radians(-12)); root.scale = (1.6, 1.6, 1.6)
    spot("LimeGlow", (0.05, TABLE_END - 0.95, top + 0.5), (0.05, TABLE_END - 0.62, top), 18, (0.88, 0.97, 0.0), 14, 0.5, 0.02)
    people = [o for hh in [h] + women for o in hh.parts]
    return dict(h=h, women=women, head=c, people=people, top=top)


MOVES = {"front": dict(kind="plate", cam=lambda c, t: ((0, -3.6, 1.55), (0, 1.0, 1.25), 40))}
