"""The heist crew for the Antwerp thumbnail: a rigged CC-BY man (Sketchfab "Eric Rigged 001", renderpeople) posed in
code into a crouched, sneaking walk with a heavy bag in one hand. Seen only as backlit silhouettes (no faces).
Poses are given as world-axis rotations per bone (character faces -Y in its own space), so they do not depend on
the rig's local bone axes."""
import math
import bpy
import numpy as np
from mathutils import Vector, Matrix
import sf

ERIC = "a46bc9f67aaa415bb4f3241eef900e7f"
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def _rot(arm, bone, axis, deg):
    """Rotate a pose bone about a world-space axis through its head (applied on top of its current pose)."""
    pb = arm.pose.bones[bone]
    bpy.context.view_layer.update()
    mw = arm.matrix_world
    head_w = mw @ pb.head
    R = Matrix.Translation(head_w) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-head_w)
    pb.matrix = mw.inverted() @ R @ mw @ pb.matrix
    bpy.context.view_layer.update()


SNEAK = [  # a natural sneaking walk: knees soft, back bent, head up, bag hand low, free arm out for balance
    ("spine_01_03", X, 20), ("spine_02_04", X, 12), ("spine_03_05", X, 6), ("neck_06", X, -18), ("head_07", X, -10),
    ("upperleg_l_074", X, -48), ("lowerleg_l_075", X, 62), ("foot_l_076", X, -12),
    ("upperleg_r_081", X, 12), ("lowerleg_r_082", X, 48), ("foot_r_083", X, -22),
    ("upperarm_r_049", Y, -40), ("upperarm_r_049", X, -6), ("lowerarm_r_050", X, -6),
    ("upperarm_l_024", Y, 30), ("upperarm_l_024", X, -30), ("lowerarm_l_025", X, -35),
]

CROUCH = [  # (bone, world axis, degrees): a low sneaking stride, left leg forward, right hand low with the bag
    ("spine_01_03", X, 26), ("spine_02_04", X, 16), ("spine_03_05", X, 8), ("neck_06", X, -28), ("head_07", X, -14),
    ("upperleg_l_074", X, -72), ("lowerleg_l_075", X, 100), ("foot_l_076", X, -25),
    ("upperleg_r_081", X, 8), ("lowerleg_r_082", X, 72), ("foot_r_083", X, -30),
    ("upperarm_r_049", Y, -42), ("upperarm_r_049", X, -20), ("lowerarm_r_050", X, -8),
    ("upperarm_l_024", Y, 40), ("upperarm_l_024", X, -60), ("lowerarm_l_025", X, -30),
]


def load_template():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=sf.fetch(ERIC))
    new = [o for o in bpy.data.objects if o not in before]
    arm = [o for o in new if o.type == 'ARMATURE'][0]
    return arm, new


def thief(loc, heading_deg, pose=SNEAK, jitter=0.0, seed=0, mat=None, name="thief"):
    """Import a fresh copy, pose it, scale to 1.82 m, set it down at loc (feet on z = loc.z), turn to heading."""
    import random
    rng = random.Random(seed)
    arm, objs = load_template()
    for o in [o for o in objs if o.name.startswith("Icosphere")]:
        objs.remove(o); bpy.data.objects.remove(o)
    root = [o for o in objs if o.parent is None and o.name.startswith("Sketchfab_model")][0]
    bpy.context.view_layer.update()
    for (b, ax, d) in pose:
        if b in arm.pose.bones:
            _rot(arm, b, ax, d + rng.uniform(-jitter, jitter))
    ms = [o for o in objs if o.type == 'MESH']
    if mat == "darken":      # keep the real clothing (folds, seams, normal maps) but dye it all near-black
        for o in ms:
            for m in o.data.materials:
                pm = m.node_tree.nodes.get("Principled BSDF")
                if pm is None:
                    continue
                src = pm.inputs['Base Color'].links[0].from_socket if pm.inputs['Base Color'].links else None
                mx = m.node_tree.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                mx.inputs['Factor'].default_value = 1.0; mx.inputs[7].default_value = (0.05, 0.05, 0.055, 1)
                if src is not None:
                    m.node_tree.links.new(src, mx.inputs[6])
                else:
                    mx.inputs[6].default_value = pm.inputs['Base Color'].default_value
                m.node_tree.links.new(mx.outputs[2], pm.inputs['Base Color'])
                pm.inputs['Specular IOR Level'].default_value = 0.25
    elif mat is not None:
        for o in ms:
            o.data.materials.clear(); o.data.materials.append(mat)
    # scale/heading/placement on the top-level object
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    P = []
    for o in ms:
        oe = o.evaluated_get(dg); me = oe.to_mesh()
        P.append(np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])); oe.to_mesh_clear()
    P = np.concatenate(P)
    h = P[:, 2].max() - P[:, 2].min(); print("RAW h", h, [o.name for o in objs], [tuple(o.scale) for o in objs if o.parent is None])
    rest_h = 1.82                       # the rest height is ~1.86 model units -> scale so a standing man is 1.82 m
    root.scale = root.scale * (rest_h / 186.0 if h > 20 else 1.0)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    P = []
    for o in ms:
        oe = o.evaluated_get(dg); me = oe.to_mesh()
        P.append(np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])); oe.to_mesh_clear()
    P = np.concatenate(P)
    root.location -= Vector(((P[:, 0].min() + P[:, 0].max()) / 2, (P[:, 1].min() + P[:, 1].max()) / 2, P[:, 2].min()))
    print("THIEF h", P[:, 2].max() - P[:, 2].min())
    pivot = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(pivot)
    root.parent = pivot
    pivot.location = loc; pivot.rotation_euler.z = math.radians(heading_deg)
    bpy.context.view_layer.update()
    # where the right hand is (for the bag)
    hand = arm.matrix_world @ arm.pose.bones["hand_r_051"].head
    # a knitted beanie on the head (child of the head bone), and the hands gloved by the near-black dye
    hb = arm.pose.bones["head_07"]; base = arm.matrix_world @ hb.head
    top = arm.matrix_world @ arm.pose.bones["head_end_08"].head
    up = (top - base).normalized(); c = top - up * 0.095
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.108, location=c, segments=32, ring_count=16)
    cap = bpy.context.active_object; cap.name = name + "_beanie"; cap.scale = (0.95, 1.05, 0.85)
    cap.rotation_euler = up.to_track_quat('Z', 'Y').to_euler()
    bm_ = cap.data
    import bmesh as _bm
    b = _bm.new(); b.from_mesh(bm_)
    _bm.ops.delete(b, geom=[v for v in b.verts if v.co.z < -0.02], context='VERTS'); b.to_mesh(bm_); b.free()
    sol = cap.modifiers.new("t", "SOLIDIFY"); sol.thickness = 0.012
    for pl in bm_.polygons:
        pl.use_smooth = True
    knit = bpy.data.materials.new(name + "_knit"); knit.use_nodes = True; pk = knit.node_tree.nodes["Principled BSDF"]
    pk.inputs['Base Color'].default_value = (0.012, 0.012, 0.014, 1); pk.inputs['Roughness'].default_value = 0.95
    pk.inputs["Sheen Weight"].default_value = 0.3
    bm_.materials.append(knit)
    mwc = cap.matrix_world.copy(); cap.parent = arm; cap.parent_type = 'BONE'; cap.parent_bone = "head_07"
    bpy.context.view_layer.update(); cap.matrix_world = mwc
    return pivot, arm, ms, hand
