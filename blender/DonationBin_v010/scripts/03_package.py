"""DonationBin v010 stage C: VO strip, frame range, purge, then the farm package (pipeline/package_for_farm.py).
blender -b anim.blend --python 03_package.py -- <vo.mp3> <out_dir>/DonationBin_v010_60fps.blend"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]
VO, OUTB = a[0], a[1]
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 2388
# the client's voiceover from frame 1
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
strips = getattr(se, "strips", None) or se.sequences
for s_ in list(strips): strips.remove(s_)
snd = strips.new_sound("VO", VO, 1, 1)
snd.sound.pack()
# helper objects never render; the temporary off-set copies are removed
for o in list(bpy.data.objects):
    if o.name in ("SparkInst",):
        o.hide_render = True
for m in bpy.data.objects:
    for md in getattr(m, "modifiers", []):
        if md.type == 'SUBSURF': md.show_viewport = True
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
sys.argv = [sys.argv[0], "--", OUTB]
exec(open("/home/user/Muhammed/blender/pipeline/package_for_farm.py").read())
