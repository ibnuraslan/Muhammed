# Batch 2: instructions for each Connect chat

Your launch message gives `{NN}` (e.g. B07), `{SLUG}` and `{BR}`. You are **Connect{NN}** and you build one film. The director is session `session_01XfwPSmLbHQF2WV66wM8mt5`. Do not message the client.

## Read first, in order
1. `blender/briefs/batch2/{NN}_{SLUG}.md`: your film's beats, risky shots and reference sheet.
2. `blender/pipeline/CONNECT_BRIEF_v2.md`: how we build, the logo rules and the old-style rule. **Mandatory.**
3. `blender/LESSONS_LEARNED.md`, all of it, especially section 1 (every fault the client rejected) and section 8 (final-round faults).
4. `blender/STYLE_ANIMATED.md` (the look) and `blender/PRODUCTION_RULES.md` (the quality bar).
5. Finished examples to copy patterns from: `blender/CaveRescue_v010/` and `blender/ToucanBeak_v009/`, both built straight to the VO. The scripts are on branches `claude/connect23-cave-rescue` and `claude/connect28-toucan-beak`.

## Setup
- Blender: `/opt/blender/blender-5.2.2-linux-x64/blender`. If it's missing, run `bash blender/pipeline/setup_env.sh`.
- Rendering is CPU only, in Cycles.
- Work on branch `claude/connect{NN}-{BR}`, in folder `blender/{SLUG}_v001/`. Push only there. No pull requests.

## Phase 1: now (no VO yet)
Build everything that does not depend on exact timing:
1. **`PLAN.md`**: one row per beat, giving:
   - the shots (1–2.5 s each, hard cuts)
   - who is in each shot and what they physically do
   - the camera position
   - where the DA KRAS FILMS logo goes (1–2 places)
   - for every risky shot, the simplest safe staging (see your film brief)
2. **Sets, characters and props.** Use real models first (`pipeline/find_models.py`, Poly Haven). For MPFB humans:
   - apply the eye fix
   - open the elbow limit per character
   - relaxed hands with neutral wrists
   - clothes in non-skin colours
3. **Animate each beat's action at 1× as its own clip**, about 30% longer than you expect the beat to be, so it can be trimmed to the VO later without stretching.
4. **Cameras for every shot.** Check the first and last frame of each one: nothing in the lens, the face readable, eyes clear.
5. **Checkpoint P1:** push, then send the director one message with:
   - `PLAN.md`
   - a still sheet with one 540×960 frame per shot, Cycles 8 samples
   - anything you're unsure about

   Then **stop and wait for the VO**. Fix any director notes that arrive meanwhile.

## Phase 2: when the director sends the VO and our script
1. Run `pipeline/transcribe.py` on the VO. Beat frame = `1 + round(seconds × 60)`. `frame_end` is about 0.5 s after the last word.
2. Lay out the shots to those frames. Trim the clips; never time-stretch character animation.
3. Run the checks (`clip_scan`, `qa_check`, `limb_check`, `body_prop_cross`) on the packed file.
4. Render the full preview with `pipeline/preview.py` (every 5th frame) from the exact package, and watch every page yourself.
5. Push `blender/{SLUG}_v002/` with:
   - the .blend (under 95 MB, all textures packed)
   - the VO mp3
   - `beats.json`
   - `review/preview.mp4`
   - README.md, SETTINGS.md and CREDITS.md

   Then send the director one message.
6. **Fix rounds:** fix everything in one rebuild. Re-render only the changed ranges, splice them into the preview, and push `v002b`, `c`, …. Don't push script-only micro-tweaks. When the director says APPROVED, stop.

## Hard limits
- No full or high-resolution renders, and no paid services.
- Don't download the reference video. You have its still sheet.
- On-screen text: none, except our logo.
- Characters:
  - Generic characters only, never a real person's likeness.
  - Real victims and children: treat them respectfully, with no distress close-ups. Deaths happen off-screen or with a cut.
- Anatomy is clean and colour-coded. No gore and no blood sprays. Violence is shown as impact, not wounds.
- No weapon or explosive construction detail.
