"""Group qa_check.py flags into frame ranges per kind.  python3 qa_summary.py qa.json"""
import json, sys
d = json.load(open(sys.argv[1])); fr = d["frames"]
items = sorted(((int(k), v) for k, v in fr.items()), key=lambda x: x[0]) if isinstance(fr, dict) else [(x["frame"], x["flags"]) for x in fr]
runs = {}
for f, fl in items:
    for kind, why in (fl or []):
        r = runs.setdefault(kind, [])
        if r and f - r[-1][1] <= 6 and r[-1][2] == why.split(",")[0][:30]: r[-1][1] = f
        else: r.append([f, f, why.split(",")[0][:30]])
for k, r in runs.items():
    print(k, len(r), "ranges:", ", ".join("%d-%d (%s)" % (a, b, w) for a, b, w in r))
print("COUNTS", d["counts"])
