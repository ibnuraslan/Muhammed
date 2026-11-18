# Mary Celeste — Part 2 ("Less than a month earlier…" → "…a ship he believes he can save.")

Blender 5.2 Cycles, 2560x1440, 24 fps. Script text: `mary_celeste/SCRIPT.txt` on `claude/mary-celeste` (unchanged).

* `shared3d/` (git-ignored) = `mary_celeste_3d/` from `claude/mary-celeste-3d`, unpacked unchanged:
  `git archive origin/claude/mary-celeste-3d mary_celeste_3d | tar -x && mv mary_celeste_3d mary_celeste_p2/shared3d`,
  then compile MakeHuman data with its `tools/mh_compile.py` (see its README).
* `p2lib/` — this part only: `cast.py` (Briggs, Sarah, Sophia, Arthur, visitor, sailors, live-rig Deveau: subclasses of the
  shared `deveau.Deveau`), `cabin.py`, `pier.py`, `seaset.py`, `rooms.py` sets, `acts.py` poses, `stage.py` render/camera helpers.
* `scenes/sc_*.py SHOT=nn` render one shot; `tools_run.sh scene shots…`; `tools/board.py` builds `review/`.
* `shots.py` = shot list (VO word for word, shot, action, SFX, cards). `STORYBOARD.md` generated.
