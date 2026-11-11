"""Find downloadable CC-BY / CC0 Sketchfab models that are mirrored in Objaverse, and download them as GLB.
python3 -I find_models.py search <cache_dir> "goat" "dairy cow" ...   -> <cache>/search.json + thumbnails sheet <cache>/search.jpg
python3 -I find_models.py get <cache_dir> <out_dir> <name>=<uid> ...  -> <out>/<name>.glb + <out>/credits.json
Check the thumbnail sheet before choosing. Every CC-BY model must go in CREDITS.md and the video description."""
import sys, os, json, gzip, urllib.request, urllib.parse, io
H = {"User-Agent": "asset-survey/1.0"}
HF = "https://huggingface.co/datasets/allenai/objaverse/resolve/main/"
OK = ("CC Attribution", "CC0 Public Domain", "Public Domain")
def op(u, t=60): return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=t)
def paths(cache):
    p = os.path.join(cache, "object-paths.json.gz")
    if not os.path.exists(p): os.makedirs(cache, exist_ok=True); open(p, "wb").write(op(HF + "object-paths.json.gz", 300).read())
    return json.load(gzip.open(p))
mode, cache = sys.argv[1], sys.argv[2]
P = paths(cache)
if mode == "search":
    res = {}
    for q in sys.argv[3:]:
        url = "https://api.sketchfab.com/v3/search?" + urllib.parse.urlencode({"type": "models", "q": q, "count": 24, "downloadable": "true"})
        hits = []
        for _ in range(3):
            try: d = json.load(op(url, 25))
            except Exception as e: print("ERR", q, e); break
            for r in d.get("results", []):
                lic = (r.get("license") or {}).get("label") or ""
                if r["uid"] in P and lic in OK and (r.get("faceCount") or 0) < 400000:
                    th = sorted(r.get("thumbnails", {}).get("images", []), key=lambda x: x["width"])
                    hits.append(dict(uid=r["uid"], name=r["name"], license=lic, faces=r.get("faceCount"),
                                     author=(r.get("user") or {}).get("displayName"), profile=(r.get("user") or {}).get("profileUrl"),
                                     thumb=next((x["url"] for x in th if x["width"] >= 300), th[-1]["url"] if th else "")))
            url = d.get("next")
            if not url or len(hits) >= 8: break
        res[q] = hits[:8]
        for h in res[q]: print(q, "|", h["uid"], "|", h["name"], "|", h["author"], "|", h["license"], "|", h["faces"], "faces")
    json.dump(res, open(os.path.join(cache, "search.json"), "w"), indent=1)
    try:
        from PIL import Image, ImageDraw
        cells = [(q, i, h) for q, hs in res.items() for i, h in enumerate(hs)]
        S = Image.new("RGB", (8 * 200, 220 * max(1, len(res))), "white"); rows = {q: k for k, q in enumerate(res)}
        for q, i, h in cells:
            try: im = Image.open(io.BytesIO(op(h["thumb"], 20).read())).convert("RGB").resize((200, 200))
            except Exception: continue
            S.paste(im, (i * 200, rows[q] * 220)); ImageDraw.Draw(S).text((i * 200 + 2, rows[q] * 220 + 202), f"{q}#{i} {h['uid'][:8]}", fill=(0, 0, 0))
        S.save(os.path.join(cache, "search.jpg"), quality=80); print("SHEET", os.path.join(cache, "search.jpg"))
    except ImportError: pass
elif mode == "get":
    out = sys.argv[3]; os.makedirs(out, exist_ok=True)
    cf = os.path.join(out, "credits.json"); credits = json.load(open(cf)) if os.path.exists(cf) else {}
    for spec in sys.argv[4:]:
        name, uid = spec.split("=")
        open(os.path.join(out, name + ".glb"), "wb").write(op(HF + P[uid], 300).read())
        m = json.load(op("https://api.sketchfab.com/v3/models/" + uid, 25))
        credits[name] = dict(uid=uid, title=m.get("name"), author=(m.get("user") or {}).get("displayName"),
                             author_profile=(m.get("user") or {}).get("profileUrl"), license=(m.get("license") or {}).get("label"),
                             source="https://sketchfab.com/3d-models/" + uid, via="Objaverse (allenai/objaverse on Hugging Face)")
        print("GOT", name, credits[name]["title"], "by", credits[name]["author"], credits[name]["license"])
    json.dump(credits, open(cf, "w"), indent=1)
