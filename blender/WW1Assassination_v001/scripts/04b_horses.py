"""Two horses at the river-side kerb near the blast (CC-BY model, auto-rigged with pipeline/rig_quadruped.py). They rear and shy
at the explosion: torso pitched about the hind hips, hind hooves planted, front hooves paw the air.
blender -b scene.blend --python 04b_horses.py -- <horse_rig.blend> <out.blend>"""
import sys, os, math
import bpy
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "00_lib.py")).read())
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(HERE, "00_story.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = a[0], a[1]
sc = bpy.context.scene
def ground_z(x, y): return 0.0
CH = coll("Horses")
with bpy.data.libraries.load(SRC, link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith("Horse")]
rig0 = next(o for o in dst.objects if o.type == 'ARMATURE'); body0 = next(o for o in dst.objects if o.type == 'MESH')
CH.objects.link(rig0); CH.objects.link(body0)
rigs = [rig0]
r2 = rig0.copy(); CH.objects.link(r2); b2 = body0.copy(); CH.objects.link(b2); b2.parent = r2
for m in b2.modifiers:
    if m.type == 'ARMATURE': m.object = r2
for pb in r2.pose.bones:
    for c in pb.constraints:
        if getattr(c, "target", None) == rig0: c.target = r2
        if getattr(c, "pole_target", None) == rig0: c.pole_target = r2
rigs.append(r2)
H0 = [(Vector((95.5, 4.4)), math.radians(-90), 0.0), (Vector((98.8, 4.2)), math.radians(-100), 0.35)]  # pos, heading (facing -X), delay
FR = list(range(380, 1201, 2))
LEGS = ("FL", "FR", "HL", "HR")
for rig_o, (pos, h, dl) in zip(rigs, H0):
    R = Rig(rig_o)
    tr = R.rest("torso"); BN = R.BN
    hip = (BN["IK_hoof.HL"].head_local + BN["IK_hoof.HR"].head_local) / 2
    hip = Vector((hip.x, hip.y, tr.translation.z * 0.95))
    base = Matrix.Translation(Vector((pos.x, pos.y, 0))) @ Matrix.Rotation(h, 4, 'Z')
    for f in FR:
        s = sig_f(f); u = s - BLAST_SIG - 0.12 - dl
        rear = 0.0; paw = 0.0; shy = 0.0
        if u > 0:
            rear = math.radians(38) * smooth(u / 0.35) * (1 - smooth((u - 1.3) / 0.6))
            paw = math.sin(u * 15) * (1 - smooth((u - 1.3) / 0.5)) if u < 1.9 else 0.0
            shy = 0.9 * smooth((u - 1.2) / 0.9)
        idle = 0.012 * math.sin(s * 2.0 + dl * 5)
        Mrear = Matrix.Translation(hip) @ Matrix.Rotation(-rear, 4, 'X') @ Matrix.Translation(-hip)
        Mbase = base @ Matrix.Translation(Vector((0, 0, 0))) @ Matrix.Translation(Vector((0, -shy * 0.6, 0)))
        R.key_world("torso", f, Mbase @ Mrear @ Matrix.Translation(Vector((0, 0, idle))) @ tr)
        for k in LEGS:
            n = "IK_hoof." + k; Mr = R.rest(n)
            if k[0] == "H":
                M = Mbase @ Mr
            else:
                lift = Matrix.Translation(Vector((0, -0.12 * paw, 0.12 * max(0, paw)))) if rear > 0.05 else Matrix.Identity(4)
                M = Mbase @ Mrear @ lift @ Mr
                if rear < 0.02:
                    M = Mbase @ Mr
            R.key_world(n, f, M)
        # head tosses
        if "head" in R.PB:
            R.key_rot("head", f, [("X", -25 * smooth(u / 0.3) * (1 - smooth((u - 1.5) / 0.6)) if u > 0 else 3 * math.sin(s))])
    rig_o.location = (0, 0, 0)
    for f, hdn in ((1, False), (sc.get("SWAP_F", 1747), True)):
        for o in (rig_o,) + tuple(rig_o.children):
            o.hide_render = hdn; o.keyframe_insert("hide_render", frame=f)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("HORSES_DONE")
