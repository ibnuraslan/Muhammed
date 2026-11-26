# ToddlerWell_v009: the from-scratch rebuild (batch 1, film 17)

**Status: READY TO RENDER.** My own watch passes the full moving preview, and the render check below passes. The director approved one extra round after check 2 (see `review/CHECK2.md` and `review/CHECK3.md`). Watch `review/preview.mp4` before it goes to the client.

A toddler falls down a narrow well, and a teen is lowered head-first on a rope to pull him out, in one continuous camera. Built to the client's VO (the v008 timing, `ToddlerWell_v009_VO.mp3`, 28.45 s), frames **1–1728** at 60 fps. The render sheet is `SETTINGS.md`; attribution is in `CREDITS.md`; the scripts are in `scripts/` (00 shirt texture, 01 build, 02 animate, 03 package).

## The film
- **The fall (f1–200):** the toddler walks across a field to an open well casing, steps over the rim and drops, arms and legs flailing. The camera dives with him to the bottom of the shaft, shown as a cut-away of the soil strata.
- **The loop (f200–396):** a rope loop comes down, swings above him and goes back up. He is too small to hold it.
- **The rescuer and the digger (f397–780):** a rescuer in a hard hat stands at a red tripod with a pulley. An excavator digs a parallel pit, and the wide cut-away time-lapse shows how slow that is while the sun swings to evening and back.
- **The teen (f735–1100):** a teen in a red DA KRAS FILMS shirt walks in, offers to go down, and ties the rope round his waist. The rescuer nods.
- **Head-first (f1100–1440):** he is lowered upside down with a head torch, reaches the toddler and grips his forearms.
- **Out (f1440–1728):** both are hauled up. The camera whip-tilts to the sky above the pulley, then comes down on all three cheering.

## Render check: PASS
On the exact file `ToddlerWell_v009_60fps.blend` (85 MB), opened with `blender --factory-startup -b`:
- No linked libraries, no unpacked images, and the VO sound is packed.
- No drivers, no Python texts, and no errors or warnings, apart from one Blender deprecation notice from the check script itself.
- Camera `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–1728, PNG to `//render/ToddlerWell_v009_####.png`, and the VO strip at frame 1.
- Cycles: 64 adaptive samples, noise threshold 0.03, OpenImageDenoise.
- Test frames rendered at full resolution on a 4-core CPU with no GPU: f230 in 209 s, f1040 in 139 s and f1700 in 173 s. None is black, empty or pink.
- To keep the file small, the background trees are decimated in packaging (1.77 M to 0.30 M vertices) and the tree and shrub textures are 512 px. Neither change is visible at their distance.
