# Part 1 of 5 — "The Ship That Came Back Without Its Crew" (Mary Celeste)

Script section (from `mary_celeste/SCRIPT.txt`, branch `claude/mary-celeste`, verbatim): "Oliver Deveau steps onto a ship
that's still moving." … "He has no record of what happened in between." 387 words, 53 shots, ~2:40.

Style: Atrium (research/style_v2 on `claude/fern-analysis`), rich warm colour. 16:9 2560x1440, 24 fps, Cycles.

## Layout
| Path | What |
|---|---|
| `shots.py` | The shot table: VO words (verbatim, split across shots), duration, description, SFX, card; one builder per shot |
| `p1/env.py` | Paths to the shared library `mary_celeste_3d/lib` (used unchanged), render setup, warm grade |
| `p1/sets.py` | Sea + sky, the Mary Celeste as found (shared `ship.build` + found-state props), the Dei Gratia |
| `p1/interiors.py` | Captain's cabin (from the shared look frame b), mate's cabin with logbook + slate, galley |
| `p1/crew.py` | Deveau (shared), Morehouse and three Dei Gratia hands (subclass of the shared Deveau builder) |
| `p1/smallboat.py` | **New asset**: a 16 ft ship's boat (thwarts, oars) |
| `p1/explain.py` | X-ray hold cutaway, 3D map (Natural Earth land), hex markers, dashed route, filled orange ripple bands |
| `comp/callout.py` | Shared card/caption module (copied unchanged from `claude/killer-in-house`) |
| `tools/board.sh` | Render storyboard frames (one Blender process per shot) |
| `tools/storyboard.py` | Review package: frames with card + caption, contact sheets, STORYBOARD.md, sfx_cues.csv |
| `review/` | Storyboard for the hub |

## Run
    tools/board.sh                     # all storyboard frames -> out/board/ (PREVIEW=0.5, SPP=24)
    python3 tools/storyboard.py        # -> review/
Shared assets must be compiled first (see `mary_celeste_3d/README.md`: MakeHuman data, Poly Haven downloads on use).
