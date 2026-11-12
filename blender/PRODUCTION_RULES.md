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
