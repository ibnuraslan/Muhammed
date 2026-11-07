# The Zipper: a vintage history short

`zipper_story.mp4` is a 1080x1920 vertical video, 49 seconds long, in a vintage paper-and-wood collage style.

All visuals are drawn in code with HTML canvas: wood and paper textures, characters, props, kinetic typography, film grain and whip-pan transitions. No stock footage or images are used.

- **Voiceover:** Piper TTS, voice `en_US-ryan-high` (`source/build_vo.py`)
- **Music and sound effects:** made in code with numpy and scipy (`source/audio.py`)
- **Frames:** rendered with headless Chromium through Playwright (`source/capture.js`)

## How to rebuild
1. Run `build_vo.py` to make `vo_full.wav` and `timeline.json`.
2. Write the timeline into `timeline.js` as `const TIMELINE = {...}`.
3. Run `node capture.js frames all 4`.
4. Run `python3 audio.py`. It reads `../vo/vo_full.wav` and `../vo/timeline.json`, so keep the VO folder next to this one or change those paths.
5. Combine the frames and `mix.wav` with ffmpeg.
