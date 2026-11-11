# ElectricianPolice_v003: farm package (animated look)

v003 is v002, with every director note in, moved to the client's animated-CG look from 22:45 UTC (`../STYLE_ANIMATED.md`). Nothing in the animation or geometry changed. The look changes are:
- `pipeline/anim_look.py`: AgX Punchy, a cyan-to-white sky gradient for the camera, saturation ×1.25, bump ×0.35, roughness at least 0.35, f/5.6, motion blur off and volumes halved.
- `../ElectricianPolice_v001/scripts/04_anim_tune.py`: brighter keyed world, sun and exposure; an evening-blue sky; and a readable blue night in the station from a cool window fill plus a soft front key.

This is the full 26 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

## Files
- `ElectricianPolice_v003_60fps.blend`: the self-contained scene. Every texture is packed inside.
- `beats.json`: the start frame of each of the 11 beats, built to the brief's target times. When the voiceover arrives, run `pipeline/retime_to_vo.py` to warp every key onto its words, then repackage.
- `SETTINGS.md`: render settings and suggested test frames.
- `CREDITS.md`: the CC-BY credit block for the video description.
- `package_check_f1306_lowres.jpg`: a 270×480, 8-sample frame from the packed file opened in factory Blender. It shows the package works; it is not a quality reference.

## Voiceover
There is no VO mp3 yet. The script is ours (73 words) and is in `../briefs/14_ElectricianPolice.md`.

## Source
The source is `../ElectricianPolice_v001/scripts`. Build order:
1. `01_build_humans.py`, once per character.
2. `02_build_scene.py`.
3. `03_animate.py`, which runs `03b_fx_camera.py`.
4. `slim_textures.py`.
5. `pipeline/anim_look.py`, then `04_anim_tune.py`.
6. `pipeline/package_for_farm.py`.

`audit.py` is the contact and camera audit. Its latest report is `../ElectricianPolice_v001/review/C_audit.txt`.

## Beats (frame = 1 + 60·t)
| # | Frame | Line | What happens |
|---|---|---|---|
| 1 | 1 | "He was riding his motorcycle without a helmet" | Low chase alongside the bike through a busy market street with saffron and teal walls, marigold strings, vendor carts, rickshaws, cows, 8 pedestrians and dust haze. His hair and shirt ripple in the wind. |
| 2 | 169 | "and the police gave him a fine" | The officer waves him over. He brakes and puts a foot down. The officer writes the ticket and the slip passes hand to hand. |
| 3 | 283 | "But he was an electrician" | He pulls the hard hat off the seat and onto his head. A whip-pan lands on him at the substation gate in a hi-vis vest. |
| 4 | 397 | "with access to the power grid" | He unlocks the gate and walks in. The camera cranes up the pylon as pulses run out along the lines over the town. |
| 5 | 505 | "So he checked the records" | The camera dives through the office window to his laptop. The record bars load as he types. |
| 6 | 619 | "...the police station hadn't paid..." | The police row turns red with a badge icon. Three calendar pages flip. He leans in with a slow grin. |
| 7 | 895 | "And that bill was huge" | The red bar bursts out of the screen across the room. He throws his arms up. |
| 8 | 1057 | "so he cut off their power" | His gloved hand throws the big lever. There is a clunk, sparks and an arc flash, and the cabinet lamps die. |
| 9 | 1165 | "the police station sat in the dark" | The camera backs out of the window and flies over the roofs at dusk. The station windows go dark one by one. |
| 10 | 1231 | "For five hours" | The camera flies through a dark window into the station and passes five officers: one fans himself with a paper, one taps the dead ceiling fan with a file, one holds a phone torch, one fans himself and wipes sweat by the water cooler, and one is slumped with his head back. The fan winds down and the clock spins five hours. |
| 11 | 1381 | "all because they fined the wrong guy" | The camera backs out through the door. He strolls past the dark station, turns to camera and smirks. |

## Review
`../ElectricianPolice_v001/review/v003_animated_look_1s.jpg`: one still per second, 270×480, 8 samples.

## Known issues
- **Animated look:** the whip-pan at 5.3–5.6 s has no motion blur any more (look rule), so it reads as a fast pan. The building boxes keep their scanned plaster textures, only softened. The face framing at about 13 s still drifts to the frame edge between two camera keys.
- **Hi-vis vest:** the vest is cut from the shirt mesh, so the armholes are a little lumpy, and in close-ups the top edge looks torn.
- **Hands:**
  - The hands-in-pockets at the end are approximate: the hands rest at the pocket line rather than inside it.
  - The fanning paper and the phone are parented to the wrists. Finger grips are curls, not per-finger contact.
- **Feet:** the walks show 2–4 cm of heel or toe lift on some contact frames (`C_audit.txt`). Planted feet are on the floor.
- **Characters:** the 5 officers and 8 street extras are re-proportioned clones of 4 MPFB bodies, with tinted clothes. Background clones have no teeth or tongue meshes. The street dog was dropped because it read as a food tray at review size. The rickshaw model's food-brand livery was repainted plain green with a yellow roof.
- **Penetration (BVH, sampled every 12 frames):** 4 frames: 2 where his legs touch the bike seat while riding, and 2 where the hard hat passes through his hand as he grabs it. There is no lip-sync, because there is no VO yet. The grin and smirk use the lip-corner bones only.
- **Interior:** the station interior at dusk is dim blue rather than pitch black, so the action reads. The phone torch is a spot light with no visible beam.
- **Screen and clock:** the laptop UI is emissive 3D planes (icons and bars) with no text. The clock's maker's mark is covered by a dial-coloured disc.
- **Camera:** from 22.4 to 23.4 s the camera turns across a fairly empty back wall of the station.
