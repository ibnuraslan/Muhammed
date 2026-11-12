# Documentary pipeline: style, workflow, tools

This is the playbook every project chat follows. The reference project is `nvidia_doc/` ("The Spy Allegations
Rocking Nvidia"). Read this whole file before starting.

## 1. Setup (fresh machine)

```bash
bash pipeline/setup.sh
source ~/render_env/env.sh
```

This takes about 5–10 minutes. It gives you Blender 5.2 as a Python module (`bpy`), Skia, faster-whisper and the
MakeHuman CC0 assets (`MH_DATA`). Poly Haven assets (CC0 scanned models, textures and skies) download themselves on
first use through `nvidia_doc/scenes/ph.py`. Cycles renders on the CPU.

## 2. The house style (what the person wants)

The look is the Iceman film and the fern-channel documentaries: CG that feels cinematic and real, never cartoon and
never photos.

- **Cinematic look (Nov 2026, every film).** A day must never look like a plain bright camera day. Tone a little
  dark, moody, filmic. Light every set with `look.py`, at the end of `build()`:
  - **One strong directional key**: a window or the sun, from the side or behind, never from the camera.
    - Exteriors: `look.day_light("overcast" | "low_sun", azim=..., haze_box=...)` (low sky, one sun lamp, haze).
    - Interiors by day: `look.interior_day(window=(point, target), mood=...)`, plus `look.gobo(...)` for window
      bars or blinds, so the sun lands in patches.
    - Night: `look.night_interior()`.
  - **Negative fill**: other lights cut to ~10–15%, low world strength, no flat ambient.
  - **Dark walls and floors**: plain albedo capped at ~0.3, no white rooms.
  - **Warm practicals**, and light haze in exteriors and forests.
  - **Grade**: `grade.add_grade` defaults to `look="cinematic"`: contrast around mid-grey, rolled-off highlights,
    teal blacks / amber highlights, saturation 0.8, stronger vignette. It runs on scene-linear light before AgX.
  - Night stays readable, never crushed.
  - `run.py --plain` renders the old look, and `--exr` + `look_sheet.py` make before/after sheets.
  - Reference: `nvidia_doc/review/cinematic_look_v1.jpg`.
- **Light.** Within that look: dawn, overcast day, low late sun, blue-hour dusk, readable night.
  Night only where the story is at night. Avoid neon glitter: no fields of "glimmering lights", no random glowing
  boxes, no flat emissive rectangles standing in for signs or screens.
- **Palette.** Cool and desaturated (steel, slate, warm skin and practical lamps), darker overall. One accent color at most.
- **Assets.** Use real scanned assets from Poly Haven for furniture, plants, props and floors (`ph.model`,
  `ph.texture`). Never build trees or furniture from primitive cones and boxes. Cities and skylines are CG in the
  house style (`sc_home.facade`, `sc_city.py`), not HDRI photos.
- **People.** People are the subject and do one clear action: typing, walking, signing, reading, passing a folder.
  - Use MakeHuman for people (`human.py`, `people.py`), seen at medium or wide distance.
  - Avoid close-ups of hands and skin. The thumb macro was rejected.
  - Faces are fine in soft light, at three-quarter or in profile.
  - Facing: rotation z = θ turns the rest pose (facing −Y) to face (sin θ, −cos θ). Check that people face their
    table, desk or screen. That bug shipped once.
- **Camera.**
  - Keep every move slow and steady: push, pull, track, crane.
  - Never tie a camera to a bone or a moving body, or it lurches into the person.
  - Never put a camera inside furniture or a person. Check every shot with a test frame.
  - Shoot at 2.35:1, 1920×816, 24 fps.
- **Animation.** Nothing is static. In every shot something moves (a person, vehicles, water, flags, LEDs, rain,
  screens) and the camera moves. Everything is keyframed or frame-driven so it plays in any external render (see §5).
- **Text.** Chapter cards are "CHAPTER N" small over a bold Roboto Slab title with a glow, over the live first shot
  of the chapter (`title_card.add_title`). Use no other graphics unless the person asks. The intro has no title.
- **Grade.** Soft bloom, slight lens dispersion, a vignette and the cinematic tone above (`grade.add_grade`).
  Add grain in the edit.

## 3. Planning (do this first, and get it approved)

The person wants a solid plan before anything is built, presented exactly like this:

| Set | Script line | Shot A | Shot B |
|---|---|---|---|

- **Set = one location.** Each set covers a script passage with two shots, A and B.
- **Cells are short.** Write one plain sentence per shot. The person dislikes long text and long messages.
- **Reuse sets across chapters**, the way the reference does. For example, the investigation room, the data hall,
  the street, the café and the Capitol all return.
- **Pick creative, specific, cinematic action**, never "a building" or "a map". Map or graphic shots were rejected
  (no globe with a red barrier).
- **Short messages to the person.** They are busy and blunt. Use tables, not essays. Show images.

## 4. Build loop (per set)

1. Write a `scenes/sc_<set>.py` with `build(variant)`, the animation functions and `MOVES` (one per shot, with
   `cam`, `focus`, `anim` and `dof`). Copy the patterns in `nvidia_doc/scenes/` (`sc_home.py`, `sc_invest.py`,
   `sc_dchall.py`, `sc_corp.py`, `sc_street.py`).
2. Test-render a still:
   `python scenes/run.py <set> <move> --still --t 0.5 --pct 25 --samples 8 --out <dir>`
   For driver-based effects, call `frame_set(N)` first. Look at it and fix it until it reads.
3. Make labelled preview sheets of every shot (see `nvidia_doc/out/ch2_preview/`) and send them. Iterate on the
   feedback.

## 5. Delivery: one .blend per chapter (the person renders externally)

- `python scenes/bake.py <set> <move> --seconds S --out out/blend/<chapter>` bakes each frame into keyframes:
  camera, focus, lens, every rig bone and every moving object. It packs the textures and saves a self-contained
  `.blend`. Phone or screen UI image sequences sit beside the file in `*_ui/`.
- Frame-driven effects (LED blinks, screens switching, flashes, fades, police lights) use simple driver
  expressions such as `frame`, `min` and `max`. These play without enabling scripts.
- `python scenes/make_master.py <chapter> out/blend/<chapter> vo/<chapter>.mp3` grades every shot and links them
  into one master `.blend`, with a timeline of scene strips in order and the voiceover underneath. The person
  renders that one file. Add the chapter's shot list to `CHAPTERS` in `make_master.py`.
- **Lead-in.** Every film opens on about 2.5 seconds of picture before the first word, so viewers settle in and
  don't miss the opening line. Extend the first shot by the lead and start the voiceover strip 60 frames in
  (`make_master.py` takes the lead in seconds as its 4th argument; it defaults to 2.5 for the intro). Chapter
  openings let the title card breathe about 2 seconds before narration resumes.
- **Timing comes from the voiceover.** `edit/align.py: transcribe()` gives word times, and each shot's seconds are
  cut at the word where its line starts.
- **Do not render the film yourself unless asked.** When asked for a preview, use `scenes/preview_render.py`
  (50%, 16 samples, every second frame) and `scenes/preview_cut.py`.

## 6. Git

- Work on your own branch. Commit and push after every set.
- Never commit `assets/polyhaven/`, `out/blend/` or preview renders. They are git-ignored.

## 7. New project layout

```
projects/<slug>/
  script.txt            the narration verbatim
  PLAN.md               the approved Set | Script line | Shot A | Shot B tables, per chapter
  scenes/sc_*.py        this project's sets (import the shared helpers from nvidia_doc/scenes)
  vo/                   voiceovers as they arrive
  out/                  previews (git-ignored) and blend/ deliveries (git-ignored)
```

Run the shared tools with the project's scenes on the path, so `run.py` and `bake.py` find your `sc_*.py` and the
shared `kit`, `human`, `ph`, `people`, `grade` and `title_card` modules:

```bash
PYTHONPATH=projects/<slug>/scenes:nvidia_doc/scenes python nvidia_doc/scenes/run.py <set> <move> --still ...
```

Reusing a set from another project (for example the data hall, investigation room, street or café) is encouraged.
Import it, or copy it into your scenes folder and adapt it.
