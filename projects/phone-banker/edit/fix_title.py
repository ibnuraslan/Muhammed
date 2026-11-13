"""Re-point a chapter-opening shot at a freshly generated title card (written into the shared texture folder, never
into nvidia_doc/assets/generated, which is a tracked file all bakes share).
  python edit/fix_title.py <shot.blend> "CHAPTER 1" "TWO HOSPITALS" """
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "nvidia_doc", "scenes")))
import bpy
import title_card
f, small, big = os.path.abspath(sys.argv[-3]), sys.argv[-2], sys.argv[-1]
tex = os.path.join(os.path.dirname(os.path.dirname(f)), "textures")
target = os.path.join(tex, f"title_{os.path.splitext(os.path.basename(f))[0]}_ChapterTitle.png")
title_card.title_image(small, big, target)
bpy.ops.wm.open_mainfile(filepath=f)
n = 0
for im in bpy.data.images:
    if "ChapterTitle" in im.name or "ChapterTitle" in im.filepath:
        im.filepath = bpy.path.relpath(target); im.reload(); n += 1
bpy.ops.wm.save_mainfile(filepath=f, compress=True)
if os.path.exists(f + "1"):
    os.remove(f + "1")
print(f"[title] {os.path.basename(f)}: {n} image(s) -> {os.path.basename(target)}", flush=True)
