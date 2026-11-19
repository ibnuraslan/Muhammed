"""Give every Part 3 shot its own span of the script (shared sentences split at natural breaks) and check that the
spans, joined, are exactly the script section (SCRIPT.txt lines 23-30 on claude/mary-celeste)."""
import re, ast, subprocess, json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VO = json.load(open(os.path.join(HERE, "vo", "shot_vo.json")))
script = subprocess.run(["git", "show", "origin/claude/mary-celeste:mary_celeste/SCRIPT.txt"], capture_output=True, text=True, cwd=HERE).stdout.splitlines()
sec = " ".join(script[22:30])
assert " ".join(VO.values()) == sec, "spans do not join to the script"
p = os.path.join(HERE, "shots.py"); s = open(p).read()
for sid, vo in VO.items():
    m = re.search(r'@shot\("%s", ("(?:[^"\\]|\\.)*")' % re.escape(sid), s); assert m, sid
    s = s[:m.start(1)] + json.dumps(vo) + s[m.end(1):]
ast.parse(s); open(p, "w").write(s); print("VO spans set:", len(VO))
