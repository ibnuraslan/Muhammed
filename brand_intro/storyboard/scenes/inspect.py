import sys, bpy
sys.path.insert(0, "/home/user/Muhammed/wt_antwerp/antwerp_heist/3d/lib")
import sf
from mathutils import Vector
for uid in ["78f76d386a4341b0b71745bdc50fd5ab", "20cd135432134121ac6e9c73164460c2", "5e660c4543cf452d87537394574c5190",
            "bd339489b2524d6583aaf9275d5bbfd8", "032cc5ff2eac42ef888c032e081618e1", "812e8f59f9e749fab483eabf4800dec2"]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        p = sf.fetch(uid)
        bpy.ops.import_scene.gltf(filepath=p)
    except Exception as e:
        print("FAIL", uid, e); continue
    bpy.context.view_layer.update()
    ms = [o for o in bpy.data.objects if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in ms for c in o.bound_box]
    mn = [min(q[i] for q in pts) for i in range(3)]; mx = [max(q[i] for q in pts) for i in range(3)]
    print("MODEL", uid, open(p.replace(".glb", ".json")).read())
    print("  dims", [round(mx[i] - mn[i], 3) for i in range(3)], "n", len(ms))
    for o in ms[:25]:
        print("   ", o.name, len(o.data.vertices), [m.name for m in o.data.materials][:3])
