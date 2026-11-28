"""Romand Part 1: animated shots. Builds each storyboard shot (sb_p1), animates the camera move and the action from
the shot list, runs the per-frame clip check on EVERY frame, saves shots/<ID>.blend and renders the frames.
    SHOT=P1-01 OUT=<dir> RES=640x360 SPP=6 blender -b --python anim_p1.py        (preview)
    SHOT=P1-01 OUT=<dir> RES=1920x1080 SPP=16 blender -b --python anim_p1.py     (native final)
    NORENDER=1 to build + check + save only."""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Matrix
import rk, rprops as PR, ranim as A
import sb_p1 as SB
E = os.environ.get
HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = {r["id"]: r for r in json.load(open(os.path.join(HERE, "..", "shots", "shots.json")))["1"]["rows"]}
FPS = 24


def fig(name):
    pv = bpy.data.objects[name]
    return dict(pivot=pv, arm=[o for o in pv.children_recursive if o.type == 'ARMATURE'][0])


def car():
    return bpy.data.objects["car_root"]


def fwd_of(o):
    return (o.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()


# per-shot animation: fn(N) with N = frame count (frames 1..N)
def a01(N):
    c = car(); p1 = c.location.copy(); p0 = p1 - fwd_of(c) * 4.0
    A.key_path(c, 1, int(N * 0.75), p0, p1, "out"); A.cam_move("push", 1, N, 0.82)
def a02(N): A.cam_move("crane_up", 1, N, 8)
def a03(N): A.cam_move("orbit", 1, N, 14)
def a04(N):
    h = bpy.data.objects["car_boot_hinge"]; A.key_value(h, "rotation_euler", 1, 6, 20, 0.0, math.radians(80 * 0.1), "out")
    A.cam_move("push", 1, N, 0.9)
def a05(N): A.cam_move("track", 1, N, 2.4)
def a06(N): A.cam_move("track", 1, N, 1.4)
def a07(N): A.cam_move("whip", 1, N, 30)
def a08(N): A.cam_move("push", 1, N, 0.9)
def a09(N): A.cam_move("push", 1, N, 0.93)
def a10(N): A.cam_move("pull", 1, N, 1.35, easing="in")
def a11(N): A.cam_move("push", 1, N, 0.88)
def a12(N): A.cam_move("creep", 1, N, 0.9)
def a13(N): A.cam_move("orbit", 1, N, -12)
def a14(N): A.cam_move("track", 1, N, 0.4)
def a15(N):
    n = bpy.data.objects["notes"]; p1 = n.location.copy(); p0 = p1 - Vector((0.75, 0, 0))
    A.key_path(n, 1, int(N * 0.8), p0, p1, "out"); A.cam_move("push", 1, N, 0.92)
def a16(N): A.cam_move("push", 1, N, 0.85)
def a17(N):
    c = car(); p0 = c.location.copy(); A.key_path(c, 1, N, p0, p0 + fwd_of(c) * 7.0, "in"); A.cam_move("track", 1, N, 2.0)
def a18(N):
    c = car(); p1 = c.location.copy(); A.key_path(c, 1, int(N * 0.8), p1 - fwd_of(c) * 6.0, p1, "out")
    A.cam_move("crane_down", 1, N, 10)
def a19(N):
    f = fig("chantal"); f["pivot"].location = Vector((1.2, 1.25, 0.12))
    A.walk(f, 1, min(N, 38), 180, period=28, stride=15)          # from the kerb to the lit door, then she stops
    A.cam_move("track", 1, N, -1.2)
def a20(N): A.cam_move("push", 1, N, 0.75, easing="in")
def a21(N): A.cam_move("track", 1, N, 0.35)
def a22(N): A.cam_move("push", 1, N, 0.85)
def a23(N): A.cam_move("push", 1, N, 0.97)
def a26(N): A.cam_move("orbit", 1, N, 18)
def a28(N):
    f = fig("romand"); A.walk(f, 1, N, -90, period=30, stride=16, carry=False); A.cam_move("crane_down", 1, N, 6)
def a29(N): A.cam_move("track", 1, N, 0.22)
def a30(N):
    coins = [o for o in bpy.data.objects if o.name.startswith("coin")]
    for o in coins:                      # coins advance toward the house, looping along their trail
        p = o.location.copy(); d = -p.normalized() * 0.32
        A.key_path(o, 1, N, p, p + d, "lin")
    A.cam_move("orbit", 1, N, 16)
def a31(N): A.cam_move("push", 1, N, 0.9)
def a33(N):
    for i in range(6):
        f = fig(f"st{i}"); A.walk(f, 1, N, math.degrees(f["pivot"].rotation_euler.z), period=30 + i, stride=13, phase0=i * 0.17)
    A.cam_move("crane_down", 1, N, 10)


ANIM = {k: globals()["a" + k[3:]] for k in SB.SHOTS3D}


def find_exposure(lo=11.0, hi=15.0, target=13.0, tries=4):
    sc = bpy.context.scene; pct, spp = sc.render.resolution_percentage, sc.cycles.samples
    sc.render.resolution_percentage = 25; sc.cycles.samples = 4
    p = os.path.join(E("OUT"), "_probe.png")
    for _ in range(tries):
        rk.render(p); L = rk.luma(p)
        if lo <= L <= hi:
            break
        sc.view_settings.exposure += max(-3, min(3, math.log2(target / max(L, 0.15)) * 1.1))
    sc.render.resolution_percentage, sc.cycles.samples = pct, spp
    return sc.view_settings.exposure


def run(sid):
    W, H = map(int, E("RES", "640x360").split("x")); spp = int(E("SPP", "6"))
    sc = rk.setup(res=(W, H), spp=spp)
    SB.SHOTS3D[sid]()
    N = max(12, round(SHOTS[sid]["dur"] * FPS))
    sc.frame_start, sc.frame_end = 1, N
    sc.frame_set(1)
    if sid in SB.EXPLAINERS:
        rk.grade(expo=-1.2, vig=0.5)
    else:
        rk.grade(expo=-2.6)
    out = E("OUT"); os.makedirs(out, exist_ok=True)
    exps = os.path.join(out, "exposure.json"); EX = json.load(open(exps)) if os.path.exists(exps) else {}
    if sid not in SB.EXPLAINERS:
        if sid in EX:
            sc.view_settings.exposure = EX[sid]
        else:
            EX[sid] = find_exposure(); json.dump(EX, open(exps, "w"), indent=1)
    ANIM[sid](N)
    sc.frame_set(1)
    bad = A.clip_check(sid, 1, N, os.path.join(out, "clip"))
    os.makedirs(os.path.join(out, "shots"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "shots", sid + ".blend"), compress=True)
    if E("NORENDER"):
        return
    sc.render.filepath = os.path.join(out, "frames", sid, "f_####.png")
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
    sc.render.use_persistent_data = True        # keep static geometry (the instanced forests) between frames
    bpy.ops.render.render(animation=True)
    print("RENDERED", sid, N, "frames", "clipping" if bad else "clean")


if __name__ == "__main__":
    for s in E("SHOT", "P1-01").split(","):
        run(s)
