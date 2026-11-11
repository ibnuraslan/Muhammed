# RooseveltSpeech_v002: farm package (checkpoint D)

A 25.0 s vertical short (1080×1920, 60 fps, frames 1–1500). One continuous camera with no cuts.

## Contents
- `RooseveltSpeech_v002_60fps.blend`:
  - Everything is packed and compressed: about 78 MB, with textures at 1K (hero skin 2K) and a 2K HDRI.
  - It opens and renders in factory Blender 5.2.2 (`--factory-startup`). See `package_check_factory_lowres.jpg`.
- `SETTINGS.md`: the farm render settings.
- `CREDITS.md`: the CC-BY block for the video description.
- `../RooseveltSpeech_v001/beats.json`: beat start frames for the VO retime.
- `../RooseveltSpeech_v001/scripts/`: the full rebuild, in order:
  1. `01_build_humans.py`
  2. `02_build_scene.py`
  3. `03_animate.py`, which runs `03b_crowd_camera.py`
  4. `04_shrink_textures.py`
  5. `pipeline/package_for_farm.py`
- Review material in `../RooseveltSpeech_v001/review/`: the B and C sheets, close-ups and audit.

## Voiceover
- **No VO mp3 is included.** None was supplied tonight.
- The animation is built to the target beat times in the brief.
- When the VO arrives:
  1. Run `pipeline/transcribe.py`.
  2. Map each beat's first word to its start time.
  3. Run `pipeline/retime_to_vo.py` with anchors `[[beat_frame, null, word_seconds], ...]`, taking the frames from `beats.json`.

## Beats
| # | Frame | Time | What happens |
|---|---|---|---|
| 1 | 1 | 0.0 s | Night street, crowd and car. The shooter silhouette flashes, and the camera rides the bullet to his chest. |
| 2 | 187 | 3.1 s | He sways, steps back, grips the brass rail and straightens. The crowd recoils and the shooter is grabbed. |
| 3 | 337 | 5.6 s | Time slows to 3 %. The camera orbits to the coat breast. |
| 4 | 445 | 7.4 s | X-ray porthole and cyan studio dome. The folded 50-sheet manuscript glows. |
| 5 | 721 | 12.0 s | The steel glasses case glows. |
| 6 | 877 | 14.6 s | The slow-motion bullet punches the sheets (ripple and flecks) and dents the case. |
| 7 | 1003 | 16.7 s | Ribs and breathing lungs. The bullet rests in the muscle with a glow ring at the gap. |
| 8 | 1189 | 19.8 s | Pull out at the podium. The set was swapped behind the dome. He pulls out the holed manuscript and lifts it. |
| 9 | 1285 | 21.4 s | Fist raised and speaking. The packed hall roars, flags ripple, the clock spins and the camera cranes up. |

## Known issues
- **Hand–rail contact:** two audit samples show the left fingers about 4 mm inside the brass rail while gripping. It's not visible at 270×480.
- **Moustache:** particle hair on a small base. It reads as a solid walrus moustache from low angles.
- **Face:** generic MPFB, with no likeness, by design. The temple arms of the spectacles stand slightly off the head (no intersection).
- **Car footwell:** it is dark, so the feet are judged by the numeric audit (0 hover, sink or slide).
- **Ghost body:** in the x-ray, the hero's teeth and tongue can be seen faintly through the ghosted head at about 19 s.
- **Hall crowd:** about 150 FK-animated MPFB instances. Their hands don't touch each other (claps are open-hand motions), and they are not audited for penetration against one another.
- **Car model:** a CC-BY Model T mesh, with no badge or script on the mesh. Its name appears only in the credits.
