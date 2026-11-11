"""CC0 assets from Poly Haven.  python3 -I fetch_polyhaven.py <dest_dir> <res e.g. 2k> <asset_id> [asset_id ...]
HDRIs -> <dest>/hdri/<id>_<res>.hdr ; textures -> <dest>/<id>/ (diff, nor_gl, rough, disp) ; models -> <dest>/<id>/ (.blend + textures).
Prints the authors for CREDITS.md. Poly Haven rejects Python's default User-Agent, hence the header."""
import sys, os, json, urllib.request
H = {"User-Agent": "blender-asset-fetch/1.0"}
def op(u): return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60)
def get(u): return json.load(op(u))
def dl(u, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p): open(p, "wb").write(op(u).read())
    print(" ", p)
dest, res, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
for a in ids:
    f = get("https://api.polyhaven.com/files/" + a); info = get("https://api.polyhaven.com/info/" + a)
    if "hdri" in f:
        dl(f["hdri"][res]["hdr"]["url"], f"{dest}/hdri/{a}_{res}.hdr")
    elif "blend" in f:
        b = f["blend"][res]["blend"]; dl(b["url"], f"{dest}/{a}/{os.path.basename(b['url'])}")
        for rel, inc in b.get("include", {}).items(): dl(inc["url"], f"{dest}/{a}/{rel}")
    else:
        for k in ["Diffuse", "nor_gl", "Rough", "Displacement"]:
            if k in f and res in f[k]:
                e = f[k][res]; fmt = "jpg" if "jpg" in e else list(e)[0]; dl(e[fmt]["url"], f"{dest}/{a}/{os.path.basename(e[fmt]['url'])}")
    print("CREDIT", a, "|", info.get("name"), "|", ", ".join(info.get("authors", {})), "| CC0 polyhaven.com")
