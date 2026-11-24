# The Army That Fought for a Country That Didn't Exist Yet

A 10.5-minute documentary about the Czechoslovak Legion (1914–1920). It is rendered in a cel-shaded "2D-3D" style: three.js toon shading with outlines, painted skies, and 2D map overlays.

- `legion.mp4` – the finished film (720p preview encode, 630 s).
- `source/` – the render pipeline.

## Pipeline

| File | Role |
|------|------|
| `engine.js`, `engine2.js`, `face.js` | Scene engine, character builder (uniform kits, poses), stylised faces |
| `lib3.js` | Shared library: sets, skies, trains, flags, explosions, camera helpers, shot runner |
| `props.js` | Rooms, furniture, ships, sea, trenches, cranes and other props |
| `maps.js` | 2D canvas maps: Austria-Hungary, routes, the Trans-Siberian, newspapers, documents |
| `sec1.js` … `sec6.js` | The six sections of the film, with shots keyed to narration cues in `tl6.json` |
| `film3.html` / `film3.js` | Loads one section (`?sec=N`) and exposes `window.renderAt(frame)` |
| `cap3.js` | Headless Chromium frame capture, run in parallel: `node cap3.js <sec> out <workers> all` |
| `queue.sh` | Renders several sections one after another |
| `sheet.py` | Builds contact sheets for checking keyframes |
| `audio/audio7.py` | Music synthesis, SFX placement, and ducking under the voice-over → `mix7.wav` |

## Rendering

1. Serve the folder with `python3 -m http.server 8765`.
2. Render each section with `node cap3.js N out 4 all`.
3. Encode the frames with the audio:

   ```
   ffmpeg -framerate 24 -i out/%05d.jpg -i mix7.wav -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac out.mp4
   ```

Third-party files are not committed and need to be added next to `film3.html`:

- three.js 0.160 (`three.module.js`, `jsm/`)
- `topojson-client.min.js`
- `countries-50m.json` (world-atlas)
- the Cinzel font
- Poly Haven CC0 textures and HDRIs (`ph/`)

The voice-over is Kokoro TTS (`am_fenrir`), and the SFX are CC0 sounds from Freesound.
