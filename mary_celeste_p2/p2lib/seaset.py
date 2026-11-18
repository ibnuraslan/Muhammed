"""Open water for Part 2: New York harbour (leaving the pier, at anchor off Staten Island, the pilot leaving) and
the Atlantic off the Azores at dawn (Santa Maria in view). Uses the shared ship and sea libraries unchanged.

Ship frame as in ship.py: bow +X, port +Y, waterline z = 0. The ship sits at the world origin unless moved."""
import math, random
import numpy as np
import bpy
from mathutils import Vector, Matrix, noise
import ship, sea, ph
import stage as S
import pier

MOODS = {
    # sky hdri, rotation, sun azimuth/elevation (deg), sun colour/energy, haze colour/density, water colours, exposure
    "harbour": dict(sky="kloppenheim_06_puresky", rot=200, az=-35, el=14, sun=(1.0, 0.8, 0.6), e=4.0, haze=(0.85, 0.75, 0.62),
                    hd=0.0014, deep=(0.008, 0.013, 0.012), crest=(0.03, 0.045, 0.04), fog=(0.55, 0.5, 0.42), wave=0.35, wind=7),
    "grey":    dict(sky="kloppenheim_06_puresky", rot=120, az=60, el=24, sun=(0.95, 0.92, 0.88), e=1.6, haze=(0.7, 0.7, 0.7),
                    hd=0.0018, deep=(0.008, 0.012, 0.014), crest=(0.03, 0.045, 0.05), fog=(0.5, 0.5, 0.5), wave=0.5, wind=10),
    "evening": dict(sky="qwantani_dusk_2_puresky", rot=60, az=200, el=4, sun=(1.0, 0.55, 0.3), e=3.0, haze=(0.9, 0.62, 0.45),
                    hd=0.0012, deep=(0.006, 0.01, 0.014), crest=(0.03, 0.04, 0.05), fog=(0.55, 0.42, 0.35), wave=0.35, wind=7),
    "dawn":    dict(sky="qwantani_sunrise_puresky", rot=0, az=95, el=6, sun=(1.0, 0.58, 0.32), e=4.0, haze=(1.0, 0.72, 0.52),
                    hd=0.0009, deep=(0.004, 0.012, 0.018), crest=(0.02, 0.06, 0.07), fog=(0.6, 0.48, 0.4), wave=1.2, wind=12),
    "noon":    dict(sky="kloppenheim_06_puresky", rot=0, az=150, el=48, sun=(1.0, 0.92, 0.8), e=4.5, haze=(0.8, 0.82, 0.85),
                    hd=0.0006, deep=(0.004, 0.015, 0.022), crest=(0.02, 0.07, 0.08), fog=(0.5, 0.55, 0.6), wave=1.2, wind=12),
    "overcast": dict(sky="mud_road_puresky", rot=60, az=150, el=26, sun=(1.0, 0.94, 0.86), e=1.4, haze=(0.7, 0.72, 0.75),
                    hd=0.0012, deep=(0.004, 0.013, 0.017), crest=(0.02, 0.07, 0.068), fog=(0.42, 0.43, 0.45), wave=2.0, wind=15),
}


def light(mood):
    m = MOODS[mood]
    sc = bpy.context.scene
    ph.world_hdri(m["sky"], strength=1.0, rot_z=math.radians(m["rot"]), res="4k")
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = m["e"]; sun.data.angle = math.radians(1.5); sun.data.color = m["sun"]
    az, el = math.radians(m["az"]), math.radians(m["el"])
    d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    sun.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    return d


def water(mood, center=(0, 0), hulls=(), cut=None, size=220):
    m = MOODS[mood]
    mat = sea.water_material("sea_" + mood, deep=m["deep"], crest=m["crest"], fog_color=m["fog"])
    o = sea.ocean(size=size, res=int(S.os.environ.get("OCEAN_RES", "22")), scale=m["wave"], chop=1.3, wind=m["wind"],
                  repeat=3, foam=0.2 if m["wave"] > 1 else 0.0, mat=mat, direction=40, hulls=hulls,
                  loc=(center[0], center[1], 0), cut=cut)
    sea.far_sea(size * 1.6, mat=mat, center=center)
    if not S.NOVOL:
        sea.haze((center[0], center[1], 40), (900, 900, 80), density=m["hd"], color=m["haze"], aniso=0.6)
    return o


def furl_all(mc):
    return pier.harbour_rig(mc)


def land(name, center, length, height, depth=60.0, color=(0.16, 0.14, 0.1), houses=0, seed=3, trees=True):
    """A low shore seen across the water: a rolling ridge (displaced strip), dark woods, a few white houses."""
    rng = np.random.default_rng(seed)
    nx, ny = 120, 12
    V = []; F = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            u, v = i / nx, j / ny
            x = center[0] + (u - 0.5) * length
            y = center[1] + v * depth
            hh = height * (0.45 + 0.55 * noise.noise(Vector((u * 5, 0.3, seed)))) * math.sin(math.pi * min(1, v * 1.6)) ** 0.6
            hh *= min(1, u * 8, (1 - u) * 8)
            V.append((x, y, hh - 0.5))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            F.append([a, a + 1, a + nx + 2, a + nx + 1])
    mt = bpy.data.materials.new(name + "_m"); mt.use_nodes = True
    N = mt.node_tree.nodes; L = mt.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 0.08
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.inputs[6].default_value = (*color, 1)
    mx.inputs[7].default_value = (color[0] * 1.6, color[1] * 1.45, color[2] * 1.1, 1); L.new(nz.outputs['Fac'], mx.inputs['Factor'])
    L.new(mx.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.95
    o = ship.mesh_obj(name, V, F, mt)
    white = ship.paint(name + "_white", (0.6, 0.56, 0.5), rough=0.6, grime=0.3)
    roof = ship.paint(name + "_roof", (0.12, 0.06, 0.04), rough=0.7, grime=0.3)
    for k in range(houses):
        x = center[0] + rng.uniform(-0.4, 0.4) * length; y = center[1] + rng.uniform(1, 6)
        ship.box(name + "_house", (x, y, 2.5), (rng.uniform(6, 10), 6, 5), white)
        ship.box(name + "_roof", (x, y, 5.4), (rng.uniform(6, 10) + 0.5, 6.4, 0.9), roof)
    return o


def island_santa_maria(center, scale=1.0):
    """Santa Maria from a few miles off: a long, high, cliffed island (eastern end higher), hazed by distance."""
    nx, ny = 160, 40
    V = []; F = []
    Lx, Ly, Hm = 9000 * scale, 2600 * scale, 560 * scale
    for j in range(ny + 1):
        for i in range(nx + 1):
            u, v = i / nx, j / ny
            x = center[0] + (u - 0.5) * Lx; y = center[1] + (v - 0.5) * Ly
            prof = math.sin(math.pi * u) ** 0.35 * math.sin(math.pi * v) ** 0.5
            ridge = Hm * (0.55 + 0.45 * u) * prof * (0.75 + 0.25 * noise.noise(Vector((u * 6, v * 6, 1.3))))
            V.append((x, y, ridge - 20))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            F.append([a, a + 1, a + nx + 2, a + nx + 1])
    mt = bpy.data.materials.new("santa_maria"); mt.use_nodes = True
    p = mt.node_tree.nodes["Principled BSDF"]; p.inputs['Base Color'].default_value = (0.12, 0.1, 0.075, 1); p.inputs['Roughness'].default_value = 0.95
    return ship.mesh_obj("SantaMaria", V, F, mt)


def tug(name, at, yaw, smoke=True):
    """A New York harbour steam tug of the 1870s: low black hull, white deckhouse, tall black stack, walking beam."""
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    blk = ship.paint(name + "_blk", (0.015, 0.014, 0.013), rough=0.4, grime=0.3)
    wht = ship.paint(name + "_wht", (0.62, 0.58, 0.5), rough=0.5, grime=0.4)
    red = ship.paint(name + "_red", (0.3, 0.04, 0.03), rough=0.5, grime=0.3)
    parts = []
    # hull: a tapered lofted box
    V = []; F = []
    n = 24
    for i in range(n + 1):
        u = i / n
        x = -11 + 22 * u
        hb = 2.6 * (math.sin(math.pi * min(1, u * 1.15)) ** 0.5) if u < 0.87 else 2.6 * max(0.05, (1 - u) / 0.13) ** 0.7
        for (yy, zz) in ((-hb, 1.4), (-hb * 0.8, -0.8), (0, -1.4), (hb * 0.8, -0.8), (hb, 1.4)):
            V.append((x, yy, zz))
    for i in range(n):
        for k in range(4):
            a = i * 5 + k
            F.append([a, a + 5, a + 6, a + 1])
    parts.append(ship.mesh_obj(name + "_hull", V, F, blk))
    parts.append(ship.box(name + "_deck", (0, 0, 1.35), (20, 4.6, 0.1), ship.wood("weathered_planks", 0.5, name=name + "_dk")))
    parts.append(ship.box(name + "_house", (-1.0, 0, 2.5), (9, 3.4, 2.2), wht, bevel=0.05))
    parts.append(ship.box(name + "_pilothouse", (3.2, 0, 4.2), (2.4, 2.4, 1.5), wht, bevel=0.05))
    parts.append(ship.box(name + "_stripe", (-1.0, 0, 3.55), (9.1, 3.5, 0.15), red))
    parts.append(ship.cyl(name + "_stack", (0.4, 0, 3.4), (0.4, 0, 9.5), 0.55, mat=blk, verts=20))
    parts.append(ship.cyl(name + "_beam", (-2.6, 0, 6.2), (-2.6 + 0.1, 0, 6.3), 0.1, mat=blk))
    for o in parts:
        o.parent = root
    root.location = at; root.rotation_euler = (0, 0, math.radians(yaw))
    if smoke:
        # coal smoke from the stack: a trail of soft puffs drifting aft and up, thinning as they spread
        sm = bpy.data.materials.new(name + "_smoke"); sm.use_nodes = True
        N = sm.node_tree.nodes; Lk = sm.node_tree.links; N.remove(N["Principled BSDF"])
        pv = N.new("ShaderNodeVolumePrincipled"); pv.inputs['Color'].default_value = (0.09, 0.08, 0.075, 1)
        tc = N.new("ShaderNodeTexCoord")
        gr = N.new("ShaderNodeTexGradient"); gr.gradient_type = 'SPHERICAL'; Lk.new(tc.outputs['Object'], gr.inputs['Vector'])
        nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 2.5; nz.inputs['Detail'].default_value = 6
        Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
        mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; Lk.new(gr.outputs['Fac'], mul.inputs[0]); Lk.new(nz.outputs['Fac'], mul.inputs[1])
        mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = 0.12; mr.inputs['From Max'].default_value = 0.5
        mr.inputs['To Max'].default_value = 1.0; Lk.new(mul.outputs[0], mr.inputs['Value'])
        at = N.new("ShaderNodeAttribute"); at.attribute_type = 'OBJECT'; at.attribute_name = "dens"
        dm = N.new("ShaderNodeMath"); dm.operation = 'MULTIPLY'; Lk.new(mr.outputs[0], dm.inputs[0]); Lk.new(at.outputs['Fac'], dm.inputs[1])
        Lk.new(dm.outputs[0], pv.inputs['Density'])
        Lk.new(pv.outputs[0], N["Material Output"].inputs['Volume'])
        # many small overlapping puffs along one curved path: reads as a single soft plume
        n = 40
        for k in range(n):
            t = k / (n - 1)
            r = 0.45 + 2.4 * t ** 1.2
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=1.0)
            pl = bpy.context.active_object; pl.name = f"{name}_plume{k:02d}"; pl.data.materials.append(sm)
            pl.scale = (r * 1.25, r, r * 0.85)
            pl.parent = root
            pl.location = (0.4 - 16.0 * t ** 1.15, 0.6 * math.sin(t * 5.0), 9.6 + 1.2 + 6.5 * t ** 0.8)
            pl["dens"] = 0.55 / r * (1.0 - 0.6 * t)       # thin as it spreads; similar opacity per unit length
            pl.visible_shadow = False
    return root


def pilot_boat(name, at, yaw, rowers=2):
    """The pilot's yawl: Poly Haven ship_pinnace scaled to a 6 m boat."""
    r, ms = S.place_model("ship_pinnace", at, size=1.0, axis=0, rot_z=math.radians(yaw), ground=False)
    for o in ms:                                   # a pulling boat: no mast or sail
        if any(k in o.name.lower() for k in ("rig", "mast", "sail", "rope", "flag")):
            o.hide_render = True; o.hide_viewport = True
    ms = [o for o in ms if not o.hide_render]
    lo, hi = ph.bounds(ms); L = max(hi.x - lo.x, hi.y - lo.y)
    r.scale = tuple(c * 6.0 / L for c in r.scale)
    bpy.context.view_layer.update()
    lo, hi = ph.bounds(ms)
    r.location.z += -(lo.z + (hi.z - lo.z) * 0.35) + at[2]
    return r, ms
