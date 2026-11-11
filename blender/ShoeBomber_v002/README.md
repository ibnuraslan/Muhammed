# ShoeBomber_v002: farm package

This is the full 27.0 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

## Files
- `ShoeBomber_v002_60fps.blend`: the self-contained scene. Every texture is packed. Git LFS.
- `beats.json`: the start frame and first words of each beat, for the voiceover retime (`pipeline/retime_to_vo.py`).
- `SETTINGS.md`: render settings, measured cost and test frames. `CREDITS.md` has the CC-BY block for the video description.
- `review/`: the final 0.2 s contact sheets, made from this packed file at 270×480 and 8 samples.
- `package_check_f965_lowres.png`: a 25 %, 4-sample frame from the packed file opened in factory Blender. It shows the package works; it is not a quality reference.

## Source and build
The scripts are in `../ShoeBomber_v001/scripts/`. Build order:
1. `01_build_humans.py`: MPFB humans
2. `02_build_scene.py`: the cabin, studio, sky and airport sets
3. `03_animate.py`: characters and props, with an automatic reach pass
4. `04_fx_camera.py`: attachments, fx, lights, grade, the camera and `beats.json`
5. `05_shrink_textures.py`
6. `pipeline/package_for_farm.py`

`audit.py` is the contact audit.

## Beats (target times; no VO yet)
| # | Frame | Line | Picture |
|---|---|---|---|
| 1 | 1 | In the middle of a flight… | A night cabin. The bomber hunches over his sneaker and lights a match at the tongue. |
| 2 | 199 | But a flight attendant smelled… | Her trolley comes down the aisle; she stops and sniffs, and the camera pushes to her face. |
| 3 | 373 | …and caught him in the act | Over her shoulder: the flame at the shoe, and he looks up. |
| 4 | 481 | Passengers and crew tackled him… | The trolley is knocked aside, a tray table drops, a cup spills, and the pile pins him in the aisle (seen from above). |
| 5 | 655 | …finally sedated | The steward's syringe goes into his upper arm, and he goes limp. |
| 6 | 769 | When they checked his shoes… | The attendant walks to his feet and pulls off both sneakers (he's in socks). She holds them sole-up, and a tan fuse cord pokes out of each sole. |
| 7 | 1069 | Both shoes were packed… | The cyan studio. Both sneakers split into a cutaway, showing a plain grey slab with a glowing edge. |
| 8 | 1249 | …bring down the entire plane | From beside the fuselage, past the engine and wing, to a wide pull-out over the cloud deck. |
| 9 | 1393 | And that's why you have to take your shoes off… | The airport security belt. The traveller steps out of his sneakers, picks one up and drops it in the grey tray, the tray rolls into the X-ray, and the camera settles on him in socks. |

## Known open items
- **Reach:** the audit (`../ShoeBomber_v001/review/C_audit.txt` and `review/D_audit.txt`) still flags reach misses during fast transitions:
  - the running steward, f451–521;
  - PaxB getting up, f461–581;
  - the attendant's grab, f501–561.
  In holds, the bomber's own left hand behind his back misses by up to 0.18 m and the officer's hands on the desk by about 0.17 m.
- **Shirt deformation:** the bomber's T-shirt deforms into a blob when he lies face down (an MPFB clothing limit at that pose).
- **Cabin smoke:** it's a low-density volume and shows as grain at low samples. At 48 samples plus denoise it should be clean; check frame 120.
- **Clouds:** the puffs in the sky beat read as soft cotton-ball cumulus, which is stylised rather than photoreal.
- **Feet:** they are masked inside the sneakers and get sock-coloured faces once the shoes are off.
