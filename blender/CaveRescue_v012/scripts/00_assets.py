"""CaveRescue v012 stage 0: fetch the source assets into <ph_dir> (run with python3 -I).
python3 -I 00_assets.py <ph_dir>
 - Poly Haven CC0 textures/models/HDRI (pipeline/fetch_polyhaven.py)
 - the CC-BY ambulance (pipeline/find_models.py, Objaverse mirror of Sketchfab 2856dd3c61f940909dced9a5c0379484)
 - shvan_body_clean.png: the ambulance body texture with EVERY text/number/flag/symbol removed (only the red stripe
   panels kept on clean white): red mask -> morphological open/close (removes text strokes, fills holes) -> flat colours."""
import sys, os, subprocess, glob
PH = os.path.abspath(sys.argv[1]); PIPE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pipeline")
fp = os.path.join(PIPE, "fetch_polyhaven.py"); fm = os.path.join(PIPE, "find_models.py")
subprocess.run([sys.executable, "-I", fp, PH, "1k", "mossy_forest", "island_tree_01", "island_tree_02", "fern_02",
                "pachira_aquatica_01", "boulder_01", "pastic_torch_6v"], check=True)
subprocess.run([sys.executable, "-I", fp, PH, "2k", "cliff_side", "brown_mud_leaves_01", "forest_leaves_03"], check=True)
cache = os.path.join(PH, "_objaverse"); d = os.path.join(PH, "shvan")
subprocess.run([sys.executable, "-I", fm, "get", cache, d, "shvan=2856dd3c61f940909dced9a5c0379484"], check=True)
# extract the body texture (Image_8, 1024 px, used by material "Body") with Blender, then clean it
BL = "/opt/blender/blender-5.2.2-linux-x64/blender"
ex = ("import bpy\nbpy.ops.import_scene.gltf(filepath=%r)\n"
      "m=bpy.data.materials['Body']\nim=[n.image for n in m.node_tree.nodes if n.type=='TEX_IMAGE'][0]\n"
      "im.filepath_raw=%r; im.file_format='PNG'; im.save()\n") % (os.path.join(d, "shvan.glb"), os.path.join(d, "shvan_body_src.png"))
subprocess.run([BL, "-b", "--factory-startup", "--python-expr", ex], check=True)
from PIL import Image, ImageFilter
import numpy as np
im = np.asarray(Image.open(os.path.join(d, "shvan_body_src.png")).convert("RGB")).astype(float)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
red = ((r > 150) & (g < 90) & (b < 90)).astype(np.uint8) * 255
m = Image.fromarray(red).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(17)).filter(ImageFilter.MaxFilter(9))
m = np.asarray(m.filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.MinFilter(21))) > 127
out = np.zeros_like(im); out[...] = (232, 234, 238); out[m] = (205, 12, 12)
Image.fromarray(out.astype(np.uint8)).save(os.path.join(d, "shvan_body_clean.png"))
print("ASSETS_READY", PH)
