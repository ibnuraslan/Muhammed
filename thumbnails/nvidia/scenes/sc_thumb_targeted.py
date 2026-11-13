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


def woman_standing(name, loc, rot, hair, suit, skin, years, stance="relaxed", turn=0.0, tilt=0.0):
    h = Human(name, gender=0.0, years=years, muscle=0.45, weight=0.4, height=0.5,
              skin=skin, eyebrows="eyebrow001", eyelashes="eyelashes01")
    add_asset(h, "clothes", suit, hue=0.5, sat=0.1, val=0.09, rough=0.6, sheen=0.3)
    add_asset(h, "clothes", "shoes02", val=0.2, rough=0.3)
    add_asset(h, "hair", hair, val=0.3, rough=0.4)
    SL, SR = h.bone_head("upperarm01.L"), h.bone_head("upperarm01.R")
    mid = (SL + SR) / 2
    if stance == "folded":                       # arms folded across the chest, hands tucked under the arms
        c = mid + Vector((0, -0.13, -0.22))
        reach(h, "L", c + Vector((-0.11, 0.0, 0.01)), (0.5, -0.2, -1.0), hand_dir=(-1, 0.25, 0.1))
        reach(h, "R", c + Vector((0.11, -0.04, 0.04)), (-0.5, -0.2, -1.0), hand_dir=(1, 0.25, 0.1))
        fingers_curl(h, 55, thumb=20)
    elif stance == "behind":                     # hands clasped behind her back
        for sd, sg in (("L", 1), ("R", -1)):
            hip = h.bone_head(f"upperleg01.{sd}")
            reach(h, sd, hip + Vector((-0.05 * sg, 0.13, 0.02)), (0.6 * sg, 0.4, -1.0), hand_dir=(-0.6 * sg, 0.3, -0.6))
        fingers_curl(h, 40)
    else:                                        # relaxed: arms down, elbows soft, one hand a little forward
        for sd, sg in (("L", 1), ("R", -1)):
            h.aim(f"upperarm01.{sd}", (0.14 * sg, 0.04, -1)); h.aim(f"upperarm02.{sd}", (0.14 * sg, 0.04, -1))
            fw = -0.35 if sd == "L" else -0.18
            h.aim(f"lowerarm01.{sd}", (0.03 * sg, fw, -1)); h.aim(f"lowerarm02.{sd}", (0.03 * sg, fw, -1))
            h.aim(f"wrist.{sd}", (0.0, fw * 0.6, -1))
        fingers_curl(h, 35, thumb=15)
    # weight on one leg: the other knee eases forward
    h.aim("upperleg01.R", (-0.06, -0.12, -1)); h.aim("upperleg02.R", (-0.06, -0.12, -1))
    h.aim("lowerleg01.R", (-0.04, 0.04, -1)); h.aim("lowerleg02.R", (-0.04, 0.04, -1))
    if turn: h.rot("neck01", (0, 0, 1), turn * 0.4); h.rot("head", (0, 0, 1), turn * 0.6)
    if tilt: h.rot("head", (0, 1, 0), tilt)
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
        if o.name.startswith(("Chair", "GlassWall", "Mullion", "Tower", "CityGround")) or o.name in ("Folder", "Paper"):
            o.hide_render = True
    # a dark wood-panelled office wall, a bookshelf, side walls
    panel = wood("Panel", (0.012, 0.007, 0.004), (0.035, 0.02, 0.011), scale=(0.4, 0.4, 7), rough=0.55, coat=0.0)
    box("BackWall", (0, 5.45, 1.5), (9, 0.06, 3.0), panel)
    for k in range(13):
        box("PanelGroove", (-4.2 + k * 0.7, 5.41, 1.5), (0.012, 0.02, 3.0), pbr("Groove", (0.004, 0.003, 0.002), 0.6))
    box("Wainscot", (0, 5.40, 0.95), (9, 0.04, 0.04), panel)
    dark = pbr("SideWall", (0.02, 0.018, 0.016), 0.8)
    for x in (-3.6, 3.6):
        box("SideWall", (x, 2.5, 1.5), (0.06, 7, 3.0), dark)
    import ph
    for x in (-2.55, 2.55):
        r, ms = ph.model("wooden_bookshelf_worn", loc=(x, 5.2, 0), rot_z=math.pi)
    for m in bpy.data.materials:                     # dim the city so it stays a soft background
        if m.name.startswith(("Windows", "Streets")) and m.node_tree:
            p = m.node_tree.nodes.get("Principled BSDF")
            for l in m.node_tree.links:
                if p and l.to_socket == p.inputs['Emission Strength']:
                    l.from_node.inputs[1].default_value *= 0.22
    bpy.data.objects["Over"].data.energy = 10
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
    for o in h.parts:                            # matte hair: no shiny helmet
        for m in o.data.materials:
            if m and "short02" in m.name:
                pb = m.node_tree.nodes["Principled BSDF"]
                pb.inputs['Roughness'].default_value = 0.85; pb.inputs['Specular IOR Level'].default_value = 0.15
                pb.inputs['Coat Weight'].default_value = 0.0
    pose_sit(h, lean=24)
    h.rot("neck01", (1, 0, 0), 8); h.rot("head", (1, 0, 0), 16); h.rot("head", (0, 1, 0), -10)
    h.arm.location = (0, TABLE_END + 0.55, 0.0); bpy.context.view_layer.update()
    _ground(h, 0.0)                                  # feet on the floor: a normal seated height
    hd = h.bone_head("head"); ht = h.bone_tail("head")
    fwd = Vector((0, -1, 0))
    F = hd + (ht - hd) * 0.42 + fwd * 0.115                  # the forehead
    # right hand: palm flat on the forehead, fingers toward his left temple; elbow down toward the table
    reach(h, "R", F + Vector((-0.085, -0.07, -0.045)), (-0.35, -0.45, -1.0), hand_dir=(1.0, 0.35, 0.5))
    h.rot("wrist.R", (1, 0, 0), 0)
    fingers_curl(h, 22, side=("R",), thumb=8)
    bpy.context.view_layer.update()
    el = h.bone_tail("upperarm02.R")
    h.arm.location.y += (TABLE_END - 0.25) - el.y; bpy.context.view_layer.update()
    el = h.bone_tail("upperarm02.R")
    top = max(0.74, min(0.84, el.z - 0.045))
    print("[pose] elbow z", round(el.z, 3), "table top ->", round(top, 3), flush=True)
    if el.z - 0.045 > top:                                  # sink him a little into the chair if the elbow rides high
        h.arm.location.z -= (el.z - 0.045) - top; bpy.context.view_layer.update()
    dz = top - TOP
    for n in ("Table", "Pedestal", "Pedestal.001"):
        if n in bpy.data.objects:
            bpy.data.objects[n].location.z += dz
    # left forearm lying on the table, hand loosely closed
    SL = h.bone_head("upperarm01.L")
    knee = h.bone_tail("upperleg02.L")
    reach(h, "L", knee + Vector((-0.06, 0.12, 0.08)), (1.0, 0.3, -0.4), hand_dir=(-0.3, -1.0, -0.2))   # left hand rests in his lap, under the table
    fingers_curl(h, 95, side=("L",), thumb=45)
    c = h.bone_head("head") + (h.bone_tail("head") - h.bone_head("head")) * 0.4
    # a chair behind him (scanned leather chair), mostly hidden by his body
    import ph
    ph.model("mid_century_lounge_chair", loc=(0, h.arm.location.y + 0.32, 0), rot_z=0.0)
    # four women behind him, between him and the glass, each dressed differently
    W = [((-1.15, 4.35, 0), 0.22, "long01", "female_elegantsuit01", "middleage_lightskinned_female_diffuse.png", 38, (0.09, 0.012, 0.018)),
         ((-0.42, 4.75, 0), 0.07, "bob02", "male_elegantsuit01", "young_lightskinned_female_diffuse.png", 31, (0.05, 0.05, 0.055)),
         ((0.45, 4.8, 0), -0.07, "ponytail01", "female_elegantsuit01", "middleage_lightskinned_female_diffuse2.png", 44, (0.012, 0.03, 0.06)),
         ((1.2, 4.4, 0), -0.22, "braid01", "male_elegantsuit01", "young_lightskinned_female_diffuse3.png", 34, (0.16, 0.11, 0.07))]
    women = []
    ST = [("behind", 18, 4), ("relaxed", 0, -5), ("behind", -25, 0), ("relaxed", -10, 6)]
    W[1] = ((-0.42, 5.0, 0),) + W[1][1:]          # a step back
    W[2] = (W[2][0], -0.55) + W[2][2:]           # half-turned toward him
    for k, (loc, rot, hair, suit, skin, yrs, col) in enumerate(W):
        st, turn, tilt = ST[k]
        w = woman_standing(f"W{k}", loc, rot, hair, suit, skin, yrs, st, turn, tilt)
        _recolor(w, suit, col, rough=0.9, coat=0.0)
        for o in w.parts:
            for m in (o.data.materials if o.data else []):
                if m and suit in m.name:
                    pb = m.node_tree.nodes['Principled BSDF']; pb.inputs['Specular IOR Level'].default_value = 0.2
                    pb.inputs['Sheen Weight'].default_value = 0.5; pb.inputs['Sheen Roughness'].default_value = 0.5
        women.append(w)
    def spot(n, loc, tgt, e, col, deg, blend, soft):
        l = bpy.data.lights.new(n, 'SPOT'); l.energy = e; l.color = col; l.spot_size = math.radians(deg)
        l.spot_blend = blend; l.shadow_soft_size = soft
        o = bpy.data.objects.new(n, l); bpy.context.collection.objects.link(o); o.location = loc; point_at(o, tgt); return o
    hy = h.arm.location.y
    spot("Key", (0.35, hy - 0.4, 2.9), (0, hy - 0.2, 1.0), 700, (1.0, 0.93, 0.84), 26, 0.4, 0.08)
    spot("Face", c + Vector((0.55, -1.2, 0.05)), c, 70, (1.0, 0.9, 0.8), 14, 0.6, 0.15)   # side light: half his face
    spot("WomenSide", (-3.0, 3.6, 2.2), (0, 4.6, 1.5), 240, (0.75, 0.8, 0.9), 30, 0.7, 0.3)
    spot("WallWash", (1.8, 4.6, 2.9), (1.2, 5.4, 1.2), 160, (1.0, 0.72, 0.45), 40, 0.8, 0.2)
    spot("WallWash2", (-2.0, 4.6, 2.9), (-1.4, 5.4, 1.0), 90, (1.0, 0.72, 0.45), 40, 0.8, 0.2)
    for k, x in enumerate((-2.8, -1.4, 0.0, 1.4, 2.8)):      # wall-washer downlights: warm scallops on the panelling
        spot(f"Scallop{k}", (x, 5.15, 2.96), (x, 5.42, 1.6), 140, (1.0, 0.74, 0.48), 48, 0.85, 0.05)
        box(f"Downlight{k}", (x, 5.15, 2.985), (0.12, 0.12, 0.01), emissive(f"DL{k}", (1.0, 0.85, 0.65), 6.0))
    # a soft cove light where the wall meets the ceiling, so the top of the panelling never goes to pure black
    cv = bpy.data.lights.new("Cove", 'AREA'); cv.shape = 'RECTANGLE'; cv.size = 8.5; cv.size_y = 0.06; cv.energy = 90; cv.color = (1.0, 0.78, 0.55)
    co = bpy.data.objects.new("Cove", cv); bpy.context.collection.objects.link(co); co.location = (0, 5.3, 2.97); co.rotation_euler = (math.radians(-160), 0, 0)
    spot("RimL", (-1.6, 5.3, 2.2), (-0.9, 4.4, 1.5), 110, (1.0, 0.78, 0.55), 30, 0.6, 0.1)
    spot("RimR", (1.7, 5.3, 2.2), (0.9, 4.5, 1.5), 110, (1.0, 0.78, 0.55), 30, 0.6, 0.1)
    # the accelerator module on the table in front of him: the one lime accent (its own small lime glow)
    from sc_gpu_module import build_module
    before = set(bpy.data.objects)
    build_module((0, 0, 0))
    mod = [o for o in bpy.data.objects if o not in before and o.parent is None]
    root = bpy.data.objects.new("Module", None); bpy.context.collection.objects.link(root)
    for o in mod:
        o.parent = root
    root.location = (-0.42, TABLE_END - 0.55, top + 0.0); root.rotation_euler = (0, 0, math.radians(-12)); root.scale = (1.6, 1.6, 1.6)
    spot("LimeGlow", (-0.42, TABLE_END - 0.9, top + 0.5), (-0.42, TABLE_END - 0.55, top), 30, (0.88, 0.97, 0.0), 14, 0.5, 0.02)
    people = [o for hh in [h] + women for o in hh.parts]
    return dict(h=h, women=women, head=c, people=people, top=top)


MOVES = {"front": dict(kind="plate", cam=lambda c, t: ((0, -3.6, 1.55), (0, 1.0, 1.25), 40))}
