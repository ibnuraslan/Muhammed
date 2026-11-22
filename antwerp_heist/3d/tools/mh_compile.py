"""Compile MakeHuman 1.x source assets (base.obj, .mhclo) into the .npz layout scenes/lib/human.py reads.
Usage: python3 mh_compile.py <makehuman source data dir> <targets.npz> <out MH_DATA dir>"""
import os, sys, shutil, numpy as np


def read_obj(path):
    v, vt, fv, fu, grp, gnames = [], [], [], [], [], []
    g = 0
    for line in open(path, encoding="utf8", errors="ignore"):
        w = line.split()
        if not w:
            continue
        if w[0] == "v":
            v.append([float(x) for x in w[1:4]])
        elif w[0] == "vt":
            vt.append([float(x) for x in w[1:3]])
        elif w[0] == "g":
            n = w[1] if len(w) > 1 else "default"
            if n not in gnames:
                gnames.append(n)
            g = gnames.index(n)
        elif w[0] == "f":
            a = [x.split("/") for x in w[1:]]
            vi = [int(x[0]) - 1 for x in a]; ui = [int(x[1]) - 1 if len(x) > 1 and x[1] else 0 for x in a]
            if len(vi) == 3:
                vi.append(vi[2]); ui.append(ui[2])
            fv.append(vi[:4]); fu.append(ui[:4]); grp.append(g)
    s = "".join(gnames).encode(); idx = np.cumsum([0] + [len(n.encode()) for n in gnames[:-1]])
    return dict(coord=np.array(v, np.float32), texco=np.array(vt or [[0, 0]], np.float32),
                fvert=np.array(fv, np.int64), fuvs=np.array(fu, np.int64), group=np.array(grp, np.int64),
                fgstr=np.frombuffer(s, np.uint8), fgidx=np.array(idx, np.int64))


def compile_mhclo(path, out_dir):
    refs, ws, offs, scale, scale_idx, obj, mat, dele = [], [], [], [0.0] * 3, [0] * 6, None, None, []
    mode = None
    for line in open(path, encoding="utf8", errors="ignore"):
        w = line.split()
        if not w or w[0].startswith("#"):
            continue
        k = w[0]
        if k in ("x_scale", "y_scale", "z_scale"):
            i = "xyz".index(k[0]); scale_idx[2 * i], scale_idx[2 * i + 1] = int(w[1]), int(w[2]); scale[i] = float(w[3])
        elif k == "obj_file":
            obj = w[1]
        elif k == "material":
            mat = w[1]
        elif k == "verts":
            mode = "v"
        elif k == "delete_verts":
            mode = "d"
        elif mode == "v" and len(w) == 9 and w[0].lstrip("-").isdigit():
            refs.append([int(x) for x in w[:3]]); ws.append([float(x) for x in w[3:6]]); offs.append([float(x) for x in w[6:9]])
        elif mode == "v" and len(w) == 1 and w[0].isdigit():
            refs.append([int(w[0])] * 3); ws.append([1.0, 0, 0]); offs.append([0, 0, 0])
        elif mode == "d":
            for x in w:
                if "-" in x:
                    a, b = x.split("-"); dele += list(range(int(a), int(b) + 1))
                elif x.isdigit():
                    dele.append(int(x))
    name = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(out_dir, exist_ok=True)
    o = read_obj(os.path.join(os.path.dirname(path), obj))
    np.savez(os.path.join(out_dir, os.path.splitext(obj)[0] + ".npz"), fvert=o["fvert"], fuvs=o["fuvs"], texco=o["texco"])
    d = dict(ref_vIdxs=np.array(refs, np.int64), weights=np.array(ws, np.float32), offsets=np.array(offs, np.float32),
             tmat_scale=np.array(scale, np.float32), tmat_scale_idx=np.array(scale_idx, np.int64),
             obj_file=np.frombuffer(obj.encode(), np.uint8))
    if mat:
        d["material_file"] = np.frombuffer(mat.encode(), np.uint8)
    if dele:
        dv = np.zeros(13380 + 6000, bool); dv[dele] = True; d["deleteVerts"] = dv
    np.savez(os.path.join(out_dir, name + ".mhpxy"), **d)
    os.replace(os.path.join(out_dir, name + ".mhpxy.npz"), os.path.join(out_dir, name + ".mhpxy"))


if __name__ == "__main__":
    src, tg, out = sys.argv[1:4]
    os.makedirs(os.path.join(out, "3dobjs"), exist_ok=True)
    np.savez(os.path.join(out, "3dobjs", "base.npz"), **read_obj(os.path.join(src, "3dobjs", "base.obj")))
    shutil.copytree(os.path.join(src, "rigs"), os.path.join(out, "rigs"), dirs_exist_ok=True)
    shutil.copy(tg, os.path.join(out, "targets.npz"))
    compile_mhclo(os.path.join(src, "eyes", "high-poly", "high-poly.mhclo"), os.path.join(out, "eyes", "high-poly"))
    print("ok", out)
