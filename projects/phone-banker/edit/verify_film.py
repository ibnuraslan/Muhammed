"""Check the one-file film before it goes to the farm (does not render the film).
  python edit/verify_film.py master <copy.blend>   (a copy outside out/blend/film, so its shot links don't load)
  python edit/verify_film.py shots                 (opens every shot file, one at a time)
  python edit/verify_film.py frames f1 f2 f3       (renders those master frames at 25% through the real links)
Results append to review/film_verify.txt."""
import os, sys, json, glob, shutil
import bpy
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
BL = os.path.join(ROOT, "out", "blend"); FILM = os.path.join(BL, "film", "phone_banker_film.blend")
T = json.load(open(os.path.join(ROOT, "vo", "timing.json")))
FPS = 24
FRAMES = {r["name"]: r["frames"] for p in ("intro", "ch1", "ch2", "ch3") for r in T[p]["shots"]}; FRAMES["seldom_sting"] = 144
ORDER = [r["name"] for r in T["intro"]["shots"]] + ["seldom_sting"] + [r["name"] for p in ("ch1", "ch2", "ch3") for r in T[p]["shots"]]
rep = []; ok = [True]
def check(cond, msg):
    rep.append(("PASS " if cond else "FAIL ") + msg); ok[0] = ok[0] and bool(cond)
def farm(sc):
    c = sc.cycles
    return sc.render.engine == 'CYCLES' and c.samples == 32 and c.use_adaptive_sampling and abs(c.adaptive_threshold - 0.05) < 1e-6 \
        and c.use_denoising and not sc.render.film_transparent
def all_strips(m):
    se = m.sequence_editor
    return list(se.strips_all if hasattr(se, "strips_all") else se.sequences_all)

mode = sys.argv[1]
if mode == "master":
    bpy.ops.wm.open_mainfile(filepath=sys.argv[2])
    m = bpy.context.scene
    libs = {l.name: l.filepath for l in bpy.data.libraries}
    real = {n: os.path.normpath(os.path.join(os.path.dirname(FILM), p[2:])) for n, p in libs.items()}
    missing = [p for p in real.values() if not os.path.exists(p)]
    check(len(libs) == 71 and all(p.startswith("//") for p in libs.values()), f"{len(libs)} linked shot files, all relative paths")
    check(not missing, f"every link resolves next to the master (out/blend/<part>/<shot>.blend){': missing ' + str(missing[:3]) if missing else ''}")
    check(not any("_placeholders" in p for p in libs.values()), "no link points at a placeholder")
    st = all_strips(m)
    scn = sorted([s for s in st if s.type == 'SCENE'], key=lambda s: s.frame_final_start)
    names = [s.scene.name for s in scn]
    check(names == ORDER, f"{len(scn)} shot strips in order: intro, sting, Ch1, Ch2, Ch3")
    bad = [(s.scene.name, s.frame_final_duration) for s in scn if s.frame_final_duration != FRAMES[s.scene.name]]
    check(not bad, f"every strip has its cut length (frames from vo/timing.json){': ' + str(bad[:4]) if bad else ''}")
    gaps = [(a.scene.name, b.scene.name) for a, b in zip(scn, scn[1:]) if a.frame_final_end != b.frame_final_start]
    check(not gaps and scn[0].frame_final_start == 1, "strips butt-joined from frame 1: no gaps, no overlaps")
    check(m.frame_start == 1 and m.frame_end == scn[-1].frame_final_end - 1 == sum(FRAMES.values()),
          f"master frames 1-{m.frame_end} = {m.frame_end / FPS:.3f} s ({m.frame_end / FPS / 60:.2f} min)")
    mk = {x.name: x.frame for x in m.timeline_markers}
    snd = {s.name: s for s in st if s.type == 'SOUND'}
    for part, key in (("intro", "INTRO"), ("ch1", "CH1"), ("ch2", "CH2"), ("ch3", "CH3")):
        s = snd.get(f"VO {part}"); lead = T[part]["vo_offset"]
        check(s is not None and s.frame_start == mk[key] + round(lead * FPS) and s.sound.packed_file is not None,
              f"VO {part}: frame {s.frame_start} = part start {mk[key]} + {lead} s ({round(lead * FPS)} frames), sound packed")
    s = snd.get("VO sting"); check(s is not None and s.frame_start == mk["STING"] and s.sound.packed_file is not None, f"sting SFX at the sting start (frame {mk['STING']}), packed")
    fades = sorted([(s.frame_final_start, s.frame_final_end) for s in st if s.type == 'COLOR'])
    a, c1 = mk["STING"], mk["CH1"]
    check(fades == [(a - 24, a), (a, a + 12), (c1 - 36, c1), (c1, c1 + 24)],
          f"fades through black: intro out {a - 24}-{a}, sting in {a}-{a + 12}, sting out {c1 - 36}-{c1}, Ch1 in {c1}-{c1 + 24}")
    vi = snd["VO intro"]; fc = m.animation_data.action if m.animation_data else None
    check(m.camera is not None and m.camera.name == "FilmCam", "master has a scene camera: FilmCam")
    check(farm(m) and m.render.use_sequencer and not m.render.use_compositing, "master: Cycles, 32 samples, adaptive 0.05, denoise, alpha off, sequencer on")
    check((m.render.resolution_x, m.render.resolution_y, m.render.resolution_percentage, m.render.fps) == (1920, 816, 100, 24), "1920x816 at 100%, 24 fps")
    import wave, subprocess
    for f in ("phone_banker_AUDIO_with_voice.wav", "phone_banker_AUDIO_no_voice.wav"):
        p = os.path.join(ROOT, "out", "deliver", f); w = wave.open(p); n = w.getnframes() / w.getframerate()
        check(abs(n - m.frame_end / FPS) < 0.5 / FPS, f"{f}: {n:.3f} s = {n * FPS:.2f} frames = film length")
        st_ = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
        I = [l for l in st_.splitlines() if l.strip().startswith("I:")][-1].split()[1]
        P = [l for l in st_.splitlines() if l.strip().startswith("Peak:")][-1].split()[1]
        rep.append(f"INFO {f}: {I} LUFS integrated, true peak {P} dBFS")
elif mode == "shots":
    files = {n: os.path.join(BL, p, n + ".blend") for p in ("intro", "ch1", "ch2", "ch3") for n in [r["name"] for r in T[p]["shots"]]}
    files["seldom_sting"] = os.path.join(BL, "sting", "seldom_sting.blend")
    probs = []
    for n, f in files.items():
        bpy.ops.wm.open_mainfile(filepath=f)
        sc = bpy.data.scenes.get(n)
        why = []
        if sc is None: why.append("scene name")
        else:
            if (sc.frame_start, sc.frame_end) != (1, FRAMES[n]): why.append(f"frames {sc.frame_start}-{sc.frame_end}")
            if not farm(sc): why.append("render settings")
            if not (sc.compositing_node_group and sc.compositing_node_group.name.startswith("HouseGrade")): why.append("grade")
            if sc.camera is None: why.append("camera")
        if [x for x in bpy.data.fonts if x.filepath and x.filepath != "<builtin>" and not x.packed_file]: why.append("font not packed")
        for im in bpy.data.images:
            if im.source == 'SEQUENCE' and not os.path.exists(bpy.path.abspath(im.filepath)): why.append("UI sequence missing")
            if im.source == 'FILE' and im.filepath and not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath)): why.append(f"image {im.name}")
        if why: probs.append((n, why))
    check(not probs, f"all {len(files)} shot files: scene named after the shot, frame range = cut length, 32 samples, adaptive 0.05, denoise, alpha off, house grade, camera, fonts packed, images packed/found{': ' + str(probs[:5]) if probs else ''}")
elif mode == "frames":
    frames = [int(x) for x in sys.argv[2:]]
    bpy.ops.wm.open_mainfile(filepath=FILM)                   # never saved back
    print("unreachable"); sys.exit(1)
open(os.path.join(ROOT, "review", "film_verify.txt"), "a").write("\n".join(rep) + "\n")
print("\n".join(rep)); print("ALL PASS" if ok[0] else "SOME FAIL")
