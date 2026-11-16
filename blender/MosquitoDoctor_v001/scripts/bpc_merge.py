"""merge range runs of body_prop_cross into review/P1_body_prop_cross.json + a summary. python3 bpc_merge.py out.json summary.txt in1.json ..."""
import json, sys, collections
out, summ, ins = sys.argv[1], sys.argv[2], sys.argv[3:]
frames = {}
for p in ins: frames.update(json.load(open(p))["frames"])
vis = sorted(int(f) for f, h in frames.items() if any(k.endswith("VIS") for k in h))
json.dump({"visible_frames": vis, "frames": frames, "sources": ins}, open(out, "w"), indent=0)
fr = collections.defaultdict(set)
for f, h in frames.items():
    for k in h:
        if k.endswith("VIS"): fr[k.rsplit("|", 1)[0]].add(int(f))
L = [f"body_prop_cross, step 3, frames 1-3190 (all rigs), props: Vial, Cork, Pen, notebook, blankets, desk, chairs, basin, bed, cutaway lining",
     f"frames sampled: {len(frames) and len(set(int(f) for f in frames))} with any hit; frames with a VISIBLE crossing: {len(vis)}"]
for k, v in sorted(fr.items(), key=lambda x: min(x[1])): L.append(f"  {k}: frames {min(v)}-{max(v)} ({len(v)} samples)")
open(summ, "w").write("\n".join(L) + "\n"); print("\n".join(L))
