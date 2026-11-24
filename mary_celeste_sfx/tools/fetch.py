"""Download HQ previews of picked Freesound sounds after verifying CC0 on each sound page."""
import json, sys, os, re, subprocess, html
res = {}
for f in sys.argv[2:]:
    for k, lst in json.load(open(f)).items():
        for o in lst:
            res[o["id"]] = o
pick = json.load(open(sys.argv[1]))
outdir = "lib_cc0"; os.makedirs(outdir, exist_ok=True)
credits = []
for cat, ids in pick.items():
    for i in ids:
        o = res.get(str(i))
        if not o:
            print("MISSING", i); continue
        page = f"https://freesound.org/people/{o['user']}/sounds/{i}/"
        s = subprocess.run(["curl", "-s", "-L", "-m", "30", page], capture_output=True, text=True).stdout
        cc0 = "publicdomain/zero" in s or "Creative Commons 0" in s
        lic = re.findall(r'creativecommons\.org/(licenses|publicdomain)/([a-z\-]+)/?([0-9.]*)', s)
        if not cc0 or any(l[0] == "licenses" for l in lic[:1]):
            print("NOT CC0?", i, o["title"], lic[:3]); continue
        url = o["mp3"].replace("-lq.mp3", "-hq.mp3")
        dst = os.path.join(outdir, f"{cat}_{i}.mp3")
        if not os.path.exists(dst):
            open("dl/urls.txt", "a").write(f"{url} {dst}\n")
        credits.append(dict(file=os.path.basename(dst), id=i, title=o["title"], user=o["user"], url=page, licence="CC0 1.0"))
        print("ok", cat, i, o["title"][:50], flush=True)
json.dump(credits, open(os.path.join(outdir, "credits.json"), "w"), indent=1)
