# BellyFat_v002: farm package

This is the full 21.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `BellyFat_v002_60fps.blend`: the self-contained scene, with every texture packed. One camera, `CAM_Film`.
- `SETTINGS.md`: render settings, the visibility-swap note, test frames and the VO retime steps.
- `CREDITS.md`: everything is CC0 or made for the film, so no CC-BY block is needed in the video description.
- `beats.json`: the start frame and first words of each beat, for the voiceover retime. `anchors_template.json` is the matching input for `retime_to_vo.py`.
- `package_check_lowres.jpg`: frames 60, 900 and 1270 from the packed file opened in factory Blender, at 20 % and 4 samples. It shows that the package works; it is not a quality reference.

The source is `../BellyFat_v001/` (`build.sh`, then `scripts/`). The review sheets are in `../BellyFat_v001/stills/` and the audit is `../BellyFat_v001/audit_C.txt`.

## The film
| # | t (s) | Line | Picture |
|---|---|---|---|
| 1 | 0.0 | A stray bullet struck her | Supermarket aisle; the woman reaches to a shelf, a shopper pushes a cart, another crosses the back. A slow dolly whips onto a slow-motion bullet and rides it. |
| 2 | 2.0 | right in the stomach | The tip touches the tee and the fabric dimples and ripples. She jolts, the basket drops and cans fall. The camera dives to the fabric. |
| 3 | 3.0 | It pierced her skin… slow down | Tilts over the edge: it's a cross-section. Skin dimples and pierces; the bullet enters the yellow fat and decelerates. |
| 4 | 7.8 | Layer by layer… like a cushion | Lobules squash and part, warm energy rings bloom and fade, and fat droplets shed from the channel. |
| 5 | 12.6 | reached deeper tissue | Red muscle fibres bow aside as the bullet barely creeps. |
| 6 | 14.8 | lost most of its force… stop | It stops 8.7 mm short of the glossy intestines; the camera orbits it on the open side. |
| 7 | 20.1 | saving her life | Rises out through the fat to the fabric, then pulls back to her: alive, shocked, one hand up, the other pressed to her side. |

## Known issues
- **No voiceover yet.** The film is timed to the brief's beat table. Retime with `beats.json` when the VO arrives.
- **The ending is short.** She is on screen for 1.3 s after the pull-out, so beat 7 relies on her pose more than her acting. A longer settle needs the VO length.
- **The orbit is a half-orbit.** In beat 6 it covers the open cut-face side only, swinging about 110° plus a crane up and down, because the far side is inside the tissue block.
- **Background shoppers act only in silhouette.** Shopper A freezes with his hands up after the bang. Shopper B turns her head. Neither gets a close-up.
- **f121 speed ramp.** Camera speed falls from about 27 to 7 macro units/s over 6 frames at impact. This is a deliberate slow-motion ramp, and the audit flags it as a jump.
- **Macro tissue is stylised explainer anatomy.** Lobules are about 1 cm, larger than real ones, so the cushion idea reads; there are no blood or gore details.
