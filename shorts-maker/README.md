# shorts-maker

Builds vertical **story shorts** (TikTok / Reels / YouTube Shorts) in the
"follow for part 2" format:

| What the viewer sees | How this tool does it |
|---|---|
| 1080×1920, 30 fps, ~35–45 s | fixed output format |
| narrator telling a story, plus a different voice for a character line | free neural voices (edge-tts), or your own `voice.mp3` |
| a new shot every 1–2 s | `[NN]` markers in the script cut to `scenes/NN.*` on that exact word |
| slow zoom / pan on every shot | automatic Ken Burns on images; video clips play as-is |
| big white 1–3 word captions with a black outline, lower middle, synced to each word | word timestamps from the TTS or from Whisper, burned in with libass |
| quiet music under the voice | `music.mp3`, auto-ducked when someone speaks |

Two ways to get the visuals:

* **Animated (built in):** write the shots as code in `animation.js`, and the tool renders real
  3D animation: moving cameras through 3D sets, plus 2D cartoon characters that walk, talk, get
  angry and hold props. `example/` is a complete animated episode. No AI services or assets are
  needed; everything is drawn in code.
* **Your own pictures or clips:** drop images or clips into `scenes/`. Images get a zoom/pan.

The tool does the voice, timing, captions, cuts, mix and export either way.

### Animated mode setup (once)

Needs [Node.js](https://nodejs.org) as well as ffmpeg and Python:

```bash
cd shorts-maker
npm install
npx playwright install chromium
```

`python3 make_short.py example` then renders the animated example. That takes a few minutes, since every frame is a 3D render.

How `animation.js` works: each `[NN]` in the script has a matching shot function. It builds a set
(`hangar`, `office`, `terminal`, `cabin`, `airfield`, sky...), places characters (`new Char(S, 'hero')`)
and props (`makeJet`, `newspaper`, `confetti`...), and returns `update(t, u)`. That function runs
every frame, with `u` going from 0 to 1 across the shot, so the action always fits however long
the narrator takes. A file in `scenes/` with the same number overrides the animated shot.
The engine lives in `animator/` (`engine.js` for the world and camera, `cast.js` for characters,
`props.js` for sets and props).

---

## 1. Install (once)

```bash
# macOS:   brew install ffmpeg
# Windows: winget install ffmpeg
# Linux:   sudo apt install ffmpeg
pip install -r requirements.txt
```

## 2. Make a video

```bash
python3 make_short.py example
```

That renders `example/out.mp4`. Grey "SCENE 03" placeholder cards stand in for
any missing art, so you can check the pacing before you make the art.

A new video is just a folder:

```
my_video/
  script.txt        <- required
  scenes/01.png     <- one picture or clip per [NN] marker (png, jpg, webp, mp4, mov...)
  scenes/02.mp4        file names only need to START with the number: 02_boss.png is fine
  voice.mp3         <- optional: your own narration (otherwise free TTS is used)
  music.mp3         <- optional: background music
```

```bash
python3 make_short.py my_video
```

### Script format

```
[01] He put tiny round windows on his airplane [02] when everyone wanted big square ones.
[03] You see, two companies are racing [04] to build the world's first jet airliner,
<en-US-ChristopherNeural> [12] Passengers want a view!
```

* `[NN]` cuts to scene NN **on that word**. Put one every 3–7 words to get the fast pace.
* `<voice-name>` at the start of a line reads that line in another voice (a character).
* Lines starting with `#` are comments.
* No `[NN]` markers at all? It auto-cuts every ~2 s and cycles through `scenes/`.

### Useful options

```bash
python3 make_short.py my_video --voice en-US-BrianNeural --rate +15%    # different narrator, faster
python3 make_short.py my_video --music lofi.mp3 --music-volume 0.12
python3 make_short.py my_video --pop               # captions pop in
python3 make_short.py my_video --uppercase         # ALL CAPS captions
python3 make_short.py my_video --font-size 100 --caption-y 0.65
edge-tts --list-voices | grep en-                  # see every free voice
```

Good free narrator voices: `en-US-AndrewNeural` (default), `en-US-BrianNeural`,
`en-US-GuyNeural`, `en-GB-RyanNeural`. Good "character" voices:
`en-US-ChristopherNeural`, `en-US-EricNeural`, `en-GB-ThomasNeural`.

A `timings.json` with every word's start/end is written next to the script.
Use it if you want to line up animated clips by hand.

---

## 3. The full workflow (how to get the same result)

### Step 1: the story (most important)

These videos work because of the script, not the graphics. Use this formula
(~110 words = ~40 s):

1. **Weird hook (1 line).** The strange thing the hero did. *"He left gaps in a railroad every 39 feet."*
2. **"You see,"** setup: a race or competition with big stakes. *"...whoever finishes first gets the whole country's business."*
3. **The underdog hero.** *"He's the youngest engineer on the job."*
4. **The boss hates it.** One short angry line in a character voice. *"You're wrecking my railroad!"*
5. **He refuses to back down.** *"But he won't close a single one."*
6. **The rival "wins".** The rival does it the obvious way and everyone loves it. The hero gets mocked with a nickname.
7. **Cliffhanger.** *"Then summer comes and something weird happens."* Then stop. Post with "FOLLOW FOR PART 2".

Part 2 reveals the hidden reason (the science or engineering), and the hero wins.

Good topics are any "why is it designed like that?" fact: round plane windows,
rail expansion gaps, holes in padlocks, why bridges have joints, square
milk cartons, the hole in pen caps, the shape of manhole covers, and so on.

### Step 2: the shot list

Go through your script and add a `[NN]` before each new image idea, about 20–25 per video.
Then write one line per scene describing what's on screen:

```
01  close-up: young engineer in flat cap kneeling on railroad tracks, train lights behind him
02  wide: tracks running along a giant red canyon wall, engineer small in frame
...
```

### Step 3: the art

The reference look is **simple 2D cartoon characters** (round white heads, dot
eyes, thin legs, hats) placed in **colourful, painterly 3D environments**, shot
from dramatic angles: low, wide, over-the-shoulder, close-ups on faces.

**Design your own characters.** Don't copy another creator's characters. Make
one character sheet (front, side, 3–4 expressions) for each of your recurring
cast: the hero, the boss, the rival. Reuse those sheets as the reference image
every time so the characters stay consistent.

Generate each scene in **9:16 (vertical)** with any image model that supports
a character or style reference image. Prompt template:

```
Vertical 9:16 frame. Stylized 3D environment, painterly textures, warm saturated
colours, cinematic lighting: <SCENE>. A simple flat 2D cartoon character composited
in: <CHARACTER from reference image>, <ACTION / EXPRESSION>. <CAMERA: low angle /
wide shot / close-up / over the shoulder>. No text, no captions.
```

Keep the bottom-middle of each frame fairly clear, because that's where the captions go.

**For the full "moving camera" feel:** turn your best stills into 3–5 s
clips with any image-to-video model ("slow dolly forward", "camera orbits
right", "character turns head") and save them as `scenes/NN.mp4`. The tool
loops or trims each clip to fit its slot. Stills alone (with the automatic
zoom/pan) get you most of the way. Animating the 5–10 most important shots
gets you the rest.

### Step 4: the voice

* **Free:** do nothing. edge-tts reads the script (Andrew narrator plus the
  `<voice>` lines).
* **Most natural:** generate the narration in a premium AI voice tool, or
  record it yourself. Save it as `voice.mp3` in the project folder. Read the
  script **exactly** as written: the tool listens to it (Whisper) and syncs
  the captions to every word automatically.

Pace: fast and conversational (~2.8–3 words per second), with no dead air.

### Step 5: music, render, post

* Put a light, curious, slightly whimsical instrumental in as `music.mp3`. Use
  royalty-free music, or add trending audio inside TikTok/Reels at low volume.
* `python3 make_short.py my_video`
* Caption: `FOLLOW FOR PART 2`. Post part 2 within a day, and pin a comment linking it.

---

## Credits

Captions use **Montserrat ExtraBold** (SIL Open Font License, see `fonts/OFL.txt`).
