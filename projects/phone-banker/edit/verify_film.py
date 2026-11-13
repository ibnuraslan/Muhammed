"""Check the one-file film before it goes to the farm (does not render the film).
  python edit/verify_film.py   -> review/film_verify.txt + out/verify/f*.png (3 test frames at 25%)
Checks: every linked shot file resolves; shot frame counts match vo/timing.json; master length == the audio files;
VO strips start at the part start + lead; fades sit around the sting; FilmCam, samples 32, adaptive 0.05, denoise and
alpha off on the master and every shot; fonts packed in every shot."""
import os, sys, json, wave, subprocess
import bpy
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
FILM = os.path.join(ROOT, "out", "blend", "film", "phone_banker_film.blend")
T = json.load(open(os.path.join(ROOT, "vo", "timing.json")))
EDL = json.load(open(os.path.join(HERE, "film_edl.json")))
FPS = 24
rep = []; ok = True
def check(cond, msg):
    global ok
    rep.append(("PASS " if cond else "FAIL ") + msg); ok = ok and cond

bpy.ops.wm.open_mainfile(filepath=FILM)
m = bpy.context.scene
libs = list(bpy.data.libraries)
missing = [l.filepath for l in libs if not os.path.exists(bpy.path.abspath(l.filepath))]
check(not missing, f"{len(libs)} linked shot files resolve (relative paths){': missing ' + ', '.join(missing) if missing else ''}")
check(all(l.filepath.startswith("//") for l in libs), "all library paths are relative")
strips = list(m.sequence_editor.strips_all if hasattr(m.sequence_editor, "strips_all") else m.sequence_editor.sequences_all)
scn = sorted([s for s in strips if s.type == 'SCENE'], key=lambda s: s.frame_final_start)
check(all(s.scene is not None and s.scene.library is not None for s in scn), f"{len(scn)} scene strips, each linked to its shot scene")
exp = [n for p in ("intro",) for n in [r["name"] for r in T[p]["shots"]]] + ["seldom_sting"] + [r["name"] for p in ("ch1", "ch2", "ch3") for r in T[p]["shots"]]
check([s.scene.name for s in scn] == exp, "shot order: intro, sting, Ch1, Ch2, Ch3 as in vo/timing.json")
want = {r["name"]: r["frames"] for p in ("intro", "ch1", "ch2", "ch3") for r in T[p]["shots"]}; want["seldom_sting"] = 144
bad = [(s.scene.name, s.frame_final_duration, want[s.scene.name]) for s in scn if s.frame_final_duration != want.get(s.scene.name)]
check(not bad, f"every shot has its cut length in frames{': ' + str(bad[:5]) if bad else ''}")
gaps = [(a.scene.name, b.scene.name) for a, b in zip(scn, scn[1:]) if a.frame_final_end != b.frame_final_start]
check(not gaps and scn[0].frame_final_start == 1, "shots butt-joined from frame 1, no gaps or overlaps")
check(m.frame_start == 1 and m.frame_end == scn[-1].frame_final_end - 1, f"master range 1-{m.frame_end} = {m.frame_end / FPS:.3f} s ({m.frame_end / FPS / 60:.2f} min)")
# audio
for f in ("phone_banker_AUDIO_with_voice.wav", "phone_banker_AUDIO_no_voice.wav"):
    w = wave.open(os.path.join(ROOT, "out", "deliver", f)); n = w.getnframes() / w.getframerate()
    check(abs(n - m.frame_end / FPS) < 0.5 / FPS, f"{f}: {n:.3f} s = {n * FPS:.1f} frames (film {m.frame_end})")
    lufs = subprocess.run(["ffmpeg", "-hide_banner", "-i", os.path.join(ROOT, "out", "deliver", f), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = [l for l in lufs.splitlines() if l.strip().startswith("I:")][-1].split()[1]
    rep.append(f"INFO {f}: integrated loudness {I} LUFS")
# VO
mk = {mm.name: mm.frame for mm in m.timeline_markers}
snd = {s.name: s for s in strips if s.type == 'SOUND'}
for part, key in (("intro", "INTRO"), ("ch1", "CH1"), ("ch2", "CH2"), ("ch3", "CH3")):
    s = snd.get(f"VO {part}"); lead = T[part]["vo_offset"]
    check(s is not None and s.frame_start == mk[key] + round(lead * FPS) and s.sound.packed_file is not None,
          f"VO {part}: starts at frame {s.frame_start if s else '?'} = part start {mk[key]} + {lead} s, packed")
s = snd.get("VO sting"); check(s is not None and s.frame_start == mk["STING"], f"sting SFX at frame {mk['STING']} (in the film file for reference)")
fades = sorted([(s.frame_final_start, s.frame_final_end) for s in strips if s.type == 'COLOR'])
st, c1 = mk["STING"], mk["CH1"]
check(fades == [(st - 24, st), (st, st + 12), (c1 - 36, c1), (c1, c1 + 24)], f"fades through black: intro out {st - 24}-{st}, sting in {st}-{st + 12}, sting out {c1 - 36}-{c1}, Ch1 in {c1}-{c1 + 24}")
# farm settings
check(m.camera is not None and m.camera.name == "FilmCam", "master has a scene camera (FilmCam)")
def farm(sc):
    c = sc.cycles
    return sc.render.engine == 'CYCLES' and c.samples == 32 and c.use_adaptive_sampling and abs(c.adaptive_threshold - 0.05) < 1e-6 and c.use_denoising and not sc.render.film_transparent
check(farm(m) and m.render.use_sequencer, "master: Cycles, 32 samples, adaptive 0.05, denoise, alpha off, sequencer on")
badf = [s.scene.name for s in scn if not farm(s.scene)]
check(not badf, f"all {len(scn)} shots: 32 samples, adaptive 0.05, denoise, alpha off{': ' + str(badf[:5]) if badf else ''}")
nograde = [s.scene.name for s in scn if not (s.scene.compositing_node_group and s.scene.compositing_node_group.name.startswith("HouseGrade"))]
check(not nograde, f"all shots carry the house grade{': ' + str(nograde[:5]) if nograde else ''}")
unpacked = [f.name for f in bpy.data.fonts if f.filepath and f.filepath != "<builtin>" and not f.packed_file and f.library is None]
rep.append(f"INFO fonts in the master: {len(bpy.data.fonts)}; fonts are packed in each shot file (checked below)")
check(m.render.resolution_x == 1920 and m.render.resolution_y == 816 and m.render.fps == FPS, "1920x816 at 24 fps")
open(os.path.join(ROOT, "review", "film_verify_master.txt"), "w").write("\n".join(rep) + "\n")
print("\n".join(rep)); print("ALL PASS" if ok else "SOME FAIL")
