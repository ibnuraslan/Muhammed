import sys, json
sys.path.insert(0, sys.argv[1])
from fs_search import search
Q = json.load(open(sys.argv[2]))
res = {}
for key, (q, mn, mx) in Q.items():
    r = search(q, mn, mx, 1)[:7]
    res[key] = r
    print(f"## {key} [{q}]")
    for o in r:
        print(f"   {o['id']:>7} {o['dl']:>6} {o['dur']:6.1f}s  {o['title'][:60]} / {o['user']}")
json.dump(res, open(sys.argv[3], "w"))
