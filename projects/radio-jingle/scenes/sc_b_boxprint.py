"""CH3 (chat B): the forensic reconstruction box in the police evidence hall (chat A's sc_box), seen from its
closed +X side (A shoots the open -Y side). The box is empty evidence; no one inside, ever.
A technician (unnamed) dusts a strip of adhesive tape on the outer wall for a fingerprint. Medium shots only.
  dust  (A): medium, slow arc: the technician brushes powder on the tape strip under the work lamp
  lift  (B): over her shoulder, slow push toward the strip as the fine powder hangs in the lamp light
"""
import math
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import pbr, box, cyl, join
from common import ease
from human import reach, fingers_curl
import sc_box as X
import b_common as B

EXPOSURE = getattr(X, "EXPOSURE", 0.0) + 0.6
BOUNCES = getattr(X, "BOUNCES", 6)
DUR = {"dust": 5.0, "lift": 5.0}
VARIANT_FOR = {"dust": "hall|tech", "lift": "hall|tech"}
TAPE = Vector((X.W / 2 + 0.002, -0.05, X.Z0 + 0.95))


def build(variant=None):
    c = X.build(variant or "hall|tech")
    tape_m = pbr("Tape", (0.62, 0.55, 0.38), 0.25, **{'Transmission Weight': 0.3})
    tp = box("TapeStrip", (TAPE.x, TAPE.y, TAPE.z), (0.002, 0.22, 0.05), tape_m)
    tp.rotation_euler = (math.radians(8), 0, 0)
    dust = pbr("Powder", (0.12, 0.12, 0.13), 0.9)
    box("PowderSmudge", (TAPE.x + 0.002, TAPE.y + 0.02, TAPE.z), (0.001, 0.12, 0.04), dust)
    # brush (a short handle with a dark fibre head), the powder jar on a stool beside her
    c["brush"] = join([cyl("BrHandle", (0, 0, 0.06), 0.006, 0.12, pbr("BrH", (0.15, 0.1, 0.05), 0.5), verts=10),
                       cyl("BrHead", (0, 0, -0.01), 0.014, 0.03, pbr("BrFib", (0.05, 0.05, 0.05), 0.9), verts=12)], "Brush")
    # a fine cloud of powder motes near the strip (drifts by frame driver)
    import bmesh
    rng = np.random.default_rng(5); bm = bmesh.new()
    for k in range(220):
        p = Vector((rng.uniform(0.0, 0.18), rng.uniform(-0.2, 0.15), rng.uniform(-0.12, 0.2)))
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rng.uniform(0.0006, 0.0014), matrix=Matrix.Translation(p))
    me = bpy.data.meshes.new("Motes"); bm.to_mesh(me); bm.free()
    mo = bpy.data.objects.new("PowderMotes", me); bpy.context.collection.objects.link(mo)
    mo.data.materials.append(pbr("MoteM", (0.5, 0.5, 0.5), 0.8)); mo.location = TAPE; mo.visible_shadow = False
    for ax, ex in ((0, "0.004 * sin(frame * 0.07)"), (2, "-0.0006 * frame")):
        d = mo.driver_add("location", ax).driver; d.type = 'SCRIPTED'; d.expression = f"{TAPE[ax]} + {ex}"
    # a hard key from the work lamp side onto the strip
    B.key_spot((1.4, -0.9, 2.3), TAPE, 260, 25, (1.0, 0.82, 0.62), soft=0.05, name="StripKey")
    B.key_spot((1.6, 1.6, 2.4), (0.9, 0.3, 1.3), 220, 35, (0.7, 0.8, 1.0), soft=0.3, name="TechRim")
    h = c["P"]["tech"]
    import rj                                                              # pale lab coat (CAST: forensic staff), painted
    for o in h.parts:                                                      # the way A paints outfits: garments only
        if o.type == 'MESH' and "suit" in o.name:
            rj._two_tone_local(o, 0.0, (0.78, 0.78, 0.75), (0.78, 0.78, 0.75))
        if o.type == 'MESH' and "short0" in o.name:                       # hair sheen 0.5 (rj.hair_matte) reads white under
            for m in o.data.materials:                                      # the hard work lamp: keep it dark and matte here
                m.node_tree.nodes["Principled BSDF"].inputs['Sheen Weight'].default_value = 0.08
    B.stand(h, (TAPE.x + 0.48, TAPE.y + 0.3, 0), -math.pi / 2 - 0.35)     # faces -X, the box wall
    c["rest"] = B.capture(h)
    B.finish_interior(lift=0.2)
    return c


def anim(c, t, move):
    sec = t * DUR[move]
    h = c["P"]["tech"]; B.apply_pose(h, c["rest"])
    try:
        X._idle(c, sec)
    except Exception:
        pass
    if move == "lift":                                   # she has stepped back; only the strip and the hanging powder
        B.hide_person(h)                                  # she has left the frame: nothing of her (or the brush) may poke in
        c["brush"].hide_render = True; c["brush"].location = (0, 0, -30)
        for o in bpy.data.objects:                         # the box's low air pipe pokes into this close-up's corner and
            if o.name.startswith("PipeLow"):               # reads as a floating handle (hub 3-2B); the wide 3-2A keeps it
                o.hide_render = True
        bpy.context.view_layer.update()
        return
    fwd = B.fwd_of(h)
    h.rot("spine03", (0, 1, 0), 0); h.rot("head", (0, 0, 1), -6); B.nod(h, 4)
    bpy.context.view_layer.update()
    stroke = Vector((0, 0.07 * math.sin(sec * 3.0), 0.012 * math.sin(sec * 6.0)))
    tip = TAPE + Vector((0.025, 0, 0)) + stroke
    reach(h, "R", tip + Vector((0.13, 0.02, -0.06)), Vector((0.4, 0.3, -1)), Vector((-1, 0, 0.6)))
    reach(h, "L", h.bone_head("spine02") + fwd * 0.15 + Vector((0, -0.18, -0.15)), Vector((0, -0.6, -1)), fwd)
    B.curl(h, 45, side=("R",), thumb=25); B.curl(h, 20, side=("L",))
    w = h.bone_tail("wrist.R"); br = c["brush"]
    br.location = w + (tip - w) * 0.45; d = (w - tip)
    br.rotation_mode = 'QUATERNION'; br.rotation_quaternion = d.to_track_quat('Z', 'Y')
    bpy.context.view_layer.update()


def cam(a, b, tgt, lens):
    return lambda c, t: (Vector(a).lerp(Vector(b), ease(t)), Vector(tgt), lens)


MOVES = {
    "dust": dict(kind="anim", dof=2.8, cam=cam((3.5, -2.4, 1.65), (3.1, -2.0, 1.6), (0.6, 0.05, 1.0), 28),
                 anim=lambda c, t: anim(c, t, "dust"), focus=lambda c, t: TAPE),
    "lift": dict(kind="anim", dof=2.0, cam=cam((1.9, -1.3, 1.55), (1.5, -0.95, 1.45), (TAPE.x, TAPE.y + 0.1, TAPE.z + 0.04), 60),
                 anim=lambda c, t: anim(c, t, "lift"), focus=lambda c, t: TAPE),
}
