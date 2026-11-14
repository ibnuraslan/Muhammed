"""The 14 rebuilt Ch4-5 shots (hub's final list). Each replaces the shot of the same id in the delivered master
nvidia_ch45.blend and keeps EXACTLY its frame count and master in/out frames (from vo/ch45_timing.json).
A shot is either one (set, move) or, for the split screen, several scenes composed in the patch's master scene."""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))

# id -> (label, list of scene parts). A part: (set, move, role); role 'full' | 'left' | 'right' | 'title'
REDO = [
    ("c4_01", "1A Split screen: the man on the phone / a reporter calling + CHAPTER 4 title",
     [("split", "office", "left"), ("split", "newsroom", "right"), ("split", "title", "title")]),
    ("c4_03", "2B A richer lobby: glass, light and life", [("lobby2", "lobby", "full")]),
    ("c4_08", "4B Code-of-conduct binder, a highlighter draws over a clause", [("paper2", "binder", "full")]),
    ("c4_09", "4C A printer feeds out the filing", [("paper2", "printer", "full")]),
    ("c4_12", "5C He walks out through the lobby's glass doors at night", [("exit", "walkout", "full")]),
    ("c4_14", "6B Boardroom: collected papers, folder, CHAIR nameplate, turned chair", [("board2", "folder", "full")]),
    ("c4_18", "7D Wall calendar: 8-11 crossed out, the 12th circled, a phone lights up", [("calendar", "calendar", "full")]),
    ("c5_01", "1A Interview room (moody) + CHAPTER 5 title", [("interview2", "passport_slide", "full")]),
    ("c5_04", "2A The passport slides away across the table", [("interview2", "question", "full")]),
    ("c5_07", "4B The empty chair under the lamp, the two-way mirror", [("interview2", "warning", "full")]),
    ("c5_09", "5A The passport slid back", [("interview2", "passport_back", "full")]),
    ("c5_11", "6A Container stacks at dusk, light masts, a gantry crane", [("port2", "stacks", "full")]),
    ("c5_14", "7A Data hall (Ch1 quality): half the racks still empty", [("aihall", "half_empty", "full")]),
    ("c5_20", "9A A realistic port X-ray gate, a truck pulls a container through", [("port2", "xray", "full")]),
]


def table():
    """id -> dict(old_name, frames, master_in, master_out, label, parts)."""
    tim = json.load(open(os.path.join(HERE, "..", "vo", "ch45_timing.json")))
    pos, f = {}, 1
    for c in ("4", "5"):
        for sh in tim[c]:
            pos[sh["name"][:5]] = (sh["name"], sh["frames"], f, f + sh["frames"] - 1); f += sh["frames"]
    out = []
    for sid, label, parts in REDO:
        old, n, a, b = pos[sid]
        out.append(dict(id=sid, old_name=old, frames=n, master_in=a, master_out=b, label=label, parts=parts))
    return out


if __name__ == "__main__":
    tot = 0
    for r in table():
        print(f"{r['id']}  {r['frames']:4d} f  master {r['master_in']:5d}-{r['master_out']:5d}  {r['label']}")
        tot += r["frames"]
    print("total", tot, "frames")
