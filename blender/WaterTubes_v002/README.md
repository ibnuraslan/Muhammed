# WaterTubes v002: farm package (checkpoint D)

- `WaterTubes_v002_60fps.blend`: 78 MB, packed and compressed, a normal git file (no LFS). It opens and renders in factory Blender 5.2 (`--factory-startup`); see `package_check_factory_lowres.jpg`.
- 1080×1920, 60 fps, frames 1–2010 (33.5 s), one camera, Cycles. Settings are in `SETTINGS.md`.
- `beats.json`: beat start frames for the VO retime (`pipeline/retime_to_vo.py`). There is **no VO mp3 yet**: our script has no recorded narration, so the director adds it at retime.
- `CREDITS.md`: the CC-BY block for the video description.
- Build scripts and review sheets are in `../WaterTubes_v001/` (scripts/, stills/).

## Look
Animated-CG look per `STYLE_ANIMATED.md` (client, 22:45 UTC):
- AgX Punchy, high-key light, no motion blur, f/6.
- A stylised storm sky that clears to the cyan-to-white sky by beat 8.
- A sky-blue gradient cutaway shell, and clean saturated blue section water with animated caustics.

## Checks
- **Hand audit** (BVH, every 2 frames; hand vs hand, own torso/head/shirt, other characters): **0 hits**.
- **Hands:** finger, thumb and wrist bones have Limit Rotation; grips use thumb opposition.
- **Camera:** never inside geometry or below ground (`audit.py`).
- **Text:** no text or logos. Shirt prints are patched out, the car's licence plate is blank, and its badges are removed.

## Known issues
- Contact audit samples (every 5th frame) show feet more than 4 cm above the surface mostly mid-swing and on the porch steps. Planted feet look grounded in the close-ups.
- The rounded start cap of each tube shows a small crease where the end fan closes.
- In the beat 1 close-up, the right fist sits on the hose at the nozzle rather than visibly wrapping the brass nozzle.
- Beat 1 opens with a sidewalk slab large in the foreground (a low ground-skim start).
- The storm sky is soft grey-blue rather than a clear blue sky until beat 8, because the story needs the storm.
- No VO yet; beats are built to the brief's target times.
