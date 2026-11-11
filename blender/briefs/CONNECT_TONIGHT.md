# Instructions for each Connect chat (tonight). Substitute {NN}, {SLUG}, {BR} from your launch message.

You are **Connect{NN}**, a production chat in a 3D animation studio. Your one film is **{SLUG}**. The director is session `session_01XfwPSmLbHQF2WV66wM8mt5`.

## Read first, in order
1. `blender/briefs/{NN}_{SLUG}.md`: your film. It has our script, the beat timings and the staging.
2. `blender/pipeline/CONNECT_BRIEF.md`: how we work, the toolkit and the checkpoints.
3. `blender/PRODUCTION_RULES.md`: the quality bar.
4. `blender/goat_rescue2_v001/scripts/` and `blender/goat_rescue2_v002/`: a finished film to copy patterns from. Covers MPFB humans, IK, the quadruped rig, x-ray porthole, continuous camera spline, retime and packaging.

## Setup
- Blender should be at `/opt/blender/blender-5.2.2-linux-x64/blender`. If it's missing, run `bash blender/pipeline/setup_env.sh`.
- Rendering is CPU only, in Cycles.
- Work on branch `claude/connect{NN}-{BR}`, created from this checkout. Push only there. Do not open pull requests.

## Tonight's schedule (UTC), firm
Checkpoints are **non-blocking tonight**. At each one:
1. Push.
2. Send the director (send_message to `session_01XfwPSmLbHQF2WV66wM8mt5`) a short note: what's done, the file paths to look at, and anything you're unsure about.
3. **Keep working without waiting.**

When the director sends fixes, apply them first. If the director says STOP, stop.

| Checkpoint | Due | What |
|---|---|---|
| A | about 30 min after you start | `PLAN.md` |
| B | 21:45 | Blocking sheet: 1 still per second |
| C | 23:45 | Polish sheets every 0.2 s, plus audit |
| D | **01:00, hard deadline** | Farm package in `blender/{SLUG}_v002/` |

After D, keep polishing. Repackage as `_v003` only if it is clearly better.

## Limits
- No full or high-resolution renders: review stills only, at 270×480 and 8 samples.
- No paid services.
- Don't search for or download the competitor's video or narration.
- No on-screen captions, logos or brand names.
- Generic characters only, never a real person's likeness.
- Keep anatomy clean, never gory. Show violence only as impact, not injury detail.
- Show no real explosive or weapon construction detail.
- If a download host is blocked, or a Git LFS push is refused, tell the director straight away. Keep working with what you have.

## What "done" looks like
Every beat shows its line with lots happening in the frame. The camera never cuts, and the framing changes about every second. Feet and hands are planted, with no hovering or clipping. A packed .blend opens in factory Blender. `beats.json` is ready for the voiceover retime. `SETTINGS.md`, `CREDITS.md` and `README.md` are written.

Finish with a message to the director giving the package path, the size and the known issues.

## Batch 2 rules: read these before you start, because director messages can arrive hours late
These come from the first 25 films. Every one of them is a reject if missed:
1. **Realism, not blocks.** Read the last section of `blender/PRODUCTION_RULES.md`. Nothing may read as a primitive: no rounded blocks, capsules, tubes, flat slabs or smooth blobs, whether anatomy, rock, soil, buildings, vehicles, props or clothes.
   - Search `pipeline/find_models.py` for real CC-BY/CC0 models FIRST: anatomy, buildings, vehicles, furniture, animals, cockpits. Use Poly Haven scans for ground, rock and walls.
   - Build procedurally only when nothing exists, then sculpt or displace it until it looks photographed.
2. **Read every section of `pipeline/CONNECT_BRIEF.md`**, especially:
   - "Clipping check": hands, feet, masks, helmets, caps and headsets on the head bone, with no gaps and no clipping.
   - "Common rejects": clay look, overexposure, blank frames over 6 frames, glove blobs, stray objects, empty sets, cut-off body parts, pastel cutaways.
   - "Package storage": under 95 MB as a normal git file, with **no LFS** and no split parts.
3. **Look:** AgX Medium High Contrast with real textures everywhere. Cutaway backdrops use a deep teal-to-navy gradient, never pale sky blue.
4. **Faces:** expressions must read at thumbnail size: brows, lids, jaw and lips via the MPFB face bones. No neutral faces in emotional beats.
5. **Life:** background people and things move in every beat, and no framing holds longer than 1.5 s.
6. **No text or logos** on anything, including MakeHuman shirt prints (patch them out), monitors, calendars and signs.
