"""Build the MH_DATA layout lib/human.py reads from what the studio environment already has installed
(MPFB 2 + the MakeHuman CC0 system assets + the `makehuman` PyPI wheel), for machines that cannot reach
download.tuxfamily.org. Converts MPFB's standard rig (rig.default.json / weights.default.json) to MakeHuman 1.x
default.mhskel / default_weights.mhw, with the 1.x joint names (`<bone>____head`, `<bone>____tail`, `joint-*`).

Usage: python3 tools/mh_from_mpfb.py <makehuman wheel or unpacked dir with makehuman/data/targets.npz> [out_dir]
       (out_dir defaults to assets/makehuman)
"""
import os, sys, json, shutil, zipfile, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mh_compile import read_obj, compile_mhclo

MPFB = os.path.expanduser("~/.config/blender/5.2/extensions/user_default/mpfb/data")
SYS = os.path.expanduser("~/.config/blender/5.2/extensions/.user/user_default/mpfb/data")


def main(wheel, out):
    os.makedirs(os.path.join(out, "rigs"), exist_ok=True); os.makedirs(os.path.join(out, "3dobjs"), exist_ok=True)
    o = read_obj(os.path.join(MPFB, "3dobjs", "base.obj"))
    np.savez(os.path.join(out, "3dobjs", "base.npz"), **o)
    names = bytes(o["fgstr"]).decode(); idx = list(o["fgidx"]) + [len(names)]
    gn = [names[idx[i]:idx[i + 1]] for i in range(len(idx) - 1)]
    groups = {}
    for f, g in zip(o["fvert"], o["group"]):
        groups.setdefault(gn[g], set()).update(int(x) for x in f)
    rig = json.load(open(os.path.join(MPFB, "rigs", "standard", "rig.default.json")))
    joints, bones = {}, {}
    for b, v in rig.items():
        ends = {}
        for end in ("head", "tail"):
            e = v[end]; s = e["strategy"]
            if s == "CUBE":
                verts = sorted(groups[e["cube_name"]]); joints[e["cube_name"]] = verts
            elif s == "VERTEX":
                verts = [e["vertex_index"]]
            else:
                verts = list(e["vertex_indices"])
            joints[f"{b}____{end}"] = verts; ends[end] = f"{b}____{end}"
        bones[b] = dict(head=ends["head"], tail=ends["tail"], parent=v.get("parent") or None, roll=v.get("roll", 0.0))
    json.dump(dict(bones=bones, joints=joints), open(os.path.join(out, "rigs", "default.mhskel"), "w"))
    shutil.copy(os.path.join(MPFB, "rigs", "standard", "weights.default.json"), os.path.join(out, "rigs", "default_weights.mhw"))
    tg = os.path.join(out, "targets.npz")
    if wheel.endswith(".whl"):
        with zipfile.ZipFile(wheel) as z, open(tg, "wb") as f:
            f.write(z.read("makehuman/data/targets.npz"))
    else:
        shutil.copy(os.path.join(wheel, "makehuman", "data", "targets.npz"), tg)
    compile_mhclo(os.path.join(SYS, "eyes", "high-poly", "high-poly.mhclo"), os.path.join(out, "eyes", "high-poly"))
    for d in ("skins", "eyebrows", "eyelashes", "clothes", "hair", "proxymeshes", "teeth", "tongue"):
        p = os.path.join(out, d)
        if not os.path.exists(p) and os.path.exists(os.path.join(SYS, d)):
            os.symlink(os.path.join(SYS, d), p)
    print("ok", out, len(bones), "bones", len(joints), "joints")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "assets", "makehuman"))
