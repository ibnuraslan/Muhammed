"""Part 1 sets, built on the shared library (ship, sea, ph) without changing it.

  atlantic(...)       open sea, sky, warm sun; returns the ocean object
  mary_celeste(...)   the brigantine as found (lib/ship.build) + the found-state props: rail section (shared),
                      second hatch off, binnacle compass smashed, empty boat chocks, lines adrift
  dei_gratia(...)     the same class of ship under full sail
  jolly_boat(...)     a 16 ft ship's boat with thwarts and oars (new here: smallboat.py)
"""
import math, os
import numpy as np
import bpy
from mathutils import Vector, Matrix
import env as E
import ship, sea, ph

WIND = Vector((0.3, -1.0, 0)).normalized()          # world wind: blows toward -Y (a north-north-west wind)


def local_wind(heading_deg):
    return Matrix.Rotation(math.radians(-heading_deg), 3, 'Z') @ WIND


def water_mat():
    # deep Atlantic blue with green-blue light in the crests; the far sea fades into the blue haze of the sky
    return sea.water_material(deep=(0.002, 0.016, 0.05), crest=(0.006, 0.075, 0.11), fog_color=(0.36, 0.48, 0.64))


def atlantic(center=(0, 0), size=240, res=None, scale=2.4, chop=1.7, wind=15.0, hulls=(), cut=None, foam=0.24,
             sun_az=200.0, sun_el=29.0, sun_energy=3.6, sky_rot=0.0, sky_k=1.0, time=11.0):
    res = res or int(os.environ.get("OCEAN_RES", "20"))
    w = water_mat()
    oc = sea.ocean(size=size, res=res, scale=scale, chop=chop, wind=wind, repeat=int(os.environ.get("OCEAN_REPEAT", "3")), foam=foam, mat=w,
                   direction=math.degrees(math.atan2(WIND.y, WIND.x)), hulls=hulls, loc=(center[0], center[1], 0),
                   cut=cut, time=time)
    sea.far_sea(size * 1.45, mat=w, center=center)
    ph.world_hdri(E.SKY_HDRI, strength=sky_k, rot_z=math.radians(sky_rot), res="4k")
    s = E.sun(sun_az, sun_el, energy=sun_energy, color=(1.0, 0.87, 0.68), angle=1.2)
    return oc, s


# ----------------------------------------------------------------------------- ships
GAP = (-2.7, -0.6, "S")


def mary_celeste(heel=2.5, pitch=0.0, heading=0.0, loc=(0, 0, -0.32), detail=True, wet=0.8):
    mc = ship.build("MC", sails="found", rail_gap=GAP, wind=local_wind(heading), wet=wet, detail=detail)
    R = Matrix.Translation(loc) @ Matrix.Rotation(math.radians(heading), 4, 'Z') @ \
        Matrix.Rotation(math.radians(pitch), 4, 'Y') @ Matrix.Rotation(math.radians(-heel), 4, 'X')
    mc["root"].matrix_world = R
    bpy.context.view_layer.update()
    mc["M"] = mc["root"].matrix_world.copy()
    if detail:
        _found_props(mc)
    return mc


def _parent(objs, root):
    bpy.context.view_layer.update()                 # matrix_world of objects placed via .location is stale until now
    for o in objs:
        mw = o.matrix_world.copy(); o.parent = root; o.matrix_world = root.matrix_world @ mw


def _found_props(mc):
    """Things as Deveau found them (in ship coordinates, parented to the ship)."""
    mats = mc["mats"]; root = mc["root"]; made = []
    # the lazarette hatch aft of the cabin trunk: cover off and lying beside it (two hatch covers off)
    xl = -ship.L / 2 + 9.3
    made.append(ship.box("MC_laz_coaming", (xl, -1.5, ship.zdeck(xl) + 0.15), (1.1, 1.1, 0.3), mats["deckwood"], bevel=0.015))
    made.append(ship.box("MC_laz_hole", (xl, -1.5, ship.zdeck(xl) + 0.29), (0.9, 0.9, 0.03), mats["dark"]))
    made.append(ship.box("MC_laz_cover", (xl + 0.2, -2.55, ship.zdeck(xl) + 0.035), (1.05, 1.05, 0.06), mats["deckwood"],
                         rot=(0, 0, 0.5), bevel=0.01))
    # binnacle: a brass compass bowl set into its top, the card under a glass that has been smashed in
    xw = -ship.L / 2 + 1.7; bx = xw + 0.75; bz = ship.zdeck(xw) + 1.05
    made += compass_bowl(Vector((bx, 0, bz)))
    _parent(made, root)


def _tex(kind):
    p = os.path.join(E.P1, "out", "tex", kind + ".png")
    if not os.path.exists(p):
        import subprocess
        subprocess.run(["python3", os.path.join(E.P1, "tools", "make_textures.py"), kind, p], check=True)
    return p


def compass_bowl(top, r=0.135):
    """A ship's compass in its bowl on the binnacle top (ship coords): brass bowl and rim, the card, and the
    glass over it smashed in: crack lines from an impact point, a piece knocked out, splinters on the card."""
    out = []
    brass = E.principled("binn_brass", (0.62, 0.43, 0.2), rough=0.32, metal=1.0)
    out.append(ship.cyl("compass_bowl", top + Vector((0, 0, 0.0)), top + Vector((0, 0, 0.078)), r, r * 0.98, mat=brass, verts=48, caps=False))
    bpy.ops.mesh.primitive_torus_add(major_radius=r + 0.004, minor_radius=0.009, location=top + Vector((0, 0, 0.079)))
    rim = bpy.context.active_object; rim.name = "compass_rim"; rim.data.materials.append(brass); out.append(rim)
    # the card (a textured disc) sits 2 cm under the rim
    card = bpy.data.materials.new("compass_card"); card.use_nodes = True
    N = card.node_tree.nodes; Lk = card.node_tree.links
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(_tex("compass"), check_existing=True)
    Lk.new(t.outputs['Color'], N["Principled BSDF"].inputs['Base Color']); N["Principled BSDF"].inputs['Roughness'].default_value = 0.7
    n = 48; V = [(0, 0, 0)] + [(r * 0.94 * math.cos(2 * math.pi * k / n), r * 0.94 * math.sin(2 * math.pi * k / n), 0) for k in range(n)]
    F = [[0, 1 + k, 1 + (k + 1) % n] for k in range(n)]
    o = ship.mesh_obj("compass_card", V, F, card, smooth=False)
    uv = o.data.uv_layers.new(name="UVMap")
    for l in o.data.loops:
        x, y, _ = V[l.vertex_index]; uv.data[l.index].uv = (0.5 + x / (2 * r * 0.94), 0.5 + y / (2 * r * 0.94))
    o.location = top + Vector((0, 0, 0.062)); o.rotation_euler = (0, 0, math.radians(-23)); out.append(o)
    # the glass: crack lines whiten and roughen it; a hole where a piece is gone (alpha from the crack map)
    g = bpy.data.materials.new("compass_glass"); g.use_nodes = True
    N = g.node_tree.nodes; Lk = g.node_tree.links; p = N["Principled BSDF"]
    p.inputs['Transmission Weight'].default_value = 1.0; p.inputs['IOR'].default_value = 1.5; p.inputs['Roughness'].default_value = 0.03
    ct = N.new("ShaderNodeTexImage"); ct.image = bpy.data.images.load(_tex("cracks"), check_existing=True); ct.image.colorspace_settings.name = 'Non-Color'
    sp = N.new("ShaderNodeSeparateColor"); Lk.new(ct.outputs['Color'], sp.inputs[0])
    rr = N.new("ShaderNodeMapRange"); rr.inputs['To Min'].default_value = 0.03; rr.inputs['To Max'].default_value = 0.6
    Lk.new(sp.outputs[0], rr.inputs['Value']); Lk.new(rr.outputs[0], p.inputs['Roughness'])
    tw = N.new("ShaderNodeMapRange"); tw.inputs['To Min'].default_value = 1.0; tw.inputs['To Max'].default_value = 0.2
    Lk.new(sp.outputs[0], tw.inputs['Value']); Lk.new(tw.outputs[0], p.inputs['Transmission Weight'])
    Lk.new(ct.outputs['Alpha'], p.inputs['Alpha'])
    o = ship.mesh_obj("compass_glass", V, F, g, smooth=False)
    uv = o.data.uv_layers.new(name="UVMap")
    for l in o.data.loops:
        x, y, _ = V[l.vertex_index]; uv.data[l.index].uv = (0.5 + x / (2 * r * 0.94), 0.5 + y / (2 * r * 0.94))
    o.scale = (1.06, 1.06, 1); o.location = top + Vector((0, 0, 0.08)); o.visible_shadow = False; out.append(o)
    out += _shattered_glass("compass_splinters", top + Vector((-0.02, -0.02, 0.064)), 0.03)
    return out


def _shattered_glass(name, c, rad, seed=4):
    """Radial cracks and loose shards of a compass glass: thin glass wedges, a few tilted and lifted."""
    rng = np.random.default_rng(seed)
    g = E.principled(name + "_m", (0.9, 0.93, 0.92), rough=0.04, **{"Transmission Weight": 1.0, "IOR": 1.5})
    out = []; n = 0
    angs = np.sort(rng.uniform(0, 2 * math.pi, max(n, 1)))
    for i in range(n):
        a0, a1 = angs[i], angs[(i + 1) % n] + (2 * math.pi if i == n - 1 else 0)
        if rng.random() < 0.25:
            continue                                       # missing shard: the card shows through
        r0 = rad * rng.uniform(0.0, 0.25)
        V = [(r0 * math.cos(a0), r0 * math.sin(a0), 0), (rad * math.cos(a0), rad * math.sin(a0), 0),
             (rad * math.cos((a0 + a1) / 2), rad * math.sin((a0 + a1) / 2), 0), (rad * math.cos(a1), rad * math.sin(a1), 0),
             (r0 * math.cos(a1), r0 * math.sin(a1), 0)]
        o = ship.mesh_obj(f"{name}{i}", V, [[0, 1, 2, 3, 4]], g, smooth=False)
        o.location = c + Vector((0, 0, rng.uniform(0, 0.004)))
        o.rotation_euler = (rng.normal(0, 0.06), rng.normal(0, 0.06), rng.normal(0, 0.03))
        so = o.modifiers.new("t", "SOLIDIFY"); so.thickness = 0.002
        out.append(o)
    for k in range(5):                                      # loose fragments on the binnacle top
        a = rng.uniform(0, 2 * math.pi); d = rad * rng.uniform(1.05, 1.5)
        V = [(0, 0, 0), (0.014, 0.003, 0), (0.006, 0.012, 0)]
        o = ship.mesh_obj(f"{name}_frag{k}", V, [[0, 1, 2]], g, smooth=False)
        o.location = c + Vector((d * math.cos(a), d * math.sin(a), -0.006)); o.rotation_euler = (0, 0, rng.uniform(0, 6))
        o.modifiers.new("t", "SOLIDIFY").thickness = 0.002
        out.append(o)
    return out


def dei_gratia(heading=0.0, loc=(0, 0, -0.2), heel=-4.0, pitch=1.5, detail=False, sails="full", wet=0.6):
    dg = ship.build("DG", sails=sails, rail_gap=None, wind=local_wind(heading), hatches_off=False, boat_chocks=True,
                    wet=wet, detail=detail)
    dg["root"].matrix_world = Matrix.Translation(loc) @ Matrix.Rotation(math.radians(heading), 4, 'Z') @ \
        Matrix.Rotation(math.radians(pitch), 4, 'Y') @ Matrix.Rotation(math.radians(heel), 4, 'X')
    bpy.context.view_layer.update()
    dg["M"] = dg["root"].matrix_world.copy()
    return dg


def deck_point(M, x, y, dz=0.0):
    """World point on the ship's deck at ship coords (x, y)."""
    return M @ Vector((x, y, ship.zdeck(x) + dz))


def deck_place(M, x, y, heading_local):
    """A person's placement matrix on deck: heading in ship frame (0 faces -Y/starboard, 90 faces the bow)."""
    return M @ Matrix.Translation((x, y, ship.zdeck(x) + 0.006)) @ Matrix.Rotation(math.radians(heading_local), 4, 'Z')
