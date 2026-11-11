"""Animated-CG look pass (client direction, Nov 11 ~22:45 UTC).

The client wants the films to read as bright 3D animation, not as a photoreal film:
- bright, high-key and saturated
- soft, even light with lifted shadows
- clean, smooth surfaces with no grit
- light sky-blue gradient backdrops
- little depth of field

This script moves an existing scene toward that look without touching
animation or geometry. It is a starting point: after running it, review stills
and hand-tune any beat that still reads as moody or film-like.

Usage:
  blender -b in.blend --python blender/pipeline/anim_look.py -- out.blend [--no-sky] [--sat 1.25] [--bump 0.35] [--exposure 0.0]

What it changes:
  * Colour: AgX "Punchy" look (exposure unchanged unless --exposure N; check bright beats for blowout)
  * World, camera rays only: a vertical sky gradient (cyan #4fc3f7 at top to near-white
    #e8f7ff at bottom). Lighting still comes from the existing world (HDRI) shader,
    whose strength is raised by 1.6x to lift shadows.
  * Materials:
    - base colour saturation x1.25 (a Hue/Sat node, or an HSV boost on unlinked colours)
    - bump/normal strength x0.35 (smoother, less gritty)
    - roughness raised to at least 0.35 on non-metal, non-glass surfaces (fewer sharp
      specular hits)
  * Cameras: f-stop at least 5.6, so backgrounds stay readable
  * Motion blur off
  * Volumes: density x0.5 (less haze and moodiness)
  * Lights: sun/area/spot energy x1.25
"""
import bpy, sys, colorsys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = argv[0] if argv and not argv[0].startswith("--") else None
def opt(name, default):
    if name in argv:
        i = argv.index(name)
        return type(default)(argv[i + 1])
    return default
SAT = opt("--sat", 1.25)
BUMP = opt("--bump", 0.35)
EXPO = opt("--exposure", 0.0)
NO_SKY = "--no-sky" in argv
TAG = "anim_look_v1"

sc = bpy.context.scene
log = []

# ---- colour management
vs = sc.view_settings
vs.view_transform = "AgX"
for lk in ("AgX - Punchy", "Punchy", "AgX - Medium Contrast", "AgX - Base Contrast"):
    try:
        vs.look = lk
        break
    except TypeError:
        continue
vs.exposure = vs.exposure + EXPO
vs.gamma = 1.0
log.append(f"view AgX look={vs.look} exposure={vs.exposure:.2f}")

# ---- motion blur
sc.render.use_motion_blur = False

# ---- world: sky gradient for camera rays, brighter lighting
def sky_world(w):
    w.use_nodes = True
    nt = w.node_tree
    if nt.nodes.get(TAG):
        return "already"
    outn = next((n for n in nt.nodes if n.type == "OUTPUT_WORLD" and n.is_active_output), None) \
        or next((n for n in nt.nodes if n.type == "OUTPUT_WORLD"), None)
    if outn is None:
        outn = nt.nodes.new("ShaderNodeOutputWorld")
    src = outn.inputs["Surface"].links[0].from_socket if outn.inputs["Surface"].is_linked else None
    # brighten existing lighting
    for n in nt.nodes:
        if n.type == "BACKGROUND":
            n.inputs["Strength"].default_value *= 1.6
    if src is None:
        bg = nt.nodes.new("ShaderNodeBackground")
        bg.inputs["Color"].default_value = (0.6, 0.75, 0.9, 1)
        bg.inputs["Strength"].default_value = 1.0
        src = bg.outputs[0]
    if NO_SKY:
        return "lit only"
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.80, 0.93, 1.0, 1)   # bottom: near white
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.08, 0.55, 0.93, 1)  # top: sky cyan (linear)
    skyb = nt.nodes.new("ShaderNodeBackground")
    skyb.inputs["Strength"].default_value = 1.0
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.name = TAG
    nt.links.new(tc.outputs["Window"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], skyb.inputs["Color"])
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(src, mix.inputs[1])
    nt.links.new(skyb.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], outn.inputs["Surface"])
    return "sky gradient"

if sc.world:
    log.append("world: " + sky_world(sc.world))

# ---- materials
def boost(rgba):
    h, s, v = colorsys.rgb_to_hsv(*rgba[:3])
    r, g, b = colorsys.hsv_to_rgb(h, min(1.0, s * SAT), v)
    return (r, g, b, rgba[3])

nmat = 0
for m in bpy.data.materials:
    if not m.use_nodes or m.node_tree is None:
        continue
    nt = m.node_tree
    if nt.nodes.get(TAG):
        continue
    touched = False
    for n in list(nt.nodes):
        if n.type == "BSDF_PRINCIPLED":
            bc = n.inputs["Base Color"]
            if bc.is_linked:
                l = bc.links[0]
                hs = nt.nodes.new("ShaderNodeHueSaturation")
                hs.inputs["Saturation"].default_value = SAT
                hs.location = (n.location.x - 200, n.location.y)
                nt.links.new(l.from_socket, hs.inputs["Color"])
                nt.links.new(hs.outputs["Color"], bc)
            else:
                bc.default_value = boost(bc.default_value)
            metal = n.inputs["Metallic"].default_value if not n.inputs["Metallic"].is_linked else 0.5
            trans = n.inputs.get("Transmission Weight") or n.inputs.get("Transmission")
            glass = trans is not None and not trans.is_linked and trans.default_value > 0.5
            r = n.inputs["Roughness"]
            if metal < 0.5 and not glass and not r.is_linked and r.default_value < 0.35:
                r.default_value = 0.35
            touched = True
        elif n.type in ("BUMP",):
            n.inputs["Strength"].default_value *= BUMP
            touched = True
        elif n.type == "NORMAL_MAP":
            n.inputs["Strength"].default_value *= BUMP
            touched = True
        elif n.type == "DISPLACEMENT":
            n.inputs["Scale"].default_value *= max(BUMP, 0.5)
            touched = True
        elif n.type in ("VOLUME_PRINCIPLED", "VOLUME_SCATTER", "VOLUME_ABSORPTION"):
            d = n.inputs.get("Density")
            if d is not None and not d.is_linked:
                d.default_value *= 0.5
            touched = True
    if touched:
        tagn = nt.nodes.new("NodeFrame")
        tagn.name = TAG
        tagn.label = TAG
        nmat += 1
log.append(f"materials adjusted: {nmat}")

# ---- cameras
for cam in bpy.data.cameras:
    if cam.dof.use_dof and cam.dof.aperture_fstop < 5.6:
        cam.dof.aperture_fstop = 5.6
log.append("camera f-stop >= 5.6")

# ---- lights
for L in bpy.data.lights:
    if L.type in ("SUN", "AREA", "SPOT"):
        L.energy *= 1.25

sc["anim_look"] = TAG
print("\n".join("[anim_look] " + s for s in log))
if out:
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    print("[anim_look] saved", out)
