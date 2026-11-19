"""FINAL thumbnail (hub pick: concept a, daylight brief). The Mary Celeste as found, alone on the open Atlantic at
midday: bright blue sky with big white clouds, royal-blue sea going turquoise where the sun lights it, white water
at her bow, torn weathered fore-topsails in full sun, a heavily weathered hull (streaked paint, salt, rust under the
chainplates). Low 3/4 bow angle near the waterline, the ship ~60% of the frame. Empty deck, no lights, no people,
no text. Natural, bright grade."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
T.C.reset()
import bpy
from mathutils import Vector, Matrix
import ship, sea, grade

E = os.environ.get
OUT = E("OUT", os.path.join(T.OUTDIR, "thumb_final.png"))
sc = T.res_setup(int(E("SPP", "384")), noise=0.012)

SUN_AZ = float(E("SUN_AZ", "300")); SUN_EL = float(E("SUN_EL", "38"))
WIND_WORLD = Vector((0.5, -1.0, 0)).normalized()
MC_HEAD = float(E("HEAD", "228"))
mc = ship.build("MC", sails="found", rail_gap=(-2.7, -0.6, "S"),
                wind=Matrix.Rotation(math.radians(-MC_HEAD), 3, 'Z') @ WIND_WORLD, wet=0.6, detail=True,
                bow_wave_h=float(E("BOWW", "1.1")))
mc_pos = Vector((float(E("SHIPX", "2")), float(E("SHIPY", "55")), 0))
mc["root"].location = mc_pos + Vector((0, 0, -0.7))
mc["root"].rotation_euler = (math.radians(float(E("HEEL", "-5"))), math.radians(1.5), math.radians(MC_HEAD))
bpy.context.view_layer.update()


# ---------------------------------------------------------------- weathering on the black topsides
def weather(m):
    nt = m.node_tree; N = nt.nodes; Lk = nt.links; p = N["Principled BSDF"]
    src = p.inputs['Base Color'].links[0].from_socket
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs['Object'], sep.inputs[0])

    def streaks(scale, sx, sz, lo, hi, seed):
        mp = N.new("ShaderNodeMapping"); mp.inputs['Scale'].default_value = (sx, sx, sz)
        mp.inputs['Location'].default_value = (seed, seed * 0.7, 0); Lk.new(tc.outputs['Object'], mp.inputs['Vector'])
        nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 9
        nz.inputs['Roughness'].default_value = 0.6; Lk.new(mp.outputs[0], nz.inputs['Vector'])
        mr = N.new("ShaderNodeMapRange"); mr.inputs['From Min'].default_value = lo; mr.inputs['From Max'].default_value = hi
        Lk.new(nz.outputs['Fac'], mr.inputs['Value']); return mr.outputs[0]

    def mul(a, b):
        n = N.new("ShaderNodeMath"); n.operation = 'MULTIPLY'; Lk.new(a, n.inputs[0])
        Lk.new(b, n.inputs[1]) if not isinstance(b, float) else None
        if isinstance(b, float):
            n.inputs[1].default_value = b
        return n.outputs[0]

    def band(sock, a, b, c, d):          # 0 below a, 1 between b..c, 0 above d (smooth)
        r1 = N.new("ShaderNodeMapRange"); r1.inputs['From Min'].default_value = a; r1.inputs['From Max'].default_value = b
        r1.interpolation_type = 'SMOOTHSTEP'; Lk.new(sock, r1.inputs['Value'])
        r2 = N.new("ShaderNodeMapRange"); r2.inputs['From Min'].default_value = d; r2.inputs['From Max'].default_value = c
        r2.interpolation_type = 'SMOOTHSTEP'; Lk.new(sock, r2.inputs['Value'])
        return mul(r1.outputs[0], r2.outputs[0])

    def mix(base, col, fac):
        mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; Lk.new(fac, mx.inputs['Factor']); Lk.new(base, mx.inputs[6])
        mx.inputs[7].default_value = (*col, 1); return mx.outputs[2]

    # faded paint: the black has weathered to a streaky charcoal-brown
    fade = streaks(3.0, 1.0, 0.12, 0.3, 0.75, 0.0)
    out = mix(src, (0.075, 0.068, 0.06), mul(fade, 0.85))
    # salt: pale crust in streaks, heaviest in a band above the waterline
    zsalt = band(sep.outputs['Z'], -0.3, 0.2, 1.2, 2.4)
    salt = mul(streaks(5.0, 1.0, 0.08, 0.5, 0.72, 3.3), zsalt)
    out = mix(out, (0.42, 0.42, 0.39), mul(salt, 0.75))
    # rust running down from the chainplates at each mast's channel
    xs = []
    for mx_ in (ship.FORE_X, ship.MAIN_X):
        xs.append(band(sep.outputs['X'], mx_ - 1.8, mx_ - 1.4, mx_ + 0.95, mx_ + 1.3))
    xm = N.new("ShaderNodeMath"); xm.operation = 'MAXIMUM'; Lk.new(xs[0], xm.inputs[0]); Lk.new(xs[1], xm.inputs[1])
    zr = band(sep.outputs['Z'], 0.2, 0.9, 2.1, 2.3)
    rust = mul(mul(streaks(7.0, 1.0, 0.05, 0.52, 0.7, 9.1), xm.outputs[0]), zr)
    out = mix(out, (0.2, 0.065, 0.02), mul(rust, 0.95))
    # general light rust bleed all along
    out = mix(out, (0.16, 0.06, 0.025), mul(mul(streaks(9.0, 1.0, 0.04, 0.62, 0.74, 5.5), zr), 0.6))
    Lk.new(out, p.inputs['Base Color'])
    # salt and faded paint are matte
    rr = N.new("ShaderNodeMath"); rr.operation = 'ADD'; rr.use_clamp = True
    r0 = p.inputs['Roughness'].links[0].from_socket if p.inputs['Roughness'].links else None
    if r0 is not None:
        Lk.new(r0, rr.inputs[0])
    else:
        rr.inputs[0].default_value = p.inputs['Roughness'].default_value
    Lk.new(mul(salt, 0.5), rr.inputs[1]); Lk.new(rr.outputs[0], p.inputs['Roughness'])


weather(mc["mats"]["topside"])

# ---------------------------------------------------------------- sea: royal blue, turquoise where lit
water = sea.water_material(deep=(0.002, 0.016, 0.075), crest=(0.0, 0.16, 0.17), fog_color=(0.55, 0.7, 0.86))
sea.ocean(size=220, res=int(E("OCEAN_RES", "13")), scale=float(E("WAVE", "2.2")), chop=float(E("CHOP", "1.8")),
          wind=float(E("OC_WIND", "15")), repeat=3, foam=float(E("FOAM", "0.3")), mat=water,
          direction=math.degrees(math.atan2(WIND_WORLD.y, WIND_WORLD.x)), hulls=(mc["hull"],), loc=(0, 50, 0), seed=7)
sea.far_sea(330, mat=water, center=(0, 50))
# sunlit turquoise: light through the water just under the surface (subsurface-ish) on the main water
p = water.node_tree.nodes["Principled BSDF"]
p.inputs['Specular IOR Level'].default_value = float(E("SPEC", "0.2"))

# white water off her bow as she falls off a sea
bow = mc["root"].matrix_world @ Vector((ship.L / 2 - 1.5, 0.0, 0.3))
fwd = (mc["root"].matrix_world.to_3x3() @ Vector((1, -0.4, 0))).normalized()
sea.spray("bow_spray", bow, (1.2, 1.0, 4.5), count=12000, rmin=0.012, rmax=0.04, up=2.6, dirv=fwd)
sea.mist_puff("bow_mist", bow + fwd * 1.5 + Vector((0, 0, 0.6)), (2.6, 2.0, 1.0), density=0.3, seed=2)

# ---------------------------------------------------------------- daylight: blue noon sky with white clouds + sun
SKY_ROT = SUN_AZ - 139.0            # sea.sky default HDRI (kloppenheim_06_puresky): sun az = 139 + rot
sea.sky(strength=float(E("SKY_K", "1.4")), rot_deg=SKY_ROT)
# deeper blue and crisper clouds: a gamma on the HDRI before the background
wn = sc.world.node_tree; env = [n for n in wn.nodes if n.type == 'TEX_ENVIRONMENT'][0]
bgn = [n for n in wn.nodes if n.type == 'BACKGROUND'][0]
gm = wn.nodes.new("ShaderNodeGamma"); gm.inputs['Gamma'].default_value = float(E("SKY_G", "1.35"))
hs = wn.nodes.new("ShaderNodeHueSaturation"); hs.inputs['Saturation'].default_value = float(E("SKY_SAT", "1.2"))
wn.links.new(env.outputs['Color'], gm.inputs['Color']); wn.links.new(gm.outputs['Color'], hs.inputs['Color'])
wn.links.new(hs.outputs['Color'], bgn.inputs['Color'])
T.sun(SUN_AZ, SUN_EL, energy=float(E("SUN_E", "4.2")), color=(1.0, 0.96, 0.9), angle=1.0)

# ---------------------------------------------------------------- camera: low 3/4 off her bow, near the water
cam_loc = Vector((float(E("CAMX", "0")), 0, float(E("CAMZ", "3.0"))))
tgt = mc_pos + Vector((float(E("TX", "-1.5")), 0, float(E("TZ", "12"))))
T.C.camera(cam_loc, tgt, lens=float(E("LENS", "28")), fstop=float(E("FSTOP", "16")), focus=(mc_pos - cam_loc).length,
           roll=float(E("ROLL", "-1.5")))

if E("CLIP"):
    import clipcheck
    clipcheck.check("thumb_final", limit=40); sys.exit(0)

# natural, bright grade: light vignette, a touch of punch and saturation, no colour cast
grade.add_grade(sc, bloom=0.15, vignette=float(E("VIG", "0.25")), look="cinematic",
                cine={"exposure": float(E("EXPO", "0.0")), "contrast": float(E("CON", "1.14")), "sat": float(E("SAT", "1.3")),
                      "knee": 0.7, "span": 1.6})
sc.render.filepath = OUT; os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.render.render(write_still=True)
print("RENDERED", OUT)
