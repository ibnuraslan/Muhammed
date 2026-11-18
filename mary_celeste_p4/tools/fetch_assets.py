"""Pre-download every Poly Haven asset Part 4 uses (with retries). blender -b --python tools/fetch_assets.py"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import p4, ph, bpy
TEX = ["seaworn_sandstone_brick", "cobblestone_floor_04", "yellow_plaster", "red_plaster_weathered", "yellow_plaster_02",
       "painted_plaster_wall", "clay_plaster", "red_slate_roof_tiles_01", "brown_planks_05", "dark_wooden_planks", "weathered_planks",
       "wood_table_worn", "white_oak_veneer", "red_oak_veneer", "wood_table_large", "oak_veneer_01", "slate_floor"]
MOD = ["wine_barrel_01", "wooden_lantern_01", "vintage_oil_lamp", "seadogs_compass", "cross_pein_hammer", "wooden_bucket_01"]
HDR = ["belfast_sunset_puresky", "kiara_1_dawn", "mud_road_puresky"]
def retry(f, *a, **k):
    for i in range(6):
        try:
            return f(*a, **k)
        except Exception as e:
            print("retry", a, e); time.sleep(3 * (i + 1))
    raise RuntimeError(a)
for t in TEX: retry(ph.texture, t); print("ok", t)
for m in MOD: retry(ph.fetch_model, m); print("ok", m)
for h in HDR:
    for r in ("4k", "8k"):
        try: retry(ph.hdri, h, r)
        except Exception as e: print("no", h, r)
    print("ok", h)
