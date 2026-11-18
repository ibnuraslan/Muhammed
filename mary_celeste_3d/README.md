# The Ship That Came Back Without Its Crew — 3D look frames

Blender 5.2 Cycles scenes for the Mary Celeste film. The script (`mary_celeste/SCRIPT.txt`) is on branch
`claude/mary-celeste` and is not changed here.

| Frame | Scene | What it shows |
|---|---|---|
| (a) | `scenes/sc_a_sighting.py` | From the Dei Gratia's bow: the Mary Celeste on the open Atlantic, torn wet sails, foam and spray |
| (b) | `scenes/sc_b_cabin.py` | Deveau in the captain's cabin by lantern light: wet bedding, the impression on the berth |
| (c) | `scenes/sc_c_rail.py` | The section of rail laid flat on deck, the gap where the boat went, Deveau at the gap |

Library (`lib/`): `human.py`, `look.py`, `grade.py`, `ph.py`, `common.py` are reused from
`claude/killer-in-house` (`nvidia_doc/scenes/`). New here: `deveau.py` (character: clothes grown as shells off
the MakeHuman body, strand hair and beard), `poses.py`, `ship.py` (procedural brigantine), `sea.py` (FFT
ocean, foam, spray, Poly Haven sky).

## Assets (not in git)

* MakeHuman 1.x CC0 data compiled to `assets/makehuman/` with `tools/mh_compile.py`
  (source: MakeHuman 1.2.0 source tarball on SourceForge for the base mesh, rig and eyes; `targets.npz` from the
  `makehuman` 1.3.2 wheel on PyPI). MPFB's UV masks (lips, nails, ears) are read from the installed MPFB extension.
* Poly Haven (CC0) sky, textures and models download on first use into `assets/polyhaven/`.

## Render

    tools/render_all.sh                 # all three, 2560x1440 -> out/frames/
    PREVIEW=0.25 blender -b --python scenes/sc_c_rail.py   # quick look

## lib/ API notes (for the part chats)

* `ship.build(name, sails="found"|"full", rail_gap=(x0, x1, "P"|"S")|None, wind=(local vector), wet=0..1, detail=bool,
  hatches_off=bool, boat_chocks=bool)` → dict(root, coll, mats, spars, hull). Bow +X, waterline z=0; `ship.zdeck(x)`,
  `ship.half_breadth(s, t)`, `ship.L`, `ship.B`, `ship.RAIL_H`.
* `sea.ocean(..., hulls=(hull objs), cut=(cx, cy, rx, ry))` (cut removes sea inside the hull you stand in), `sea.far_sea`,
  `sea.sky(strength, rot_deg)` (default sky `kloppenheim_06_puresky`: blue noon sky; sun lamp az = 139° + rot), `sea.spray`,
  `sea.mist_puff`.
* `deveau.Deveau(wet=)`; pose with `poses.stand/head/hand_reach/grip/rest_hand/arm_down` (rig faces −Y, left = +X), then
  `d.finish(look_at=world_pt, place=Matrix, density=1.0)`. `finish` bakes the pose, adds convex sea boots, grows hair,
  aims the eyes, then places him.
* Colour: grade `cine={"sat": 1.2, ...}` in exteriors; `tools/house_finish.py` never drains colour (hub/user: rich Atrium colour).
