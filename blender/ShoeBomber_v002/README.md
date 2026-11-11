# ShoeBomber_v002: farm package

This is the full 27.0 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

## Files
- `ShoeBomber_v002_60fps.blend`: the self-contained scene, 75 MB. Every texture is packed. Normal git file (no LFS).
- `beats.json`: the start frame and first words of each beat, for the voiceover retime (`pipeline/retime_to_vo.py`).
- `SETTINGS.md`: render settings, measured cost and test frames. `CREDITS.md` has the CC-BY block for the video description.
- `review/`: the final 0.2 s contact sheets, made from this packed file at 270×480 and 8 samples.
- `package_check_f120_lowres.png`: a 25 %, 4-sample frame from the packed file opened in factory Blender. It shows the package works; it is not a quality reference.

## Source and build
The scripts are in `../ShoeBomber_v001/scripts/`. Build order:
1. `01_build_humans.py`: MPFB humans
2. `02_build_scene.py`: the cabin, studio, sky and airport sets
3. `03_animate.py`: characters and props, with an automatic reach pass
4. `04_fx_camera.py`: attachments, fx, lights, grade, the camera and `beats.json`
5. `05_shrink_textures.py`: hero textures 2K, the rest 1K, JPEG diffuse maps, a 1K HDRI and an orphan purge
6. `pipeline/package_for_farm.py`

`audit.py` is the contact audit. It covers hover, sink, reach, camera-in-geometry and props, plus a BVH penetration count of hand and foot vertices into other bodies and the floor. `make_icons.py` makes the lane-sign pictograms (system Python with PIL) before step 2.

## Beats (target times; no VO yet)
| # | Frame | Line | Picture |
|---|---|---|---|
| 1 | 1 | In the middle of a flight… | A night cabin: dim blue light, shades down with a moonlit sliver, glowing seat-back screens, and passengers asleep under blankets. Low and in front, the bomber hunches over his sneaker; the match at the tongue is the brightest light and lights his face orange. |
| 2 | 199 | But a flight attendant smelled… | Her trolley comes down the aisle; she stops and sniffs, and the camera pushes to her face. |
| 3 | 373 | …and caught him in the act | Over her shoulder: the flame at the shoe, and he looks up. |
| 4 | 481 | Passengers and crew tackled him… | The trolley is knocked aside, a tray table drops, a cup spills, and the pile pins him in the aisle (seen from above). |
| 5 | 655 | …finally sedated | The steward's syringe goes into his upper arm, and he goes limp. |
| 6 | 769 | When they checked his shoes… | The attendant walks to his feet and pulls off both sneakers (he's in socks). She holds them sole-up, and a tan fuse cord pokes out of each sole. |
| 7 | 1069 | Both shoes were packed… | A cyan-to-navy studio. Both sneakers split into a cutaway, showing only a grey putty slab caught by a cyan rim light. There is nothing wire-like. |
| 8 | 1249 | …bring down the entire plane | Out of a cloud bank beside the fuselage, past the engine (with exhaust glow) and the wing, to a wide pull-out over a dusk cloud deck. |
| 9 | 1393 | And that's why you have to take your shoes off… | The airport security lane, with dusk light through the glass wall, a queue of travellers, an officer at the monitor and pictogram signs. The traveller steps out of his sneakers, picks one up and drops it in the grey tray, which rolls into the X-ray. The camera settles on him in dark socks. |

## Known open items
Audit: `review/D_audit.txt` (run on this packed file).
- **Camera inside geometry:** none, apart from the intended passes through the smoke wisp (f161–211) and the cloud bank (f1261).
- **Penetration (BVH):** 87 flagged samples (4,630 hand and foot vertices in total, cabin only, sampled every 30 frames). They are almost all in the tackle pile, f481–760: hands pressing into the bomber's back and arm, and the kneelers' feet overlapping. From the high camera this reads as gripping and pinning, but the meshes do intersect slightly.
- **Reach:** the remaining misses are in fast transitions: the running steward (f451–521), PaxB getting up (f461–581) and the attendant's grab (f501–561). In holds, the bomber's own left hand behind his back misses by up to 0.18 m and the officer's hands on the desk by about 0.17 m.
- **Hover/sink:** the bomber is up to 0.19 m off the floor during the fall itself (f531–571); the kneeling attendant's knees sit about 4.5 cm up; the running steward dips 10 cm (f541–561).
- **Shirt:** a corrective smooth is applied for the face-down pose, but some bunching remains.
- **Clouds:** the sky uses the dusk cloud deck plus volumetric banks for the crossings. Volumetric cumulus puffs cost about 140 s per preview still and the surface version looked like craters, so the puffs are hidden.
- **Realism replacements:**
  - Real models: the seats, airliner, sneakers, syringe, conveyor and detector.
  - Procedural pieces (no usable CC-BY airliner-interior model was found): the cabin shell, bins, windows and shades, the trolley and the terminal.
  - Detail added to the procedural pieces: displaced cloth on the blankets, displaced putty on the slab, and textured materials.
- **Voiceover:** none yet. Retime with `beats.json` when it arrives.
