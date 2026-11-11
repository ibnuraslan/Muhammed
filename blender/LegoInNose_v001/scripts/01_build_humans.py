"""Build the four MPFB2 characters (MakeHuman CC0 assets): Boy (~7), Teen (~15), Man (~33), Mom.
blender -b --python 01_build_humans.py -- <out.blend>
Expression units (MakeHuman CC0 face targets) are loaded as shape keys on each basemesh: expr_<unit>."""
import sys, os
import bpy
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService

out = sys.argv[sys.argv.index("--") + 1]
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

EXPR_DIR = os.path.join(os.path.dirname(TargetService.__module__ and sys.modules[TargetService.__module__].__file__),
                        "..", "data", "targets", "expression", "units", "caucasian")
EXPR = ["mouth-corner-puller", "mouth-open", "mouth-pursing", "mouth-depression", "mouth-elevation",
        "eyebrows-left-up", "eyebrows-right-up", "eyebrows-left-inner-up", "eyebrows-right-inner-up",
        "eyebrows-left-down", "eyebrows-right-down", "eye-left-opened-up", "eye-right-opened-up",
        "eye-left-slit", "eye-right-slit", "nose-left-dilatation", "nose-right-dilatation", "nose-compression"]

CHARS = [
    ("Boy", dict(gender=1.0, age=0.13, muscle=0.5, weight=0.5, proportions=0.5, height=0.7),
     "young_caucasian_male/young_caucasian_male.mhmat", "short02/short02.mhclo",
     ["male_casualsuit03/male_casualsuit03.mhclo", "shoes01/shoes01.mhclo"], "eyebrow001/eyebrow001.mhclo", 1),
    ("Teen", dict(gender=1.0, age=0.28, muscle=0.45, weight=0.45, proportions=0.55, height=0.5),
     "young_caucasian_male/young_caucasian_male.mhmat", "short02/short02.mhclo",
     ["male_casualsuit04/male_casualsuit04.mhclo", "shoes01/shoes01.mhclo"], "eyebrow001/eyebrow001.mhclo", 0),
    ("Man", dict(gender=1.0, age=0.56, muscle=0.55, weight=0.55, proportions=0.6, height=0.55),
     "young_caucasian_male/young_caucasian_male.mhmat", "short02/short02.mhclo",
     ["male_casualsuit01/male_casualsuit01.mhclo", "shoes01/shoes01.mhclo"], "eyebrow001/eyebrow001.mhclo", 1),
    ("Mom", dict(gender=0.0, age=0.5, muscle=0.5, weight=0.5, proportions=0.6, height=0.5, cupsize=0.5, firmness=0.5),
     "young_caucasian_female/young_caucasian_female.mhmat", "ponytail01/ponytail01.mhclo",
     ["female_casualsuit01/female_casualsuit01.mhclo", "shoes02/shoes02.mhclo"], "eyebrow010/eyebrow010.mhclo", 1),
]
for i, (name, ph, skin, hair, clothes, brow, subd) in enumerate(CHARS):
    info = HumanService._create_default_human_info_dict()
    info["name"] = name
    p = {"gender": 0.5, "age": 0.5, "muscle": 0.5, "weight": 0.5, "proportions": 0.5, "height": 0.5,
         "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.05, "caucasian": 0.9, "african": 0.05}}
    p.update(ph); info["phenotype"] = p
    info["rig"] = "default"
    info["eyes"] = "high-poly/high-poly.mhclo"; info["eyebrows"] = brow
    info["eyelashes"] = "eyelashes01/eyelashes01.mhclo"; info["teeth"] = "teeth_base/teeth_base.mhclo"
    info["tongue"] = "tongue01/tongue01.mhclo"; info["hair"] = hair; info["clothes"] = clothes
    info["skin_mhmat"] = skin; info["skin_material_type"] = "ENHANCED_SSS"; info["eyes_material_type"] = "PROCEDURAL_EYES"
    st = HumanService.get_default_deserialization_settings(); st["subdiv_levels"] = subd
    before = set(bpy.data.objects)
    bm = HumanService.deserialize_from_dict(info, st)
    new = set(bpy.data.objects) - before
    arm = [o for o in new if o.type == "ARMATURE"][0]
    arm.name = name
    bm.name = name + "_Body"
    for o in new:
        if o.type == "MESH" and o is not bm and not o.name.startswith(name + "_"):
            o.name = name + "_" + o.name
    # expression units as shape keys (weight 0)
    nk = 0
    for u in EXPR:
        fp = os.path.normpath(os.path.join(EXPR_DIR, u + ".target.gz"))
        if os.path.exists(fp):
            try:
                TargetService.load_target(bm, fp, weight=0.0, name="expr_" + u); nk += 1
            except Exception as e:
                print("EXPR_FAIL", name, u, e)
    arm.location.x = i * 1.5
    print("HUMAN", name, "expr", nk, sorted(o.name for o in new), tuple(round(d, 3) for d in bm.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=out)
