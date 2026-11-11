# LegoInNose_v002: farm package

This is the full 38.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `LegoInNose_v002_60fps.blend`: the self-contained scene, with every texture packed inside (47 MB). It's a normal git file, with no LFS.
- `beats.json`: start frame and first words for each of the 11 beats (target timing). Use it with `blender/pipeline/retime_to_vo.py` once the voiceover exists.
- `SETTINGS.md`: render settings and suggested test frames.
- `CREDITS.md`: the CC-BY credit block for the video description (one model: the sleeping cat), plus provenance for the CC0 assets.
- The textures were slimmed before packing by `../LegoInNose_v001/scripts/slim_textures.py`, then packed by `pipeline/package_for_farm.py`.
- `package_check_lowres.jpg`: a low-res, low-sample frame rendered from the packed file opened with `--factory-startup`. It shows the package works; it is not a quality reference.

**No voiceover yet.** The film is built to the target beat times in `../briefs/03_LegoInNose.md`. When the VO mp3 arrives:
1. Run `python3 -I blender/pipeline/transcribe.py` on it.
2. Write an anchors file from `beats.json` (old frame → the second the first words are spoken).
3. Run `retime_to_vo.py`. It warps every keyframe and adds the VO strip.

The tunnel visibility windows and the teleports are keyframes too, so they warp along with everything else.

## Source and build order
The source is `../LegoInNose_v001/scripts`:
1. `01_build_humans.py` (MPFB2)
2. `02_build_sets.py <assets_dir>`
3. `03_animate.py`, which also runs `03b_props_fx_camera.py`
4. `audit.py`
5. `campath.py`

Assets come from Poly Haven (fetched with `pipeline/fetch_polyhaven.py`) and one Objaverse model (`pipeline/find_models.py`). See CREDITS.md.

## How the single camera works
There is one camera, `CAM_Film`, on a Catmull-Rom path through about 74 framing keys. It never cuts.

- **The cross-section studio** is a cyan-to-white gradient sphere 7 m below the living-room floor. The camera reaches it physically, by flying into the boy's nostril and down an organic tube. There are two dives and two returns: 12.0–12.6 s, 14.1–14.5 s, 18.3–18.9 s and 21.7–22.2 s.
- **Inside a tube**, the room, props and people are switched off for the camera only (`visible_camera` keys), so the floor slab and the boy's skin don't cut across the tunnel. Lighting and shadows are unchanged.
- **The bedroom→bathroom pass** at 31.2–31.5 s goes through the wall. The two wall pieces are hidden from the camera for those frames only.
- **Character swaps** use the Boy, Teen and Man rigs. The time-lapse swaps sit inside three short exposure flashes (23.2, 24.0 and 24.5 s). Moving the Man from the bench to the bed (28.7 s) and from the bed to the shower (31.2 s) happens while the old spot is out of frame.

## Known issues
- **Mom's walk-in (14.6–15.8 s):** the audit flags 5–9 cm foot heights. These are swing-phase lifts of a fast walk, not hovering plants. Her kneel is approximate, with knees near the rug but not measured.
- **31.1 s:** the Man in bed is cut off at the left edge of frame for about 4 frames before he is moved to the shower.
- **Facial acting** uses MakeHuman expression shape keys (smile, open mouth, brows, squint, nostril flare) plus jaw, head and body. The eyebrows and eyelashes don't follow the brow shapes exactly.
- **Cross-section anatomy** is a clean explainer illustration on the real cut head (skin, cut surface, skull, brain, airway, turbinates, palate, tongue, spine), not a medical-grade model.
- **Shower modesty:** the glass is frosted up to 1.42 m, so everything below the chest is a blurred silhouette from every camera angle. The shoulders and chest are visible through the clear upper glass.
- **Hair at review samples (8)** looks speckled. At the farm's 48 samples it resolves.
- **Brick in the palm (35.6–38.5 s):** the brick follows the palm centre within 2.5 cm and rests on the palm; it isn't gripped.
