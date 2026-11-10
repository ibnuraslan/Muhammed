# The Iceman: a short film made entirely from code

This is a 45-second cinematic test in the style of the "How an Ancient Mummy Changed History"
documentary. Every frame is made procedurally in Python. There are no stock assets, no
downloaded models or textures, and no hand-made art.

| # | Shot | What it does |
|---|------|--------------|
| 1 | `shot1_peaks.py` | A dawn aerial drift over eroded Alpine peaks, above a sea of volumetric clouds |
| 2 | `shot2_map.py` | A tilted relief map of the same terrain. It has contour lines, a border ridge, and a least-cost hiking route that draws itself to the place of discovery |
| 3 | `shot3_trail.py` | A ground-level storm shot. Footprints wind between fractured boulders toward the ridge |
| 4 | `shot4_axe.py` | A macro of the copper axe half-buried in snow: a yew haft, a leather and birch-tar binding, and an oxidised copper blade, lit by blue hour and firelight |
| 5 | `shot5_name.py` | The title: "ÖTZI" pressed into the glacier snow at night |
| 6 | `shot6_lab.py` | The mummy on a perforated steel table in a cold lab |
| 7 | `shot7_discovery.py` | 19 September 1991: the body lies face-down in glacier ice and meltwater, with the two hikers who found it standing behind |
| 8 | `shot8_fire.py` | Ötzi alive, sitting by a fire at night: the camera starts on the flames and rises to his face as the focus shifts from the fire to him |
| 9 | `shot9_walk.py` | Ötzi walks away into the blizzard with his bow staff |

The final edit runs in this order: 1, 2, 7, 6, 3, 9, 8, 4, 5.

## How it works

* **Terrain** (`scenes/terrain.py`). The base is rotated-octave Perlin ridged multifractal
  noise with domain warping. A numba droplet-erosion simulation then carves gullies and
  ridges into it.
* **Rendering** (`scenes/*.py`) uses Blender 5.2 as a Python module (`bpy`) with the
  Cycles path tracer on the CPU. It uses physically based materials:
  * snow with subsurface scattering and ice-crystal glints made from clear-coat facets
  * metallic copper with oxide patina
  * aerial perspective, Nishita-style sky and volumetric clouds
* **Post** (`post.py`):
  * per-shot colour grading
  * motion-compensated interpolation from 12 to 24 fps (ffmpeg `minterpolate`)
  * 3D-projected falling snow with depth of field and motion blur
  * bloom and halation, chromatic aberration, vignette and film grain
  * documentary typography, with map labels tracked to points projected from the 3D scene
  * dissolves between shots
* **Sound** (`sound.py`) is synthesised: gusting alpine wind, a low drone, a glass pad,
  a riser and a sub-boom on the title cut, with convolution reverb.

## Humans

The people are built on the base mesh, morph targets and skeleton from MakeHuman 1.2. These
assets are released as CC0, so they are free to use. The code generates everything else:

* **`scenes/human.py`**
  * Blends body-shape targets for age, gender, muscle, weight and height.
  * Fits the skeleton and skin weights to the new shape.
  * Fits brows and lashes, and adds procedural eyeballs.
  * Fits clothing proxies and hides the skin underneath them.
  * Has posing helpers for sitting, walking, the mummy's frozen pose and lying on a surface.
* **`scenes/mummy.py`** makes the mummy:
  * about 30 targets for wasting and a shrunken face
  * a geometry pass that tightens skin over bone and sinks it between the ribs
  * a leathery shader where stretched skin over bone goes pale and the creases go dark, with
    wrinkles and cracks
* **`scenes/otzi.py`** makes the living Ötzi:
  * shoulder-length hair, a beard, a fur cap and a fur cape, all grown as Blender hair-curve
    strands with gravity, clumping and collisions
  * a striped goat-hide coat, leggings and shoes cut from the body mesh, so they deform with
    the rig

Get the assets once. They come from the official MakeHuman 1.2.0 release. Use `7z` to extract
the data from the Windows installer; it is never run.

```bash
curl -O https://download.tuxfamily.org/makehuman/releases/makehuman-community-1.2.0-windows.zip
unzip makehuman-community-1.2.0-windows.zip makehuman-community-1.2.0-windows.exe
7z x -omh makehuman-community-1.2.0-windows.exe -x'!*.exe' -x'!*.dll' -x'!*.pyd'
export MH_DATA=$PWD/mh/makehuman/data
```

## Reproduce

```bash
python3 -m venv venv && venv/bin/pip install bpy==5.2.3 numba scipy pillow   # plus MH_DATA, see above
cd scenes
../venv/bin/python shot1_peaks.py  --out ../frames/shot1_peaks --frames 72 --samples 32
../venv/bin/python shot4_axe.py    --out ../frames/shot4_axe   --frames 60 --samples 28
../venv/bin/python shot2_map.py    --out ../frames/shot2_map   --frames 72 --samples 16
../venv/bin/python shot5_name.py   --out ../frames/shot5_name  --frames 60 --samples 24
../venv/bin/python shot3_trail.py  --out ../frames/shot3_trail --frames 60 --samples 24
../venv/bin/python shot6_lab.py    --out ../frames/shot6_lab   --frames 60 --samples 40
../venv/bin/python shot7_discovery.py --out ../frames/shot7_discovery --frames 48 --samples 28
../venv/bin/python shot8_fire.py   --out ../frames/shot8_fire  --frames 60 --samples 24
../venv/bin/python shot9_walk.py   --out ../frames/shot9_walk  --frames 60 --samples 24
cd .. && venv/bin/python post.py frames work out/iceman_short.mp4
```

Add `--lowres --samples 16 --frames 1` to any scene to get a quick preview still. On a
4-core CPU a full render takes about 7 hours. Most of that time goes to the cloud volumes in
shot 1 and to the hair and the fire volume in the human shots.
