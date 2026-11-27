# Production rules (from client feedback)

## Camera: one continuous move, never cuts
- **New angle about every 1 s, but no cuts.** The viewer should feel one camera that keeps moving: it pushes in, orbits, cranes, pulls back, drops low, rises. The *angle* changes; the shot doesn't.
- Build each shot as **one camera on a smooth spline path** through keyframed framings, one per ~1 s beat. Velocity stays continuous through every framing, so the camera never stops or snaps.
- **No camera switching** (no multiple cameras with timeline markers) for angle changes. Cut5s_v001 did this, and even with whip-pans it read as "cut, cut, cut".
- Whip-pans and fly-throughs are occasional accents inside the move, not a way to hide a camera switch.
- Change shot size gradually (medium → close → macro over the move), not by jumping wide straight to macro.
- Keep the key action (grasp, contact, drink, impact) on screen while the camera travels.

## Carried over from the motion test
- 1080×1920, 60 fps, set before animating. Cycles 48 samples / 0.05 / OIDN baseline, verified per scene.
- Planted feet locked; whole-body coordination; anticipation, weight transfer, follow-through, settle.
- Grasp visible before an object moves; no hands through props or faces (check numerically and in close-up renders).
- Continuous preview reviewed before any farm job; technical checks are not artistic approval.
- Look: textured, grounded, muted natural colour. Pacing and visual grammar: see `reference_analysis/batch01_analysis.md`.

## Quality bar (client, Nov 11): "insane", not "correct"
- **Animation must be spectacular.** Big, readable, physical acting: real weight, impacts with squash and follow-through, secondary motion (dust, debris, cloth, hair, tails, ears), reactions from everyone in frame. Never a character standing still while the narration talks.
- **Camera must be spectacular.** Still one continuous move, but bold: fast push-ins to macro, low ground-skimming dollies, crane-ups, orbits around the action, fly-throughs (through a window, between legs, over a fence), speed ramps that land on the key word. Every ~1 s the framing must change.
- **A lot happening in every beat.** Foreground, midground and background layers all alive: animals, weather, light changing, props reacting, environment detail. No empty frames, no dead air.
- **Every beat illustrates its narration line literally and on the word** (time-warp to the VO's word timestamps).
- **No full renders.** Deliver a RenderStreet-ready package plus review stills (0.2 s sheets). Never start a long local render or any paid job.

## Studio workflow (Connect chats)
- The main chat is the director. Connect1…Connect15 are production chats, one film each, on branch `claude/connectNN-<slug>`, in folder `blender/<slug>_v001/`.
- Checkpoints where a Connect chat stops and waits for director approval: **A** beat sheet + camera plan, **B** blocking stills (1 per s), **C** polish stills (0.2 s sheets) + audit, **D** farm package.
- See `pipeline/CONNECT_BRIEF.md` for the full brief every Connect chat follows.

## Detailed shapes, not blocks (client, 21:00 UTC)
> **Look update (22:45 UTC):** the films must read as **bright 3D animation, not photoreal film**. Read `blender/STYLE_ANIMATED.md`; it overrides the photo-realism wording below. Keep the detailed shapes and drop the photographic look.
- **Nothing may read as primitive geometry:** no rounded blocks, capsules, tubes, flat slabs or smooth blobs standing in for real things. That covers anatomy, organs, tissue, rock, soil, buildings, vehicles, props, clothes and water.
- **Use real assets first.** Search CC-BY or CC0 models (`pipeline/find_models.py`: skull, head sagittal section, nasal cavity, ear anatomy, liver, intestines, lungs, ribcage, muscles, cochlea, buildings, vehicles…) and Poly Haven scans. Build procedurally only when no real asset exists, and then sculpt or displace it until the shape is convincing (surfaced in the clean animated look).
- **Cutaways and cross-sections** show correctly shaped anatomy in clean, colour-coded, glossy layers (see STYLE_ANIMATED.md), never wet or gory.
- **Test:** pause any still. If a viewer could mistake it for a clay model, a toy or a diagram, it's a reject.

## Logo placement (mandatory in every film, client reminder Nov 2026)
- Every film carries the DA KRAS FILMS logo. Use the files in `blender/assets/brand/`: `DaKrasFilms_logo_dark.png` for light surfaces, `DaKrasFilms_logo_white.png` for dark ones.
- Put it on a natural surface IN the scene: a T-shirt print, a box, a shop sign, a vehicle door, a banner or a mug. Never put it as a screen overlay.
- It must read in full, sharp and unobstructed, for at least 1.5 s, at least once. Two or three placements is better when the story allows.
- No other brands, logos or readable text anywhere.
- Note the logo frames in README.md/SETTINGS.md, and check them in the preview.

## Fast to render, zero errors (mandatory for every package, client direction Nov 2026)
Render speed. Keep the look and cut the waste:
- Cycles adaptive sampling on, with noise threshold 0.03–0.05 and max samples about 64.
- Denoiser: OpenImageDenoise, with albedo and normal passes.
- Light paths: max bounces 6, diffuse 3, glossy 3, transmission 6, transparent 8–16 (raise only where a shot needs it), and caustics off.
- Turn on Persistent Data.
- Simplify: texture limit 2048 px, child particles capped, subdivision levels kept at render level 1–2.
- No volumetrics, motion-blur-heavy effects or huge hair counts unless a shot truly needs them. Fake glows with emission instead of volumes.
- Delete hidden and unused objects, materials and images before packing (`Purge`). The .blend should be under about 80 MB.
- Target under 60 s per 1080x1920 frame on the farm, and note the measured time per test frame in SETTINGS.md.

Zero-error checks. Run all of these on the EXACT file you deliver, before pushing:
1. It opens with `blender --factory-startup -b file.blend`, with no errors or warnings in the console and no missing files (`bpy.data.libraries`, missing images, missing fonts).
2. All external files are packed. Scripts must not need auto-run, and there are no driver or Python errors.
3. Scene camera set, resolution 1080x1920 at 100%, 60 fps, correct frame range, PNG output path set, and the VO strip present.
4. Render 3 test frames (start, middle, end) at full resolution from the packed file. None may be black, empty or pink (missing texture).
5. Record the results in README.md as a "Render check: PASS" block. No package goes to the client without it.
