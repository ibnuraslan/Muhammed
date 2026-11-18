# Mary Celeste — Part 5 (the boat and the ending)

Script section (mary_celeste/SCRIPT.txt on `claude/mary-celeste`, unchanged): "A boat could also have been lowered
as a temporary precaution." → "The boat and the ten people who may have been in it were never found."

* `shots.py` — the 28-shot list (exact VO per shot, picture, camera, SFX, cards).
* `scenes/` — `sc5_sea.py` (S01–S08, S27–S28), `sc5_cabin.py` (S09, S10, S12–S14), `sc5_cabin_reuse.py` (S11: the
  shared `mary_celeste_3d/scenes/sc_b_cabin.py` run unchanged with a new camera), `sc5_parlour.py` (S15–S23, S26),
  `sc5_ports.py` (S24, S25). `p5.py` puts the shared library on the path.
* `lib5/` — new assets (not forks): `yawl.py` (clinker ship's boat), `boatsea.py` (boat rides the FFT sea; sea pushed
  down inside the hull), `people.py` (cast as subclasses of the shared `deveau.Deveau`), `sitpose.py` (seated poses,
  pelvis on a real seat), `boatcrew.py` (ten people in the yawl), `props5.py` (bands, island, slate, stove, parcels,
  seal, reed organ, dolls, mugs, steam, water on floors).
* `tools/sb.sh` storyboard stills, `tools/board.py` review sheet (captions + cards via shared `callout.py`).

Needs `mary_celeste_3d/assets/makehuman` compiled (see that README) and Blender 5.2.
