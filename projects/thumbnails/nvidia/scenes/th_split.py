"""Thumbnail 5 - TWO WORLDS. Split frame: on the left the domed Capitol at night in cold blue floodlight; on the right
the film's data hall turned blood-red, the woman walking away down the aisle between racks of AI servers.
Rendered as two plates (variant "capitol" / "aisle") and joined with a soft light seam by compose_split().
Title space: the dark night sky, top left."""
import math
import bpy
from mathutils import Vector
from kit import pbr, emissive, box, haze
from human import pose_walk
from people import woman
from thumbkit import *

EXPOSURE = 0.0
VIGNETTE = 0.6


def build(variant=None):
    if variant == "capitol":
        import sc_capitol
        c = sc_capitol.build("night")
        bpy.context.scene.view_settings.exposure = -0.7
        # cold moonlight from above-left, a deep blue sky
        sun_o = bpy.data.objects.new("Moon", bpy.data.lights.new("Moon", 'SUN')); bpy.context.collection.objects.link(sun_o)
        sun_o.data.energy = 0.25; sun_o.data.color = (0.45, 0.6, 1.0); sun_o.rotation_euler = (math.radians(55), 0, math.radians(-30))
        bpy.context.scene.world.node_tree.nodes["Background"].inputs['Color'].default_value = (0.004, 0.008, 0.025, 1)
        for o in bpy.data.objects:
            if o.type == 'LIGHT' and o.name.startswith("Flood"):
                o.data.color = (0.75, 0.85, 1.0)
        c["cam"] = (Vector((-26, -175, 3.5)), Vector((0, 0, 47)), 38)
        c["focus"] = Vector((0, 0, 40)); c["fstop"] = 16
        c["shift"] = (0.22, 0.04)
        return c
    import sc_dchall
    c = sc_dchall.build("on")
    for o in bpy.data.objects:                          # the empty hall: no technicians, no open tray
        if o.name.startswith(("Tech", "Chassis")):
            o.hide_render = True
    # turn the hall red: strips dim and red, LEDs red, a red haze
    for m in bpy.data.materials:
        if m.name.startswith("Strip") and m.use_nodes:
            p = m.node_tree.nodes["Principled BSDF"]
            p.inputs['Emission Color'].default_value = (1.0, 0.05, 0.03, 1); p.inputs['Emission Strength'].default_value = 3.0
        if m.name.startswith(("LedGreen", "LedBlue")):
            for n in m.node_tree.nodes:
                if n.type == 'EMISSION':
                    n.inputs['Color'].default_value = (1.0, 0.04, 0.02, 1)
    for o in bpy.data.objects:
        if o.type == 'LIGHT':
            o.data.color = (1.0, 0.08, 0.05); o.data.energy *= 0.35
    for o in bpy.data.objects:
        if o.name.startswith(("Ceil", "Floor", "Wall")) and o.type == 'MESH':
            for m in o.data.materials:
                if m and "Principled BSDF" in m.node_tree.nodes:
                    p = m.node_tree.nodes["Principled BSDF"]
                    p.inputs['Base Color'].default_value = tuple(v * 0.35 for v in p.inputs['Base Color'].default_value[:3]) + (1,)
    bpy.context.scene.frame_set(40)
    # backlight at the end of the aisle: she walks into it
    soft(Vector((0, 19.5, 1.8)), Vector((0, 5, 1.3)), 500, (1.0, 0.1, 0.06), size=2.5, name="EndGlow")
    bpy.context.scene.view_settings.exposure = -0.6
    haze((0, 8, 1.8), (6, 26, 3.6), density=0.014, color=(1.0, 0.9, 0.9), anis=0.5)
    w = woman("Woman")
    pose_walk(w, 0.3, stride=22, arm_swing=12)
    place(w, (0.15, 8.2, 0), 180)
    ground(w, 0.0)
    rim = soft(Vector((0.0, 11.5, 2.8)), Vector((0.15, 8.2, 1.3)), 120, (1.0, 0.15, 0.08), size=0.8, name="HerRim")
    c["cam"] = (Vector((0.05, -1.8, 1.35)), Vector((0.0, 16.0, 1.3)), 32)
    c["focus"] = Vector((0.15, 8.2, 1.2)); c["fstop"] = 4.0
    c["shift"] = (-0.2, 0.02)
    return c


def compose_split(left_png, right_png, out_png, seam=0.5, soft_px=0.06):
    """Join the two plates: soft vertical blend at `seam` (fraction of width), with a faint red light line."""
    from PIL import Image
    import numpy as np
    a = np.asarray(Image.open(left_png).convert("RGB")).astype(np.float32) / 255
    b = np.asarray(Image.open(right_png).convert("RGB").resize((a.shape[1], a.shape[0]))).astype(np.float32) / 255
    H, W, _ = a.shape
    x = np.linspace(0, 1, W)[None, :, None]
    y = np.linspace(0, 1, H)[:, None, None]
    edge = seam + 0.04 * (y - 0.5)                   # a slight lean to the seam
    t = np.clip((x - edge) / soft_px + 0.5, 0, 1)
    img = a * (1 - t) + b * t
    line = np.exp(-((x - edge) / 0.004) ** 2) * (0.35 + 0.4 * (1 - y))
    img = 1 - (1 - img) * (1 - line * np.array([1.0, 0.18, 0.12])[None, None, :])
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out_png)
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((1280, 720), Image.LANCZOS).save(out_png.replace(".png", "_1280.png"))
