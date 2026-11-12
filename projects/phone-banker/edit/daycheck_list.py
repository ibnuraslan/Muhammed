"""List every shot with its look recipe: name set move seconds recipe (for the day-brightness check)."""
import os, sys, json, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scenes")); sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "nvidia_doc", "scenes"))
import pblook
T = json.load(open(os.path.join(HERE, "..", "vo", "timing.json")))
for part in ("intro", "ch1", "ch2", "ch3"):
    for r in T[part]["shots"]:
        mod = importlib.import_module("sc_" + r["set"])
        v = getattr(mod, "VARIANT_FOR", {}).get(r["move"])
        plan = pblook.PLAN.get("sc_" + r["set"], {})
        rec = plan.get(v, plan.get(None, ("keep", {})))[0]
        print(part, r["name"], r["set"], r["move"], r["seconds"], rec, v)
