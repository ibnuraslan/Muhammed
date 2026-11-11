"""Downscale large images to 1K (hero skin 2K) before packing. Three steps (Blender has no PIL):
  blender -b anim.blend --python 04_shrink_textures.py -- list plan.json
  python3 -I 04_shrink_textures.py convert plan.json
  blender -b anim.blend --python 04_shrink_textures.py -- apply plan.json out.blend"""
import sys, os, json
try:
    import bpy; a = sys.argv[sys.argv.index("--") + 1:]
except ImportError:
    bpy = None; a = sys.argv[1:]
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/assets/tex_small"
mode, plan = a[0], a[1]
if mode == "list":
    hero = {n.image.name for o in bpy.data.objects["Hero"].children if o.type == "MESH" and o.name.endswith(".body")
            for m in o.data.materials for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image}
    P = []
    for im in bpy.data.images:
        if im.source != "FILE": continue
        p = bpy.path.abspath(im.filepath); lim = 2048 if im.name in hero else 1024
        if os.path.exists(p) and not p.endswith((".hdr", ".exr")) and max(im.size) > lim:
            P.append({"name": im.name, "src": p, "lim": lim})
    json.dump(P, open(plan, "w"), indent=0); print("PLAN", len(P))
elif mode == "convert":
    from PIL import Image
    os.makedirs(D, exist_ok=True); P = json.load(open(plan)); saved = 0
    for e in P:
        pi = Image.open(e["src"]); pi.thumbnail((e["lim"], e["lim"]), Image.LANCZOS)
        base = os.path.splitext(os.path.basename(e["src"]))[0]
        alpha = pi.mode in ("RGBA", "LA") and pi.getextrema()[-1][0] < 255
        if alpha or "normal" in base: q = os.path.join(D, base + "_s.png"); pi.save(q, optimize=True)
        else: q = os.path.join(D, base + "_s.jpg"); pi.convert("RGB").save(q, quality=90)
        e["dst"] = q; saved += os.path.getsize(e["src"]) - os.path.getsize(q)
    json.dump(P, open(plan, "w"), indent=0); print("CONVERTED", len(P), "saved MB", saved // 2**20)
elif mode == "apply":
    for e in json.load(open(plan)):
        im = bpy.data.images[e["name"]]; im.filepath = e["dst"]; im.reload()
    bpy.ops.wm.save_as_mainfile(filepath=a[2]); print("APPLIED")
