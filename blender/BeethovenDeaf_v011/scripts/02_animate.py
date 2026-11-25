"""BeethovenDeaf v011 stage B: staging, acting, hands on the keys, the rod in the teeth, rings, x-ray, camera.
blender -b stageA.blend --python 02_animate.py -- <VO.mp3> <out.blend> [--blocking]
Part files (exec'd in order): 02a_pose.py (seat, legs, spine/head acting, jaw, eyes), 02b_hands.py (piano hands: keys + fingers
solved so every pad sits exactly on its key top), 02c_rod.py (rod in the teeth through the clamp, rings),
02d_xray.py (x-ray window, skull, ear anatomy, vibration path), 02e_camera.py (the one continuous camera)."""
import bpy, sys, os, math, json, random
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.join(HERE, "..", "..", "pipeline")
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
exec(open(os.path.join(PIPE, "hand_poses.py")).read())
args = sys.argv[sys.argv.index("--") + 1:]
VO, OUT, SRC = args[0], args[1], args[2]
BLOCKING = "--blocking" in args
O = bpy.data.objects
COMP = O["Composer"]; CB = O["Composer.body"]
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print("LOG", s); LOG.append(s)
def F(sec): return 1 + int(round(sec * 60))
WORDS = json.load(open(os.path.join(HERE, "vo_words.json")))
def wf(word, n=1):
    k = 0
    for s, e, w in WORDS:
        if w.lower().strip(".,").startswith(word.lower()):
            k += 1
            if k == n: return F(s)
    raise KeyError(word)
END = sc.frame_end
T = dict(bite=wf("bite"), rod=wf("rod"), attached=wf("attached"), piano=wf("piano"), playing=wf("playing"),
         vib=wf("vibrations"), through=wf("through"), into=wf("into"), jaw=wf("jawbone"), reached=wf("reached"), inner=wf("inner"),
         sent=wf("sent"), sound=wf("sound"), skull=wf("skull"), bypass=wf("bypassing"), eardrum=wf("eardrum"),
         allowing=wf("allowing"), hear=wf("hear"), using=wf("using"), beethoven=wf("beethoven"), composing=wf("composing"),
         even=wf("even"), deaf=wf("deaf"))
T["pianos"] = wf("piano", 2)
log("beats", T)
for part in ("02a_pose.py", "02b_hands.py", "02c_rod.py", "02d_xray.py", "02e_camera.py"):
    p = os.path.join(HERE, part)
    if os.path.exists(p):
        log("exec", part); exec(open(p).read())
# VO strip
if not sc.sequence_editor: sc.sequence_editor_create()
for s_ in list(sc.sequence_editor.strips_all if hasattr(sc.sequence_editor, "strips_all") else sc.sequence_editor.sequences_all):
    pass
try:
    snd = sc.sequence_editor.strips.new_sound("VO", VO, 1, 1)
except AttributeError:
    snd = sc.sequence_editor.sequences.new_sound("VO", VO, 1, 1)
sc.frame_set(1)
json.dump(LOG, open(OUT + ".log.json", "w"), indent=0)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_OK", OUT)
