# The Iceman: a short film made entirely from code

This is a short cinematic test in the style of the "How an Ancient Mummy Changed History"
documentary. Every frame is made procedurally in Python. There are no stock assets, no
downloaded models or textures, and no hand-made art.

| # | Shot | What it does |
|---|------|--------------|
| 1 | `shot1_peaks.py` | A dawn aerial drift over eroded Alpine peaks, above a sea of volumetric clouds |
| 2 | `shot2_map.py` | A tilted relief map of the same terrain. It has contour lines, a border ridge, and a least-cost hiking route that draws itself to the place of discovery |
| 3 | `shot3_trail.py` | A ground-level storm shot. Footprints wind between fractured boulders toward the ridge |
| 4 | `shot4_axe.py` | A macro of the copper axe half-buried in snow: a yew haft, a leather and birch-tar binding, and an oxidised copper blade, lit by blue hour and firelight |
| 5 | `shot5_name.py` | The title: "ÖTZI" pressed into the glacier snow at night |

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

## Reproduce

```bash
python3 -m venv venv && venv/bin/pip install bpy==5.2.3 numba scipy pillow
cd scenes
../venv/bin/python shot1_peaks.py  --out ../frames/shot1_peaks --frames 72 --samples 32
../venv/bin/python shot4_axe.py    --out ../frames/shot4_axe   --frames 60 --samples 28
../venv/bin/python shot2_map.py    --out ../frames/shot2_map   --frames 72 --samples 16
../venv/bin/python shot5_name.py   --out ../frames/shot5_name  --frames 60 --samples 24
../venv/bin/python shot3_trail.py  --out ../frames/shot3_trail --frames 60 --samples 24
cd .. && venv/bin/python post.py frames work out/iceman_short.mp4
```

Add `--lowres --samples 16 --frames 1` to any scene to get a quick preview still. On a
4-core CPU a full render takes about 3–4 hours, and most of that time goes to the cloud
volumes in shot 1.
