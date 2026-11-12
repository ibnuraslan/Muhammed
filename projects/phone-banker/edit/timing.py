"""Cut every shot to the word its line starts on -> vo/timing.json and a printed table.

Each part's shots are taken in order from scenes/<part>.list (label|set|move|t); ANCHORS gives the phrase each
shot starts on (the first shot of a part starts at 0). The picture leads the voice: LEAD seconds before the first
word (intro 2.5 s; chapters 3.0 s under the title card). The last shot runs TAIL seconds past the last word.
"""
import os, sys, json, difflib
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "..", "..", "nvidia_doc", "edit"))
from align import norm_tokens, canon
FPS = 24
LEAD = {"intro": 2.5, "ch1": 3.0, "ch2": 3.0, "ch3": 3.0}
TAIL = {"intro": 1.2, "ch1": 1.5, "ch2": 1.5, "ch3": 3.0}

ANCHORS = {
    "intro": [None, "the phone belongs", "the substance on the handset", "among them are eight",
              "when investigators search", "on the one thing"],
    "ch1": [None, "is at work in moscow", "that afternoon he makes", "from the office according",
            "his brother comes by", "there's already a familiar", "by the time he reaches", "the next evening",
            "to a different hospital", "she's unconscious when", "the pathologist assigned", "neither he says fits",
            "later forensic experts", "and in blood samples", "when a nerve tells", "muscles can twitch",
            "back at the bank investigators", "the case files describe", "how zara came", "but the phone is still",
            "at kivalidi's memorial", "include mikhail gorbachev", "at the bank the investigation", "who had been inside"],
    "ch2": [None, "he visits the office", "investigators believe he spends", "they also find a potential",
            "police detain him", "they have a visitor", "the lab work points", "the trail leads to a closed",
            "in shihani leonid rink", "that develops chemical weapons", "rink describes a handover",
            "and was paid for it", "investigators believe that a batch", "prosecutors trace an ampoule",
            "in their account he takes", "and puts the poison on", "by december 1999", "nearly seven years",
            "in june 2006", "outside an apartment building"],
    "ch3": [None, "prosecutors argue the evidence", "khutashwili denies", "his defense says",
            "on december 24th 2007", "it finds him guilty", "he later wins early release", "the court reaches a verdict",
            "then in 2018", "the attack on sergei", "the british public inquiry", "placed on the handle",
            "in moscow the object", "novaya gazeta publishes", "residue from the handset", "other specialists dispute",
            "rink gives a new account", "that account conflicts", "the evidence photograph", "the files that later"],
}


def shots_of(part):
    out = []
    for line in open(os.path.join(ROOT, "scenes", f"{part}.list")):
        if "|" in line:
            label, st, mv, t = line.strip().split("|")
            out.append((label, st, mv))
    return out


def find(words, phrase, pos):
    a = [canon(t) for t in norm_tokens(phrase)]
    toks = [w[0] for w in words]
    best = None
    for i in range(pos, len(toks)):
        win = toks[i:i + len(a) + 2]
        m = difflib.SequenceMatcher(None, a, win).get_matching_blocks()
        sc = sum(b.size for b in m); first = next((b.b for b in m if b.size), 0)
        if best is None or sc > best[0]:
            best = (sc, i + first)
        if sc == len(a):
            break
    return best


def main():
    W = json.load(open(os.path.join(ROOT, "vo", "words.json")))
    res = {}
    for part in ("intro", "ch1", "ch2", "ch3"):
        words, dur = W[part]["words"], W[part]["dur"]
        shots = shots_of(part); anchors = ANCHORS[part]
        assert len(shots) == len(anchors), (part, len(shots), len(anchors))
        starts, pos = [0.0], 0
        for k in range(1, len(shots)):
            sc, idx = find(words, anchors[k], pos)
            n = len(norm_tokens(anchors[k]))
            if sc < max(2, n - 1):
                print(f"  !! {part} {shots[k][0][:30]}: weak match {sc}/{n} for '{anchors[k]}'")
            starts.append(max(0.0, words[idx][1] - 0.15)); pos = idx + 1
        last_word = words[-1][2]
        end = max(dur, last_word + TAIL[part])
        L = LEAD[part]
        bounds = [0] + [round((L + s) * FPS) for s in starts[1:]] + [round((L + end) * FPS)]
        rows = []
        for k, (label, st, mv) in enumerate(shots):
            f = bounds[k + 1] - bounds[k]
            rows.append(dict(name=f"{part}_{k + 1:02d}_{st}_{mv}", set=st, move=mv, label=label, start=bounds[k] / FPS,
                             frames=f, seconds=round(f / FPS, 3), anchor=anchors[k]))
        res[part] = dict(shots=rows, vo_offset=L, vo_dur=dur, frames=bounds[-1])
        print(f"== {part}: {len(rows)} shots, {bounds[-1]} frames = {bounds[-1] / FPS:.1f} s (VO {dur:.1f} s at +{L} s)")
        for r in rows:
            print(f"   {r['start']:6.1f}  {r['seconds']:5.2f}s  {r['name']:34s} {r['label'][:46]}")
    json.dump(res, open(os.path.join(ROOT, "vo", "timing.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
