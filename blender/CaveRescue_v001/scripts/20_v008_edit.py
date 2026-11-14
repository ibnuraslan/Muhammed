"""v008 edit (director review of v007):
1. No black frames: every rock-wipe key is cleared. The camera's passes through rock are removed by direct cuts (below).
2-3, 7. Cuts (old -> new frames). Kept spans play at normal speed; a removed span collapses into one frame (a direct cut).
   The first cross-section is time-compressed to 2.5 s, the second is removed; the diver tunnel keeps 1231-1300 and the
   lone diver going still (1489-1600).
4. Divers in a normal-thickness wetsuit: the baggy MPFB work coverall is hidden and the MPFB body itself wears a dark
   neoprene material from the neck to the wrists and ankles (head, hands and feet keep skin / booties).
6. DiverA's torch lens is hidden while he is underwater in view (1040-1140): it read as a giant glowing ball.
blender -b in.blend --python 20_v008_edit.py -- out.blend beats_in.json beats_out.json"""
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]; OUT, BIN, BOUT = a[0], a[1], a[2]
sc = bpy.context.scene
KEEP = [(1, 283, None), (297, 574, None), (600, 999, 150), (1020, 1300, None), (1489, 1600, None), (1736, 2406, None), (2428, 2559, None), (2731, 3090, None)]
AN = []; n = 1
for o0, o1, L in KEEP:
    n0 = n if not AN else AN[-1][1] + 1
    n1 = n0 + (L if L else (o1 - o0))
    AN += [(o0, n0), (o1, n1)]
END = AN[-1][1]
def warp(x):
    if x <= AN[0][0]: return AN[0][1] + (x - AN[0][0])
    for (a0, b0), (a1, b1) in zip(AN, AN[1:]):
        if x <= a1: return b0 + (x - a0) * (b1 - b0) / (a1 - a0)
    return AN[-1][1] + (x - AN[-1][0])
# 6. torch lens
ln = bpy.data.objects.get("DiverA_TorchLens")
if ln:
    for f, h in ((1039, False), (1040, True), (1140, True), (1141, False)):
        ln.hide_render = h; ln.keyframe_insert("hide_render", frame=f)
# 1. clear the rock wipe
mw = bpy.data.materials.get("M_RockWipe")
if mw and mw.node_tree.animation_data: mw.node_tree.animation_data_clear()
if mw: mw.node_tree.nodes["Wipe"].outputs[0].default_value = 0.0
card = bpy.data.objects.get("CAM_RockWipe")
if card: card.hide_render = True; card.hide_viewport = True
# 4. wetsuits
SKIN = ("head", "neck", "jaw", "eye", "ear", "nose", "lip", "cheek", "brow", "temple", "orbicularis", "levator", "oris", "risorius", "special", "tongue", "teeth",
        "hand", "finger", "metacarpal", "thumb", "palm", "foot", "toe")
neo = bpy.data.materials.new("M_Neoprene"); neo.use_nodes = True
p = neo.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (0.02, 0.022, 0.028, 1); p.inputs["Roughness"].default_value = 0.42
if "Coat Weight" in p.inputs: p.inputs["Coat Weight"].default_value = 0.25
for dn in ("DiverA", "DiverB", "DiverC"):
    rig = bpy.data.objects[dn]; body = bpy.data.objects[dn + ".body"]
    for o in rig.children_recursive:
        if o.type == 'MESH' and o.name.endswith("male_worksuit01"):
            o.hide_render = True; o.hide_viewport = True
    for md in body.modifiers:
        if md.type == 'MASK' and "worksuit" in md.name: md.show_render = False; md.show_viewport = False   # keep "Hide helpers" (proxy shells) and the shoe mask on
    body.data.materials.append(neo); slot = len(body.data.materials) - 1
    bones = {b.name.lower() for b in rig.data.bones}; gi = {g.index: g.name.lower() for g in body.vertex_groups}
    dom = {}
    for v in body.data.vertices:
        gs = [g for g in v.groups if gi.get(g.group, "") in bones]
        dom[v.index] = gi[max(gs, key=lambda g: g.weight).group] if gs else ""
    k = 0
    for pl in body.data.polygons:
        names = [dom[i] for i in pl.vertices]
        if not any(nm.startswith(SKIN) or any(s in nm for s in ("hand", "finger", "metacarpal", "head", "neck", "foot", "toe")) for nm in names):
            pl.material_index = slot; k += 1
    print("WETSUIT", dn, "faces", k)
# 2-3, 7. cuts
nk = 0
for act in bpy.data.actions:
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        kp.co.x = warp(kp.co.x); kp.handle_left.x = warp(kp.handle_left.x); kp.handle_right.x = warp(kp.handle_right.x); nk += 1
                    fc.update()
sc.frame_start, sc.frame_end = 1, END
beats = json.load(open(BIN))
for b in beats:
    b["frame_v007"] = b["frame"]; b["frame"] = int(round(warp(b["frame"])))
json.dump(beats, open(BOUT, "w"), indent=1)
print("EDIT keys", nk, "end", END, "anchors", AN)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("V008_EDIT_OK")
