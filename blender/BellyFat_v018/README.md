# BellyFat_v018: the from-scratch rebuild (batch 1, film 10)

**Status: ON HOLD.** Pushed on the director's instruction after the render check passed. My own watch passes it; a fresh reviewer still marked it FAIL (see `review/CHECK4.md` for each item and the evidence). Watch `review/preview.mp4` before it goes to the client.

One woman, one bullet, one continuous camera. Built to the client's VO (the v017 timing), frames **1–1273** at 60 fps. The render sheet is `SETTINGS.md`; attribution is in `CREDITS.md` (all CC0); the scripts are in `scripts/` (00 shirt texture, 01 build, 02 animate, 03 package).

## The film
- **Outside on a sunny terrace:** an orange facade with blue shutters and a white French window, one leaf open. She stands inside in a teal living room. The bullet streaks in and cracks the closed pane (f30).
- **The chase:** the camera glides in through the open leaf. She turns, startled. The bullet flies at her belly in slow motion with a short trail, with her face and the DA KRAS FILMS print in frame.
- **The impact:** the shirt dents, then a short warm flash around the bullet (f133–147). Inside the flash the same bullet comes out in a real-scale cross-section.
- **The cross-section:** shirt, skin, yellow fat lobules with three fascia sheets, red muscle, peritoneum and bowel loops. The bullet pierces the skin, slows layer by layer (the wound track forms, and the fat squeezes and ripples ahead of the nose), and stops with its nose at the muscle. A pull-back shows the untouched bowel below.
- **The way out:** up the wound track, through a short flash (f1135–1139), to the hole in her shirt. The camera pulls out to her face. Her right hand rests flat on her belly beside the hole; she looks down, then up, and exhales.

## The client's extra lessons
- One character model for the woman, all film.
- Solid bodies: real CC0 MakeHuman T-shirt and jeans garments, given thickness, and no crotch frames.
- One bullet object, never held by a hand, with no pop-ins.
- The window reads clearly, in colour.
- The hand rests flat and relaxed on the belly.

## Render check: PASS
On the exact file `BellyFat_v018_60fps.blend` (65 MB), opened with `blender --factory-startup -b`:
- No linked libraries, no unpacked images, and the VO sound is packed.
- No drivers, no Python, and no errors or warnings, apart from one Blender deprecation notice from the check script itself.
- Camera `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–1273, PNG to `//render/BellyFat_v018_####.png`, and the VO strip at frame 1.
- Test frames rendered at full resolution, 64 adaptive samples, on a 4-core CPU with no GPU: f20 in 187 s, f600 in 247 s and f1240 in 232 s. None is black, empty or pink.
