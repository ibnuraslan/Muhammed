---
name: story-short
description: Turn a script + voiceover into a fully animated vertical story short (TikTok/Reels/Shorts, "follow for part 2" style) using the shorts-maker 3D animator. Use whenever the user sends a script and/or a voiceover file and wants a video, asks for a new episode, part 2, or a storyboard, or gives feedback on a video made this way.
---

# Story Short: script + voiceover → animated video

The user sends **a script** (text) and **a voiceover** (audio file). You deliver a finished
1080×1920 animated MP4: 3D sets, moving cameras, 2D cartoon characters, word-synced captions.
Nothing else is required from them. No reference videos, no art.

Everything runs on the engine in `shorts-maker/` (Python + ffmpeg for timing/captions/mix,
three.js in headless Chromium for the animation). It's all code: no AI image/video services.

## Before you start (every time)

1. Read `references/lessons.md`. It holds everything the user has taught us. Its rules override
   anything else in this skill.
2. Read `references/style-bible.md`. It covers the cast, colour codes, look and camera language. Never break it
   without the user's say-so.
3. Skim `references/engine-api.md` so you know which sets, props and poses already exist.

## Project setup

```bash
cd shorts-maker
slug=<short-kebab-name-of-story>          # e.g. railroad-gaps
mkdir -p projects/$slug
cp <user's script>  projects/$slug/script.original.txt
cp projects/$slug/script.original.txt projects/$slug/script.txt
cp <user's voiceover> projects/$slug/voice.mp3        # any audio format; keep the name voice.*
python3 make_short.py projects/$slug --timings-only   # whisper-times every word → timings.txt
```

`script.txt` must contain the **exact words spoken**, one sentence or beat per line. If the
voiceover differs from the script (ad-libs, cut lines), edit `script.txt` to match the audio,
because captions come from the script text. `timings.txt` shows when every line is spoken.
Plan with it.

## The three phases

Each phase writes a file in the project folder. Do them in order and don't skip ahead: a
weak analysis makes a weak storyboard, and a weak storyboard makes a slideshow.

### Phase 1: Analyse (`01-analysis.md`)
Understand the story and gather the raw material. Follow `references/phase1-analysis.md`:
beat map with timings, the hidden fact / twist, era + setting research (use WebSearch for real
facts and for what things actually looked like), cast mapping to the recurring characters,
visual metaphors for every abstract line, a long list of scene ideas including at least
5 "crazy" ones, and a list of the sets and props needed (existing vs. to build).

### Phase 2: Storyboard (`02-storyboard.md` + markers in `script.txt`)
Turn ideas into shots. Follow `references/phase2-storyboard.md`: one shot every 0.8–2.5 s cut
on strong words, each with a set, shot size, camera move, **character action**, emotion,
props/FX and a "why it's interesting" note. Run the variety and wow checks. Then put the `[NN]`
markers into `script.txt` and run `--timings-only` again to confirm the shot lengths.

**Checkpoint:** if the user said "storyboard first" (or this is a brand-new kind of story), send
them the storyboard table and stop. Otherwise post a 3–5 line summary of it and carry on.

### Phase 3: Produce (sets → `animation.js` → previews → render)
Follow `references/phase3-production.md`:
1. Build missing sets/props/characters as **reusable** functions in `animator/props.js` /
   `animator/cast.js`, and add them to `references/engine-api.md`.
2. Write `projects/$slug/animation.js`, one function per shot (start from
   `templates/animation.js`).
3. **Preview loop (mandatory, at least 2 rounds):**
   `python3 make_short.py projects/$slug --preview` → Read every `preview_N.jpg` → run the
   self-review checklist → fix → re-preview just the fixed shots with `--shots 03,07`.
4. Full render: `python3 make_short.py projects/$slug` (about 10 min per 40 s; run it in the background).
5. Check the final: make a 1 fps contact sheet, Read it, and confirm the captions and cuts match the voice.
6. Deliver with SendUserFile, plus a short note on what's in it and any weak shots you know about.
7. Commit the project folder (not the mp4s) and push.

## After delivery: the training loop

Ask for feedback in one line: "Score 1–10? Best shot? Worst shot? Anything to change in the
characters or colours?" Then:
- Append every piece of feedback to `references/lessons.md` (date, project, what they said, the
  rule you derived). Write the *rule*, not just the incident.
- If a rule is about the look or the cast, update `references/style-bible.md` too.
- If it's a missing capability (a set, a pose, an effect), build it into the engine so the
  next episode gets it for free.
- Fix the current video if they ask, re-render, and re-deliver.

## Hard rules
- Never hand over still images with zoom/pan as "animation". Every shot needs real motion of
  the camera **and** of something in the scene.
- Never skip the preview loop. Problems are cheap to fix in previews and expensive in a full render.
- Recurring characters always look the same (style bible). Never redesign the cast silently.
- Don't copy another creator's characters, logos or exact scenes. Our cast is our own.
- Keep facts plausible: research the real history, then dramatise it. Don't invent fake facts
  and show them as real (a fake newspaper headline inside the story is fine).
