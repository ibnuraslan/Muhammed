"""(drain-diamond copy: this film's CHAPTERS; the voiceover is optional until it arrives)
Assemble a chapter into ONE file to render: every shot .blend is graded, then linked into a master scene whose
timeline plays the shots in order with the voiceover underneath.

  python scenes/make_master.py intro out/blend/intro vo/intro_vo.mp3
  -> out/blend/intro/intro.blend    (render this: Render > Render Animation, or blender -b intro.blend -a)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
import grade

CHAPTERS = {
    "intro": [("drain_walk", "Drain A  'In March 2011, French police search a house'"),
              ("drain_patch", "Drain B  'This time, they notice a patch of concrete'"),
              ("drain_drill", "Drain A  'They drill through it.'"),
              ("drain_container", "Drain B  'Inside is a ring set with a thirty-one-carat diamond.'"),
              ("boutique_facade", "Boutique A  'The stone came from Harry Winston'"),
              ("boutique_painters", "Boutique B  'The first time, they came dressed as painters.'")],
    "ch1": [("boutique_grille", "Avenue A  'On the morning of October sixth, 2007'"),
            ("boutique_corridor", "Corridor B  'They've used the service entrance.'"),
            ("boutique_floor", "Salon A  'The men threaten and tie up staff.'"),
            ("boutique_safe", "Safe B  'They force a manager to deactivate alarms'"),
            ("stairs_powder", "Stairs A  'On the service stairs, the robbers empty fire extinguishers.'"),
            ("stairs_settle", "Stairs B  'There are employees who can tell police what happened.'")],
    "ch2": [("boutique2_xmas", "Avenue A  'Fourteen months later'"), ("boutique2_door", "Door B  'A guard lets them in.'"),
            ("boutique2_wig", "Upstairs A  'Upstairs, the disguises come off.'"), ("boutique2_floor16", "Upstairs B  'Soon, sixteen people are on the floor.'"),
            ("boutique2_suitcase", "Suitcase A  'The robbers have brought a suitcase.'"), ("boutique2_panel", "Panel B  'concealed compartments'"),
            ("boutique2_grenade", "Grenade A  'they show the people on the floor a grenade'"), ("boutique2_getaway", "Avenue B  'A driver picks them up outside.'"),
            ("boutique2_after", "After A  'The insurer offers a million-dollar reward'"), ("boutique_chair", "Chair B  'Who knew the shop well enough'")],
    "ch3": [("unit_pin", "Unit A  'The case lands with the Paris police unit'"), ("unit_read", "Unit B  'Investigators are also looking at one of the guards'"),
            ("gym_bag", "Gym A  'A link between the two men runs through a gym.'"), ("gym_lockers", "Gym B  'Chiniah puts them in touch.'"),
            ("car_mic", "Car A  'Detectives put microphones in Yahiaoui's car.'"), ("car_envelope", "Car B  'envelopes change hands through car windows'"),
            ("raid_arrive", "Raid A  'In June 2009, police move in'"), ("raid_stairs", "Raid B  'a hidden compartment beneath a staircase'"),
            ("drain_yard", "House A  'It's Yahiaoui's house.'"), ("car_reels", "House B  'the big stone that keeps coming up on the recordings'"),
            ("drain_gate", "Drain A  'They keep coming back to the house.'"), ("drain_torch", "Drain B  'the lighter patch in the drain'"),
            ("drain_circle", "Tub A  'The container holds nineteen rings'"), ("drain_bag", "Tub B  'roughly twenty-five million dollars'"),
            ("table_layout", "Table A  'a haul they can lay out and count'"), ("table_tags", "Table B  'a guard who was supposed to protect the shop'")],
    "ch4": [("court_aisle", "Court A  'In February 2015, eight men go on trial'"), ("court_dock", "Court B  'Mouloud Djennad admits supplying information'"),
            ("boutique_night_door", "Night A  'he let the men in the evening before'"), ("boutique_night_wait", "Night B  'the men were already there'"),
            ("court_prosecutor", "Court A  'Prosecutor Sylvie Kachaner tells the court'"), ("court_file", "Court B  'traces of their DNA in the boutique'"),
            ("court_ashamed", "Dock A  'I'm ashamed every day'"), ("court_reverse", "Dock B  (reverse on the public benches)"),
            ("court_judges", "Judges A  'the court convicts all eight men'"), ("steps_steps", "Steps B  'three of them suspended'"),
            ("table_alone", "Table A  'Police can account for the thirty-one-carat diamond'"), ("table_empty", "Table B  'hundreds of the pieces ... are still missing'")],
}

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
chapter, folder, vo = args[:3]
LEAD = float(args[3]) if len(args) > 3 else (2.5 if chapter == "intro" else 0.0)   # seconds of picture before the first word
folder = os.path.abspath(folder)
shots = CHAPTERS[chapter]

# 1. grade every shot file in place (compositor tree stored in its scene)
for name, _ in shots:
    path = os.path.join(folder, name + ".blend")
    bpy.ops.wm.open_mainfile(filepath=path)
    sc = bpy.context.scene
    if sc.compositing_node_group is None or sc.compositing_node_group.name.startswith("HouseGrade") is False:
        grade.add_grade(sc)
    sc.name = name
    bpy.ops.wm.save_mainfile(filepath=path, compress=True)
    print("[master] graded", name, sc.frame_end, "frames", flush=True)

# 2. the master file: link each shot's scene, lay them end to end on the timeline, voiceover underneath
bpy.ops.wm.read_factory_settings(use_empty=True)
master = bpy.context.scene; master.name = chapter.upper()
master.render.resolution_x, master.render.resolution_y, master.render.resolution_percentage = 1920, 816, 100
master.render.fps = 24
se = master.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
frame = 1
for k, (name, label) in enumerate(shots):
    path = os.path.join(folder, name + ".blend")
    with bpy.data.libraries.load(path, link=True, relative=True) as (src, dst):
        dst.scenes = [n for n in src.scenes if n == name] or src.scenes[:1]
    sc = dst.scenes[0]
    st = strips.new_scene(name=label[:60], scene=sc, channel=1, frame_start=frame)
    st.scene_input = 'CAMERA' if hasattr(st, "scene_input") else None
    n = sc.frame_end - sc.frame_start + 1
    print(f"[master] {name:20s} frames {frame}-{frame + n - 1}", flush=True)
    m = master.timeline_markers.new(label.split("  ")[0], frame=frame)
    frame += n
master.frame_start, master.frame_end = 1, frame - 1
# voiceover (packed into the master); until it arrives the timeline uses the estimated shot lengths
vo_path = os.path.abspath(vo)
if os.path.exists(vo_path):
    snd = strips.new_sound("Voiceover", vo_path, channel=2, frame_start=1 + int(round(LEAD * 24)))
    try:
        snd.sound.pack()
    except Exception as e:
        print("[master] could not pack sound:", e)
else:
    print("[master] no voiceover yet:", vo_path, flush=True)
master.render.use_sequencer = True
master.render.use_compositing = False          # each shot scene applies its own grade
master.render.filepath = f"//render/{chapter}_"
master.render.image_settings.file_format = 'PNG'
out = os.path.join(folder, chapter + ".blend")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=True)
print("[master] saved", out, "frames", master.frame_end, flush=True)
