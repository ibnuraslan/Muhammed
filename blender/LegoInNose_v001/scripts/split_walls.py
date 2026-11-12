"""v008b: shared walls were built twice in the same 12 cm slab (LR east = BR west at x 2.8, BR east = BA west at x 6.4) and
z-fought (the dark back of the bathroom tiles showed through the bedroom wall at 30.5 s). Each room keeps its own 6 cm half.
exec'd at the end of 02_build_sets.py, or: blender -b in.blend --python split_walls.py -- out.blend"""
import bpy, sys
def _split(pfx_a, side_a, pfx_b, side_b):
    for o in bpy.data.objects:
        for pfx, side, sgn in ((pfx_a, side_a, -1), (pfx_b, side_b, +1)):     # room A lies at -x of the wall, room B at +x
            if o.type == "MESH" and o.name.startswith("%s_Wall%s" % (pfx, side)) and abs(o.scale.x - 1) < 1e-6:
                o.scale.x = 0.5; o.location.x += sgn * 0.03
for a_, b_ in ((("LR", "E"), ("BR", "W")), (("BR", "E"), ("BA", "W"))): _split(a_[0], a_[1], b_[0], b_[1])
print("SPLIT_WALLS", sorted((o.name, round(o.location.x, 3)) for o in bpy.data.objects if o.name.startswith(("LR_WallE", "BR_WallW", "BR_WallE", "BA_WallW"))))
if __name__ == "__main__" and not globals().get("_IN_BUILD_SETS"):
    bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index("--") + 1], compress=True)
