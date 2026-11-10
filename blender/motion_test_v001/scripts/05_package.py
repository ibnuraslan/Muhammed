"""Pack + verify the delivery file.  blender -b anim.blend --python 05_package.py -- <out.blend>"""
import sys, os, bpy
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
sc.frame_set(1)
sc.render.filepath = "//render/MotionTest_v001_"
bpy.ops.file.pack_all()
missing = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file]
drivers = []
for idb in list(bpy.data.objects) + list(bpy.data.meshes) + list(bpy.data.shape_keys) + list(bpy.data.armatures):
    ad = getattr(idb, "animation_data", None)
    if ad:
        for d in ad.drivers:
            drivers.append((idb.name, d.data_path, d.driver.type, d.driver.expression))
print("PACKED_IMAGES", sum(1 for i in bpy.data.images if i.packed_file), "UNPACKED", missing)
print("LIBRARIES", [l.filepath for l in bpy.data.libraries])
print("DRIVERS", len(drivers), sorted(set((t, e) for _, _, t, e in drivers))[:10])
print("CACHES", [m.name for o in bpy.data.objects for m in getattr(o, "modifiers", []) if m.type in ('MESH_SEQUENCE_CACHE', 'FLUID', 'CLOTH', 'PARTICLE_SYSTEM')])
print("CAMERAS", [o.name for o in bpy.data.objects if o.type == 'CAMERA'], "markers", len(sc.timeline_markers))
bpy.context.preferences.filepaths.use_file_compression = True
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
print("SAVED", OUT, os.path.getsize(OUT))
