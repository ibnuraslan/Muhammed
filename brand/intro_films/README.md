# Seldom intro films 5–8: key frames for review

The scripts are on `claude/mary-celeste-p4` (`mary_celeste_p4/intro_concepts/SELDOM_INTRO_CONCEPTS_P4.pdf`).
Each film has 3 story key frames plus the logo hold. They are 1280x720 Cycles previews at 32–48 spp, rendered on CPU.
The full animation has not been rendered.

| Film | Sheet | Logo on |
|---|---|---|
| 5 Projection Booth | `frames/film5_sheet.jpg` | The title card on the leader, projected for real: a spot light carries the film frame through the lens, so the beam and the screen take its shape |
| 6 Ice Station | `frames/film6_sheet.jpg` | Brush paint on a rusted 200 l drum: a paint layer with flakes and brush ridges, rime on the edges |
| 7 Darkroom | `frames/film7_sheet.jpg` | A real sign painted on a night brick wall, rendered as a photograph (`assets/seldom_sign_photo.png`, made by `scenes/sc7_photo.py`) that develops on the print |
| 8 The Archivist | `frames/film8_sheet.jpg` | An embossed brass plate with lime enamel: real relief displaced from the art's alpha, four rivets |

The logo always comes from the official art (`brand/seldom_logo_original.webp` on `claude/killer-in-house`, cropped to
`assets/seldom_logo_tex.png`) and is used as a texture or a light. There is no 3D text. Every letter, the `d` included, was checked in the close frames.
The 'o' counters are transparent in the art, so the surface underneath (paper, brass, drum, screen) shows through them.

## Cast and lib
* Scenes run inside `mary_celeste_3d/` from `claude/mary-celeste-3d`: copy `scenes/*` into its `scenes/` and `assets/*` into its `assets/`.
* Cast:
  * 5: Deveau, as the projectionist.
  * 6: Deveau with a cap, gloves and a head torch, as the researcher. The script says "she", but the shared cast has no woman dressed for the polar cold, so he is a man for now. Flag it if this matters.
  * 7: Briggs, as the photographer.
  * 8: Sarah, bonnet off, as the archivist, in a dark navy dress with a bottle-green knitted shawl worn like a cardigan.
* `tools/mh_from_mpfb.py` builds `assets/makehuman` from the preinstalled MPFB, the MakeHuman CC0 system assets and the
  `makehuman` PyPI wheel. The proxy blocks download.tuxfamily.org, so the MH 1.x rig is converted from MPFB's
  standard rig; it gives the same bones and joint names.
* Render one frame: `SHOT=1..4 SPP=48 blender -b --python scenes/sc5_booth.py` (outputs to `out/intros/`).

## Not done yet (after approval)
* Farm packaging per `FARM_DELIVERY_RULES.md`: MASTER.blend with a scene camera, independent zips under 300 MB,
  2560x1440, 24 fps, 64 spp, and a fresh-unzip test.
* Animating the moves between the key frames.
