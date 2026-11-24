"""Search Freesound (CC0 only) via the public search page; print candidates as JSON lines."""
import sys, re, json, html, urllib.parse, subprocess
def search(q, mindur=0, maxdur=100000, pages=2, sort="Downloads (most first)"):
    out = []
    for p in range(1, pages + 1):
        f = f'license:"Creative Commons 0" duration:[{mindur} TO {maxdur}]'
        url = "https://freesound.org/search/?" + urllib.parse.urlencode({"q": q, "f": f, "s": sort, "page": p})
        s = subprocess.run(["curl", "-s", "-m", "30", url], capture_output=True, text=True).stdout
        for blk in s.split('class="bw-player"')[1:]:
            g = lambda k: (re.search(k + r'="([^"]*)"', blk) or [None, None])[1]
            out.append(dict(id=g("data-sound-id"), user=html.unescape(g("data-username") or ""), title=html.unescape(g("data-title") or ""),
                            dur=float(g("data-duration") or 0), dl=int(g("data-num-downloads") or 0), mp3=g("data-mp3")))
    seen, res = set(), []
    for o in out:
        if o["id"] and o["id"] not in seen:
            seen.add(o["id"]); res.append(o)
    return res
if __name__ == "__main__":
    q, mn, mx = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    for o in search(q, mn, mx, 1):
        print(json.dumps(o))
