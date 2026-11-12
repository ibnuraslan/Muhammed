"""House LIGHTING recipe (Nov 2026): cinematic, never a plain bright 'normal camera' day.

The grade (grade.add_grade, look="cinematic") darkens and tints, but it cannot make shadows. The mood comes from
how the set is lit:
  * ONE strong directional key: a window or the sun, from the side or behind (never from the camera).
  * Negative fill: the other lights cut way down, no flat ambient, low sky/world strength.
  * Darker walls, floors and ceilings (no white rooms): constant-colour surfaces are capped at ~0.3 albedo.
  * Practicals (lamps, downlights you see) warm.
  * Faces stay readable (face_fill: a soft warm bounce per person), never silhouettes unless the shot asks for it.
  * Natural colours: the mood is light, shadow and contrast, never a colour cast (no blue/teal wash).
  * A little haze / volumetrics in exteriors and forests, so the key reads as light in the air.

Moods:  "overcast" - moody grey day: dark slate sky gradient, soft side key (shadow side ~2 stops down), firmer mids.
        "mist"     - woods by day: cool grey mist, low sun shafts and warm patches, dark understory (look.forest).
        "dusk"     - blue hour: deep blue sky, last warm glow on the horizon, readable (look.forest search scenes).
        "low_sun"  - late sun: warm, low, hard key raking across the set; cool sky fill very low.
        "night"    - keep the set's own night lights, just warm the practicals and darken the walls.

Use in a set's build() (call it at the end, after every object and light exists):
    import look
    if look.enabled():
        look.interior_day(window=((-6.8, -1.3, 1.7), (-4.5, -1.3, 0.6)), mood="low_sun")
    look.day_light("overcast", azim=150, haze=((0, 0, 20), (400, 400, 40)))      # exteriors (builds sky + sun)
    look.night_interior()                                                         # night sets
`HOUSE_LOOK=plain` in the environment (run.py --plain) turns every call into a no-op, for before/after sheets.
"""
import math, os
import bpy
from mathutils import Vector

MOODS = {
        # key: key-light colour, gain: key energy factor, sky: world strength (no sun disc), elev/angle: sun height and
    # softness (deg), sun: sun-lamp energy, haze: volume colour, exposure: scene exposure for exteriors
    "overcast": dict(key=(0.97, 0.97, 1.0), gain=1.0, sky=1.0, tint=(0.95, 0.95, 0.98), elev=24, angle=16.0,
                     sun=3.4, haze=(0.55, 0.6, 0.66), exposure=-0.45,
                     horizon=(0.125, 0.127, 0.132), zenith=(0.04, 0.043, 0.05), ground=(0.02, 0.02, 0.021),
                     cine=dict(contrast=1.32)),
    "mist":     dict(key=(1.0, 0.88, 0.72), gain=1.0, sky=2.0, tint=(1.0, 1.0, 1.0), elev=13, angle=3.0,
                     sun=7.0, haze=(0.78, 0.79, 0.76), exposure=1.9,
                     horizon=(0.27, 0.285, 0.29), zenith=(0.11, 0.12, 0.13), ground=(0.035, 0.036, 0.034),
                     cine=dict(contrast=1.2, sat=1.08, black=(0.0003, 0.00012, 0.0), warm=(1.02, 1.01, 0.97), lift=(0.996, 1.0, 1.007))),
    "dusk":     dict(key=(1.0, 0.62, 0.42), gain=1.0, sky=2.0, tint=(1.0, 1.0, 1.0), elev=2.5, angle=2.0,
                     sun=1.4, haze=(0.5, 0.6, 0.82), exposure=2.0,
                     horizon=(0.17, 0.16, 0.22), zenith=(0.03, 0.055, 0.12), ground=(0.025, 0.027, 0.035),
                     cine=dict(contrast=1.15, sat=0.9, black=(0.0004, 0.0002, 0.0), warm=(0.97, 1.0, 1.07), lift=(0.992, 1.0, 1.014))),
    "low_sun":  dict(key=(1.0, 0.76, 0.56), gain=1.35, sky=0.14, tint=(0.85, 0.88, 0.95), elev=7, angle=1.2,
                     sun=4.2, haze=(1.0, 0.80, 0.62), exposure=-0.6),
}
WARM = (1.0, 0.72, 0.46)          # practicals: tungsten-ish


def set_grade(**cine):
    """Per-shot overrides for grade.CINE, stored on the scene; add_grade picks them up (and bakes keep them)."""
    import json
    s = bpy.context.scene
    cur = json.loads(s.get("look_cine", "{}")); cur.update(cine); s["look_cine"] = json.dumps(cur)


def enabled():
    return os.environ.get("HOUSE_LOOK", "cinematic") != "plain"


def _is_human(o):
    if o.parent is not None and o.parent.type == 'ARMATURE':
        return True
    return any(m.type == 'ARMATURE' for m in getattr(o, "modifiers", []))


def _principled(m):
    if not m or not m.use_nodes:
        return None
    return next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)


# ----------------------------------------------------------------------------------------------- surfaces
def darken_surfaces(cap=0.3, tex_scale=1.0, names=None, objects=None):
    """Cap the albedo of plain constant-colour surfaces (walls, floors, ceilings, counters) at `cap` (max channel),
    keeping their hue. Textured base colours are multiplied by `tex_scale` (1.0 = untouched; scanned Poly Haven
    assets are already realistic). Skips people, glass, metals and emitters. names: only materials whose name
    contains one of these strings."""
    seen = set()
    obs = objects if objects is not None else [o for o in bpy.context.scene.objects if o.type in ('MESH', 'CURVE', 'FONT')]
    for o in obs:
        if _is_human(o):
            continue
        for m in getattr(o.data, "materials", []) or []:
            if m is None or m.name in seen:
                continue
            seen.add(m.name)
            if names and not any(n in m.name for n in names):
                continue
            p = _principled(m)
            if p is None:
                continue
            if p.inputs['Transmission Weight'].default_value > 0.5 or p.inputs['Metallic'].default_value > 0.5:
                continue
            if p.inputs['Emission Strength'].default_value > 0.0 and not p.inputs['Emission Strength'].is_linked \
                    and max(p.inputs['Emission Color'].default_value[:3]) > 0.0:
                continue
            bc = p.inputs['Base Color']
            if bc.is_linked:
                src = bc.links[0].from_node
                if src.type == 'TEX_BRICK':          # procedural tiles: scale their colours directly
                    for nm in ('Color1', 'Color2', 'Mortar'):
                        c = src.inputs[nm].default_value; mx = max(c[:3])
                        if mx > cap:
                            src.inputs[nm].default_value = (*(v * cap / mx for v in c[:3]), 1)
                elif tex_scale != 1.0:
                    N = m.node_tree.nodes; L = m.node_tree.links
                    mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
                    mul.inputs['Factor'].default_value = 1.0; mul.inputs[7].default_value = (tex_scale,) * 3 + (1,)
                    L.new(bc.links[0].from_socket, mul.inputs[6]); L.new(mul.outputs[2], bc)
                continue
            c = bc.default_value; mx = max(c[:3])
            if mx > cap:
                bc.default_value = (*(v * cap / mx for v in c[:3]), 1)


def let_light_through():
    """Clear glass casts no shadow (Cycles has no caustics here), so window light gets into rooms."""
    for o in bpy.context.scene.objects:
        for m in getattr(o.data, "materials", []) or []:
            p = _principled(m)
            if p is not None and p.inputs['Transmission Weight'].default_value > 0.5:
                o.visible_shadow = False
                break


# ----------------------------------------------------------------------------------------------- lights
def negative_fill(scale=0.15, keep=()):
    """Cut every light except the key(s) to `scale`: no flat even fill. Returns the lights it touched."""
    out = []
    for o in bpy.context.scene.objects:
        if o.type == 'LIGHT' and o not in keep and not o.get("look_key"):
            if o.data.animation_data and o.data.animation_data.drivers:
                continue                               # driven lights (blinks, flashes) keep their own levels
            o.data.energy *= scale; out.append(o)
    return out


def warm_practicals(color=WARM, amount=0.7, types=('POINT', 'SPOT')):
    """Tint visible-practical style lights (points, spots: lamps, downlights) towards tungsten."""
    for o in bpy.context.scene.objects:
        if o.type == 'LIGHT' and o.data.type in types and not o.get("look_key"):
            c = o.data.color
            o.data.color = tuple(c[i] * (1 - amount) + color[i] * amount for i in range(3))


def world_strength(factor):
    """Scale the world background (sky / flat ambient) by factor."""
    w = bpy.context.scene.world
    if w and w.use_nodes:
        for n in w.node_tree.nodes:
            if n.type == 'BACKGROUND':
                n.inputs['Strength'].default_value *= factor


def _light(kind, name, energy, color, loc=None, target=None, size=None, angle=None):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if size is not None:
        d.size = size
    if angle is not None:
        d.angle = math.radians(angle)
    o = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(o)
    if loc is not None:
        o.location = loc
    if target is not None:
        z = (Vector(loc) - Vector(target)).normalized()
        o.rotation_euler = z.to_track_quat('Z', 'Y').to_euler()
    o.visible_camera = False; o.visible_transmission = False     # never seen, not even through glass
    if kind == 'AREA':
        o.visible_glossy = False                                  # no white panels in glass or polished floors
    o["look_key"] = True
    return o


def sky(mood="overcast", azim=200, elev=None, strength=None):
    """World: a physical sky with no sun disc (the sun is a lamp, so the key is controllable), low strength."""
    md = MOODS[mood]
    w = bpy.data.worlds.new("LookSky"); bpy.context.scene.world = w; w.use_nodes = True
    N = w.node_tree.nodes; L = w.node_tree.links; N.clear()
    if "zenith" in md:                          # overcast / mist: a slate gradient, dark at the top, pale low down
        tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['Generated'], sp.inputs[0])
        rp = N.new("ShaderNodeValToRGB"); el = rp.color_ramp.elements
        el[0].position = 0.0; el[0].color = (*md["ground"], 1); el[1].position = 0.55; el[1].color = (*md["zenith"], 1)
        e2 = el.new(0.03); e2.color = (*md["horizon"], 1)          # direction z: below horizon dark, pale band, dark top
        bias = N.new("ShaderNodeMath"); bias.operation = 'ADD'; bias.inputs[1].default_value = 0.02
        L.new(sp.outputs['Z'], bias.inputs[0]); L.new(bias.outputs[0], rp.inputs['Fac'])
        bg = N.new("ShaderNodeBackground"); bg.inputs['Strength'].default_value = md["sky"] if strength is None else strength
        out = N.new("ShaderNodeOutputWorld"); L.new(rp.outputs['Color'], bg.inputs['Color']); L.new(bg.outputs[0], out.inputs['Surface'])
        return w
    sk = N.new("ShaderNodeTexSky")
    try:
        sk.sky_type = 'MULTIPLE_SCATTERING'
    except Exception:
        pass
    sk.sun_elevation = math.radians(elev if elev is not None else md["elev"]); sk.sun_rotation = math.radians(azim)
    sk.sun_disc = False; sk.air_density = 1.0
    sk.aerosol_density = 4.0 if mood == "overcast" else 2.0
    mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs[7].default_value = (*md["tint"], 1)
    bg = N.new("ShaderNodeBackground"); bg.inputs['Strength'].default_value = md["sky"] if strength is None else strength
    out = N.new("ShaderNodeOutputWorld")
    L.new(sk.outputs['Color'], mx.inputs[6]); L.new(mx.outputs[2], bg.inputs['Color']); L.new(bg.outputs[0], out.inputs['Surface'])
    return w


def sun_key(mood="low_sun", azim=200, elev=None, energy=None):
    md = MOODS[mood]
    e = math.radians(elev if elev is not None else md["elev"]); a = math.radians(azim)
    d = Vector((math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e)))   # towards the sun
    o = _light('SUN', "LookSun", md["sun"] if energy is None else energy, md["key"], loc=d * 10, target=(0, 0, 0),
               angle=md["angle"])
    return o


def haze(loc, size, mood="overcast", density=None):
    """Exterior/forest atmosphere: a thin forward-scattering volume so the key reads as light in the air."""
    from kit import haze as _haze
    md = MOODS.get(mood, MOODS["overcast"])
    dens = density if density is not None else (0.0012 if mood == "overcast" else 0.0008)
    return _haze(loc, size, density=dens, color=md["haze"], anis=0.55)


def gobo(center, size, axis="x", bars=6, bar=0.22, kind="mullions"):
    """Shadow-only cookie outside a window (invisible to the camera and reflections): breaks the key into window
    patches. axis: the wall normal ("x" or "y"); kind "mullions" = vertical bars, "blinds" = horizontal slats.
    center/size: the window opening (size = (width, height)). Returns the objects."""
    from kit import box
    if not enabled():
        return []
    cx, cy, cz = center; w, h = size; obs = []
    m = bpy.data.materials.get("LookGobo") or bpy.data.materials.new("LookGobo")
    for k in range(bars + 1):
        f = k / bars - 0.5
        if kind == "mullions":
            off, dims = (f * w, 0.0), (bar, h)
            loc = (cx, cy + off[0], cz) if axis == "x" else (cx + off[0], cy, cz)
            sz = (0.05, bar, h) if axis == "x" else (bar, 0.05, h)
        else:
            loc = (cx, cy, cz + f * h)
            sz = (0.05, w, bar) if axis == "x" else (w, 0.05, bar)
        o = box("LookGobo", loc, sz, m)
        o.visible_camera = False; o.visible_glossy = False; o.visible_transmission = False; o.visible_diffuse = False
        obs.append(o)
    return obs


def face_fill(energy=30.0, color=(1.0, 0.86, 0.72), dist=1.3, size=0.9, side=0.6, people=None):
    """Face floor: faces must stay readable mid-tones, never silhouettes (unless the shot asks for it).
    For every rigged person (armature with a 'head' bone) a small soft warm bounce sits in front of the face,
    off to one side and a little above, like light coming back off a desk, a page or a nearby wall.
    Faces turn with rotation z = th towards (sin th, -cos th) (pipeline README). people: armature objects (default all).
    Returns the lights. Call after the people are posed (at the end of build())."""
    if not enabled():
        return []
    out = []
    arms = people if people is not None else [o for o in bpy.context.scene.objects
                                              if o.type == 'ARMATURE' and "head" in o.pose.bones]
    bpy.context.view_layer.update()
    for a in arms:
        a = getattr(a, "arm", a)                                # accepts human.Human too
        head = a.matrix_world @ a.pose.bones["head"].head + Vector((0, 0, 0.08))
        th = a.matrix_world.to_euler().z
        fwd = Vector((math.sin(th), -math.cos(th), 0)); sd = fwd.cross(Vector((0, 0, 1)))
        loc = head + fwd * dist + sd * side + Vector((0, 0, 0.25))
        o = _light('AREA', "LookFaceFill", energy, color, loc=loc, target=head, size=size)
        o.visible_glossy = False                                # no tell-tale highlight in eyes / glass
        out.append(o)
    return out


# ----------------------------------------------------------------------------------------------- recipes
def day_light(mood="overcast", azim=200, elev=None, sun_energy=None, sky_strength=None, haze_box=None,
              haze_density=None, replace=True, exposure=None):
    """Exterior day. Replaces the set's sky and sun lamps (replace=True) with a low sky and one sun key.
    haze_box=(center, size) adds atmosphere. Sets the scene exposure for this mood (pass exposure= to override).
    Pick azim so the sun comes from the side or behind the subject, never from the camera."""
    if not enabled():
        return None
    s = bpy.context.scene
    if replace:
        for o in [o for o in s.objects if o.type == 'LIGHT' and o.data.type == 'SUN']:
            bpy.data.objects.remove(o)
    sky(mood, azim, elev, sky_strength)
    k = sun_key(mood, azim, elev, sun_energy)
    if haze_box is not None:
        haze(haze_box[0], haze_box[1], mood, haze_density)
    s.view_settings.exposure = MOODS[mood]["exposure"] if exposure is None else exposure
    if MOODS[mood].get("cine"):
        set_grade(**MOODS[mood]["cine"])
    return k


def ground_haze(center, size, mood="overcast", height=4.0, density=0.006):
    """Haze that hugs the ground only (a thin low slab), so the sky and the top of the frame stay clean and dark."""
    return haze((center[0], center[1], height / 2), (size[0], size[1], height), mood, density)


def forest(scene=None, mood="mist", azim=160, elev=None, area=((0, 0), (80, 80)), canopy=18.0, density=None,
           sun_energy=None, darken=0.75, exposure=None):
    """Woods / lakeside path. One low sun behind or beside the trees throws shafts through a volume of mist that
    fills the wood up to the canopy; the understory stays dark (textured ground and foliage x `darken`), the sky
    is a dark slate gradient ("mist") or a low warm sun ("low_sun").
    area = ((cx, cy), (sx, sy)): the wooded patch to fill with mist. Place the camera looking towards the sun
    (azim) through the trunks for shafts."""
    if not enabled():
        return None
    s = scene or bpy.context.scene
    for o in [o for o in s.objects if o.type == 'LIGHT' and o.data.type == 'SUN']:
        bpy.data.objects.remove(o)
    sky(mood, azim, elev)
    k = sun_key(mood, azim, elev, sun_energy)
    (cx, cy), (sx, sy) = area
    dens = density if density is not None else {"mist": 0.010, "dusk": 0.007}.get(mood, 0.006)
    hz = haze((cx, cy, canopy / 2), (sx, sy, canopy), mood, dens)
    darken_surfaces(cap=0.25, tex_scale=darken, objects=[o for o in bpy.data.objects if o.type == 'MESH'])  # incl. instanced
    s.view_settings.exposure = MOODS[mood]["exposure"] if exposure is None else exposure
    if MOODS[mood].get("cine"):
        set_grade(**MOODS[mood]["cine"])
    return dict(sun=k, haze=hz)


def interior_day(window, mood="overcast", key_energy=None, key_size=2.5, fill=0.15, sky_factor=0.35, darken=0.3,
                 tex_scale=1.0, keep=(), sun_through=None, warm=True, faces=30.0):
    """Interior by day: one strong window key, everything else cut back, dark walls, warm practicals.
    window = (window_point, target): an area key at the window aimed into the room. For "low_sun" a hard sun lamp
    along the same direction also throws window patches across the floor (sun_through=False to skip).
    key_energy defaults to a strong value for an area of key_size (scale it per set).
    faces: energy of the face floor (face_fill) for every person in the set; 0 to skip (a deliberate silhouette)."""
    if not enabled():
        return None
    md = MOODS[mood]
    loc, tgt = Vector(window[0]), Vector(window[1])
    let_light_through()
    negative_fill(fill, keep)
    world_strength(sky_factor)
    if warm:
        warm_practicals()
    darken_surfaces(darken, tex_scale)
    through = sun_through if sun_through is not None else mood == "low_sun"
    e = (key_energy if key_energy is not None else 260.0 * key_size * key_size) * md["gain"]
    if through:                     # the hard sun is the key; the window area is only its soft spill
        e *= 0.2
    key = _light('AREA', "LookKey", e, md["key"], loc=loc, target=tgt, size=key_size)
    out = dict(key=key)
    if through:
        d = (loc - tgt).normalized()
        sn = _light('SUN', "LookSunThrough", md["sun"] * 2.6, md["key"], loc=tgt + d * 10, target=tgt, angle=md["angle"])
        out["sun"] = sn
    if faces:
        out["faces"] = face_fill(faces)
    return out


def night_interior(darken=0.28, fill=0.8, warm=0.6, lift=0.4, faces=12.0):
    """Night: keep the set's own lights (it is already dark), deepen walls, warm the practicals a touch.
    Stays readable: no crushing, the grade's exposure is mild."""
    if not enabled():
        return None
    darken_surfaces(darken)
    negative_fill(fill)
    warm_practicals(amount=warm)
    bpy.context.scene.view_settings.exposure += lift      # keeps faces and desks readable under the cinematic grade
    if faces:
        face_fill(faces, color=(1.0, 0.82, 0.62))           # like a desk lamp / screen bounce
    return True
