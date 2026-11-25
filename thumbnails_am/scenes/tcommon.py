"""Shared setup for the Antwerp / Mummy thumbnails. The scenes reuse each film's 3D library:
    ANTWERP3D = checkout of branch claude/antwerp-heist, folder antwerp_heist/3d
    MUMMY3D   = checkout of branch claude/mummy-cladh-hallan, folder mummy/3d
Call T.use("antwerp") or T.use("mummy") before importing anything from those libraries."""
import os, sys, math
import importlib.util as _iu
HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "..", "out")
ROOTS = {"antwerp": os.environ.get("ANTWERP3D", os.path.join(HERE, "..", "..", "wt_antwerp", "antwerp_heist", "3d")),
         "mummy": os.environ.get("MUMMY3D", os.path.join(HERE, "..", "..", "wt_mummy", "mummy", "3d")),
         "mc": os.environ.get("MC3D", os.path.join(HERE, "..", "..", "wt_mary", "mary_celeste_3d"))}
C = None
E = os.environ.get


def use(film):
    global C
    root = ROOTS[film]
    for p in (os.path.join(root, "lib"), HERE):
        if p not in sys.path:
            sys.path.insert(0, p)
    spec = _iu.spec_from_file_location("film_common", os.path.join(root, "scenes", "common.py"))
    C = _iu.module_from_spec(spec); spec.loader.exec_module(C)
    C.reset()
    return C


def res_setup(spp, noise=0.015):
    import bpy
    sc = C.render_setup(samples=spp, noise=noise, res=(1920, 1080))
    pv = float(E("PREVIEW", "0"))
    sc.render.resolution_percentage = int(100 * pv) if pv else 100
    sc.cycles.samples = spp
    sc.cycles.adaptive_threshold = noise
    sc.view_settings.view_transform = 'AgX'
    return sc


def sun(az_deg, el_deg, energy=3.0, color=(1.0, 0.95, 0.88), angle=1.5):
    import bpy
    from mathutils import Vector
    sc = bpy.context.scene
    s = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(s)
    s.data.energy = energy; s.data.angle = math.radians(angle); s.data.color = color
    az, el = math.radians(az_deg), math.radians(el_deg)
    toward = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    s.rotation_euler = (-toward).to_track_quat('-Z', 'Y').to_euler()
    return s


def area(name, loc, target, size, energy, color=(1, 1, 1), size_y=None):
    import bpy
    from mathutils import Vector
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.color = color
    if size_y:
        l.shape = 'RECTANGLE'; l.size = size; l.size_y = size_y
    else:
        l.size = size
    o = bpy.data.objects.new(name, l); bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


def grade(sc, sat=1.25, con=1.1, expo=0.0, vig=0.2, bloom=0.15):
    import grade as G
    G.add_grade(sc, bloom=bloom, vignette=vig, look="cinematic",
                cine={"exposure": expo, "contrast": con, "sat": sat, "knee": 0.7, "span": 1.6})


def render(sc, name):
    import bpy
    out = E("OUT", os.path.join(OUTDIR, name + ".png"))
    sc.render.filepath = out; os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", out)


def hdri_sun_rot(aid, want_az, res="4k"):
    """Rotation (rad) for ph.world_hdri so the HDRI's brightest spot (its sun) sits at world azimuth want_az (deg)."""
    import bpy, numpy as np, ph
    im = bpy.data.images.load(ph.hdri(aid, res), check_existing=True)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::4, ::4, :3].sum(2)
    j, i = np.unravel_index(np.argmax(a), a.shape)
    u = (i + 0.5) / a.shape[1]; v = (j + 0.5) / a.shape[0]
    phi = (u - 0.5) * 2 * math.pi
    az = math.degrees(math.atan2(math.sin(phi), -math.cos(phi)))
    print("HDRI sun az", az, "el", (v - 0.5) * 180)
    return math.radians(az - want_az)


def glints(sc, thr=1.5, strength=0.6, streaks=6):
    """Add star streaks on the brightest specular points (diamond glints) after the house grade."""
    import bpy
    nt = sc.compositing_node_group if hasattr(sc, "compositing_node_group") else None
    if nt is None:
        print("no compositor group"); return
    out = [n for n in nt.nodes if n.bl_idname == "NodeGroupOutput"][0]
    src = out.inputs[0].links[0].from_socket
    g = nt.nodes.new("CompositorNodeGlare")
    for name, val in (("Type", 'Streaks'), ("Threshold", thr), ("Strength", strength), ("Streaks", streaks),
                      ("Quality", 'High'), ("Fade", 0.88), ("Streaks Angle", math.radians(15))):
        if name in g.inputs:
            try:
                g.inputs[name].default_value = val
            except Exception as e:
                print("glare", name, e)
    nt.links.new(src, g.inputs['Image']); nt.links.new(g.outputs['Image'], out.inputs[0])
