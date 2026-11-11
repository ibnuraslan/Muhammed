# LegoInNose_v004: farm package

This is the full 38.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `LegoInNose_v004_60fps.blend`: the self-contained scene, with every texture packed inside (56 MB). It's a normal git file, with no LFS.
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

## What changed since v002 (director's notes on C)
- **Cross-sections use real anatomy, not drawn shapes.**
  - A scanned human skull (CC-BY) and a CT-style nasal-cavity/sinus cast (CC-BY) are fitted into the boy's head and cut on the same sagittal plane. Cut faces are shaded as cut bone and as the cavity interior.
  - The brain and tongue are displaced solids with gyri and papillae, not flat slabs.
  - Materials: wet mucosa (SSS and a clear coat), porous bone, fibrous cut muscle.
  - The backdrop is darker teal-to-navy and the studio light is lower-key.
  - The bricks sit inside the nasal cavity. The hidden yellow one glows softly.
- **Tunnel entries:**
  - Nostril-hair strands and wet, veined mucosa.
  - Each tunnel pass is about 0.4 s. At most about 3 flat frames appear where the camera crosses skin or the studio wall.
- **26-year time-lapse:**
  - The boy plays with bricks.
  - Then the teen (about 15, taller, long-sleeve sweatshirt) is hunched over a gamepad, and the toys are gone.
  - Then the man (33) scrolls a phone.
  - Meanwhile the seasons and the sun change through the window, and the camera keeps orbiting toward his face.
- **Shower:** the elbow poles were mirrored, which hid the upper arms. The arms are now connected in every frame, and the idle hand rests at his side.
- **Contacts:** the boy's support hand no longer sinks into the rug, and the man's hands in bed stay on the mattress. The audit's new penetration count is 0.

## v004: the animated look (client change, Nov 11 22:45 UTC)
This is v003 restyled per `blender/STYLE_ANIMATED.md`. Animation, geometry and timing are unchanged.

`pipeline/anim_look.py --no-sky` applied:
- AgX Punchy
- saturation ×1.25
- bump and normal strength ×0.35
- roughness at least 0.35
- motion blur off
- volumes ×0.5
- lights ×1.25

`--no-sky` keeps the seasons visible through the window.

`../LegoInNose_v001/scripts/anim_fix.py` then re-applied the keyed values the tool can't change, and fixed the look by hand:
- **Keyed light energy:** ×1.25. The moonlit bedroom is brighter, with the lamp at 25 W.
- **Keyed world strength:** ×1.4.
- **Exposure:** +0.25 overall.
- **Focus:** f-stop at least 5.6 everywhere.
- **Cross-section studio:** a bright sky-blue gradient (cyan top to near-white bottom) on a light floor.
- **Anatomy:** clean and colour-coded: cream bone (the same scanned skull shapes), glossy pink mucosa on the sinus-cast shapes, pink brain, red-pink cut muscle. There's no wet or medical-photo shading.
- **Tunnel:** clean glossy pink with soft veins.

v003, the approved photoreal version, is kept as it was.

## Source and build order
The source is `../LegoInNose_v001/scripts`:
1. `01_build_humans.py` (MPFB2)
2. `02_build_sets.py <assets_dir>`
3. `03_animate.py`, which also runs `03b_props_fx_camera.py`
   - for v004, then run `pipeline/anim_look.py --no-sky` and then `anim_fix.py`
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
- **Cross-section anatomy:** the skull is an adult scan scaled into a 7-year-old head. The brain and tongue are procedural. It's realistic, but not a medical-grade child model.
- **Hair at review samples (8)** looks speckled. At the farm's 48 samples it resolves.
- **Shower modesty** relies on frosted glass (up to 1.42 m) and framing. There are no swim shorts, because MakeHuman has no shorts asset; nothing below the chest is ever seen sharply.
- **Brick in the palm (35.6–38.5 s):** the brick follows the palm centre within 2.5 cm and rests on the palm; it isn't gripped.
