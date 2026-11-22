"""Farm packaging for the Seldom intro films (FARM_DELIVERY_RULES.md).

Step 1, one shot:  FILM=6 SHOT=2 PACKDIR=/path/film6 blender -b --python tools/pack_intro.py
    Builds the shot with its scene script, then (instead of rendering) adds the house grade, the shot's animation,
    the farm render settings (2560x1440, 24 fps, Cycles 64 spp adaptive + OIDN, motion blur, textures <= 2K),
    packs every image into the file and saves PACKDIR/shots/S0<SHOT>.blend with its scene named S0<SHOT>.
Step 2, master:    FILM=6 PACKDIR=/path/film6 MASTER=1 blender -b --python tools/pack_intro.py
    MASTER.blend: scene "MASTER" sequencing the linked shot scenes, a scene camera, colour management copied
    from the shots, output //frames/, plus the CapCut shot list (.txt + .csv).
"""
import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
SCENES = os.path.join(HERE, "..", "scenes")
sys.path.insert(0, SCENES)
import bpy
from mathutils import Vector

FILM = int(os.environ["FILM"]); SHOT = int(os.environ.get("SHOT", "1"))
PACKDIR = os.environ["PACKDIR"]
SCRIPT = {5: "sc5_booth.py", 6: "sc6_ice.py", 7: "sc7_darkroom.py", 8: "sc8_archive.py"}[FILM]
TITLE = {5: "Projection Booth", 6: "Ice Station", 7: "Darkroom", 8: "The Archivist"}[FILM]
# shot lengths in seconds, from the P4 script's shot lists
DUR = {5: [3.0, 3.5, 3.5, 3.0], 6: [3.0, 3.5, 3.0, 2.5], 7: [3.0, 4.0, 4.0, 3.0], 8: [3.0, 3.0, 3.0, 3.0]}[FILM]
DESC = {6: ["Wide: head torch through the blizzard toward the buried shape", "Medium low: kneeling, digging with the ice axe",
            "Close over his shoulder: the glove brushes the drum's flank", "Hold: the painted logo in the torch beam, breath clouding"],
        8: ["Wide down the card-index aisle, desk lamp at the far end", "Medium: the blank-label drawer is stuck, she pulls",
            "Close over her shoulder: the drawer gives in a puff of dust", "Top-down hold: the enamel plate in the open file"],
        5: ["Vault: the unlisted can, dust blown off", "Booth: side-lit profile, hand on the lever",
            "Reverse: the beam pours from the port, his silhouette", "Hold: the title card on the screen"],
        7: ["Wide: the darkroom under the safelight", "Medium: rocking the tray", "Over the shoulder: the image rises in the developer",
            "Hold: the print pegged on the line"]}[FILM]
FPS = 24
NF = [round(d * FPS) for d in DUR]


def master():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.name = "MASTER"
    names = []
    for k in range(1, 5):
        path = os.path.join(PACKDIR, "shots", f"S0{k}.blend")
        with bpy.data.libraries.load(path, link=True, relative=True) as (src, dst):
            dst.scenes = [f"S0{k}"]
        names.append(f"S0{k}")
    ref = bpy.data.scenes["S01"]
    sc.render.resolution_x, sc.render.resolution_y = 2560, 1440; sc.render.resolution_percentage = 100
    sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = sum(NF)
    sc.render.engine = 'CYCLES'
    for a in ("view_transform", "look", "exposure", "gamma"):
        setattr(sc.view_settings, a, getattr(ref.view_settings, a))
    sc.display_settings.display_device = ref.display_settings.display_device
    sc.sequencer_colorspace_settings.name = ref.sequencer_colorspace_settings.name
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
    sc.render.filepath = "//frames/"
    sc.render.use_sequencer = True; sc.render.use_compositing = False
    se = sc.sequence_editor_create()
    strips = se.strips if hasattr(se, "strips") else se.sequences
    f = 1
    for k, n in enumerate(names):
        st = strips.new_scene(name=n, scene=bpy.data.scenes[n], channel=1, frame_start=f)
        st.frame_final_duration = NF[k]
        try:
            st.scene_input = 'CAMERA'
        except Exception:
            pass
        f += NF[k]
    cam = bpy.data.objects.new("MASTER_cam", bpy.data.cameras.new("MASTER_cam")); sc.collection.objects.link(cam)
    sc.camera = cam
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PACKDIR, "MASTER.blend"), relative_remap=True)
    # CapCut shot list
    rows = []; f = 1
    for k in range(4):
        rows.append((f"S0{k+1}", f, f + NF[k] - 1, NF[k], f"{DUR[k]:.1f}", DESC[k])); f += NF[k]
    with open(os.path.join(PACKDIR, f"film{FILM}_shotlist.csv"), "w") as fh:
        fh.write("shot,first_frame,last_frame,frames,seconds,description\n")
        for r in rows:
            fh.write(",".join(str(x) for x in r[:5]) + f',"{r[5]}"\n')
    with open(os.path.join(PACKDIR, f"film{FILM}_shotlist.txt"), "w") as fh:
        fh.write(f"Seldom intro {FILM}: {TITLE}  ({sum(NF)} frames, {sum(NF)/FPS:.1f} s, 24 fps, 2560x1440)\n\n")
        for r in rows:
            fh.write(f"{r[0]}  frames {r[1]}-{r[2]}  ({r[4]} s)  {r[5]}\n")
    print("MASTER ok", sum(NF), "frames")


# ----------------------------------------------------------------------------- animation per shot
def key_cam(cam, f0, f1, move=Vector((0, 0, 0)), handheld=0.0):
    cam.rotation_mode = cam.rotation_mode
    p0 = cam.location.copy()
    cam.location = p0; cam.keyframe_insert("location", frame=f0)
    cam.location = p0 + move; cam.keyframe_insert("location", frame=f1)
    for fc in _fcurves(cam):
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'; kp.easing = 'EASE_IN_OUT'
    if handheld:
        for i, fc in enumerate(_fcurves(cam)):
            n = fc.modifiers.new('NOISE'); n.scale = 40; n.strength = handheld; n.phase = 7 * i + FILM


def _fcurves(o):
    ad = o.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves") and len(act.fcurves):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                out += list(cb.fcurves)
    return out


def key_move(objs, f0, f1, delta, ease=True):
    for o in objs:
        p = o.location.copy()
        o.location = p - delta; o.keyframe_insert("location", frame=f0)
        o.location = p; o.keyframe_insert("location", frame=f1)


def haze_density(obj, f0, fpeak, f1, peak, end):
    m = obj.active_material; v = [n for n in m.node_tree.nodes if n.type == 'PRINCIPLED_VOLUME'][0]
    s = v.inputs["Density"]
    if s.links:                                   # noise-mapped: scale the map range's max instead
        s = s.links[0].from_node.inputs[4]
    for fr, val in ((f0, 0.0), (fpeak, peak), (f1, end)):
        s.default_value = val; s.keyframe_insert("default_value", frame=fr)


def animate(sc):
    n = NF[SHOT - 1]; f0, f1 = 1, n
    sc.frame_start, sc.frame_end = f0, f1
    cam = sc.camera
    fwd = (cam.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
    if FILM == 6:
        b = bpy.data.objects.get("blizzard")
        if b:                                        # the snow streams past on the wind
            w = Vector((1.0, -0.3, -0.28)).normalized()
            b.location -= w * 1.2; b.keyframe_insert("location", frame=f0)
            b.location += w * 2.4; b.keyframe_insert("location", frame=f1)
            for fc in _fcurves(b):
                for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
        if SHOT == 1: key_cam(cam, f0, f1, fwd * 0.6, handheld=0.006)
        if SHOT == 2: key_cam(cam, f0, f1, Vector((0.25, 0.05, 0.03)), handheld=0.005)
        if SHOT == 3: key_cam(cam, f0, f1, fwd * 0.15, handheld=0.003)
        if SHOT == 4:
            key_cam(cam, f0, f1, fwd * 0.04)               # locked off, a breath of drift
            breath = [o for o in bpy.data.objects if o.name.startswith("haze") and o.dimensions.x < 1.0]
            for o in breath:
                haze_density(o, f0, int(n * 0.45), f1, 1.1, 0.25)
    elif FILM == 8:
        if SHOT == 1: key_cam(cam, f0, f1, fwd * 0.8, handheld=0.004)
        if SHOT == 2:
            key_cam(cam, f0, f1, fwd * 0.08)
            dr = [o for o in bpy.data.objects if o.name.startswith("the_drawer")]
            for o in dr:                                    # the stuck drawer shudders out its last few cm
                p = o.location.copy()
                for fr, dx in ((1, 0.04), (20, 0.03), (26, 0.036), (40, 0.018), (47, 0.026), (62, 0.0), (72, 0.0)):
                    o.location = p + Vector((dx, 0, 0)); o.keyframe_insert("location", frame=fr)
        if SHOT == 3:
            key_cam(cam, f0, f1, fwd * 0.12, handheld=0.002)
            puffs = [o for o in bpy.data.objects if o.name.startswith("haze") and o.dimensions.x < 1.0]
            for o in puffs:
                haze_density(o, f0, 14, f1, 1.2, 0.35)
            m = bpy.data.objects.get("dust_motes")
            if m:
                m.keyframe_insert("location", frame=f0); m.location.z += 0.12; m.keyframe_insert("location", frame=f1)
        if SHOT == 4: key_cam(cam, f0, f1, fwd * 0.06)
    else:
        key_cam(cam, f0, f1, fwd * 0.2, handheld=0.003)


def limit_textures(maxpx=2048):
    for im in bpy.data.images:
        if im.source == 'FILE' and im.size[0] and max(im.size) > maxpx:
            s = maxpx / max(im.size); im.scale(int(im.size[0] * s), int(im.size[1] * s))


def save_shot(out, grade=True, cine=None, bloom=0.3):
    sc = bpy.context.scene
    if grade:
        import grade as G
        G.add_grade(sc, bloom=bloom, look="cinematic", cine=cine)
    sc.name = f"S0{SHOT}"
    sc.render.resolution_x, sc.render.resolution_y = 2560, 1440; sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.cycles.samples = 64; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception: pass
    sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
    sc.render.filepath = f"//../frames/S0{SHOT}_"
    animate(sc)
    limit_textures()
    for im in bpy.data.images:
        if im.source == 'FILE':
            try: im.pack()
            except Exception as e: print("PACK FAIL", im.name, e)
    os.makedirs(os.path.join(PACKDIR, "shots"), exist_ok=True)
    p = os.path.join(PACKDIR, "shots", f"S0{SHOT}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=p, compress=True)
    print("SHOT SAVED", p)
    sys.exit(0)


if os.environ.get("MASTER"):
    master(); sys.exit(0)

import common as C
C.finish = save_shot
os.environ["SHOT"] = str(SHOT); os.environ.setdefault("HAIR", "0.85"); os.environ["SPP"] = "64"
sys.argv = [os.path.join(SCENES, SCRIPT)]
exec(compile(open(os.path.join(SCENES, SCRIPT)).read(), os.path.join(SCENES, SCRIPT), "exec"),
     {"__name__": "__main__", "__file__": os.path.join(SCENES, SCRIPT)})
