# TitanicIceberg — PLAN (Checkpoint A)

Connect35 · branch `claude/connect35-titanic-iceberg` · 1080×1920 @ 60 fps · frame_end 1830 (30.5 s) · Cycles CPU · AgX Medium High Contrast.

## World layout (one continuous camera, no cuts)
All sets live in one scene, placed so one spline camera can travel between them:
- **Ocean set** (origin): Ocean-modifier sea (displaced, foam attribute), 2K Poly Haven sky HDRI dimmed for dawn, volumetric low fog, the hero iceberg (~60 m wide), the steamship deck section (planks, rail, funnel and rigging in BG), floating debris field 150 m downwind.
- **Darkroom** (x = +400 m, sealed box, red safelight): sits "inside" the photo: the camera enters it by diving into the red smear (macro ice crystals ≤6 frames) and emerging from the developer liquid surface.
- **Office** (behind the darkroom wall, through a door): reached with a lateral fly-through of the open doorway.
- **Explainer stage** (deep teal→navy gradient, no pale sky): entered by pushing through the print under the magnifying glass.
- **Return to ocean**: pull back out of the explainer "photo" plane, which is matched to the real iceberg view, and into the fog orbit.

## Beat table (frames @60)
| # | t (s) | frame | Line | On screen | Camera (one framing ≈ 1 s) |
|---|---|---|---|---|---|
| 1 | 0.0 | 0 | He took a photo of an iceberg | Dawn, North Atlantic, April 1912. A steward in a dark brass-buttoned uniform and cap at the rail raises a wooden bellows camera; deckhands coil rope in BG, smoke from the funnel, gulls, swell, mist rolling on the berg. | 0.0 low over the deck boards past his shoes → 1.0 rises over his shoulder, camera and hands sharp, berg soft behind. |
| 2 | 2.0 | 120 | the exact one that sank the Titanic | The berg fills the frame. A translucent cold-blue ghost of a four-funnel liner (no name or text) glides past it at night, with ghost lit portholes and smoke. | 2.0 rack focus from the camera lens to the berg → 3.0 slow push out over the rail → 4.0 the push continues, tracking the ghost liner bow to stern → 5.0 drifts toward the waterline. |
| 3 | 5.8 | 348 | streaked with red, with one big smear | Macro along the ice: a dark oxide-red smear and streaks at the waterline height, wet crystals, meltwater drips, chunks bobbing, waves slapping. | 5.8 skim the waterline → 7.0 slide along the streak → 8.0 crab past ice crystals (macro DOF) → 9.0 tilt up the smear → 10.0 ease back. |
| 4 | 10.2 | 612 | his ship was near where the Titanic had gone down | An aerial pull-up: a dark swell with a debris field (deck chairs, planks, a lifebelt with no text, crates) drifting; the steamship cuts in with a bow wave and smoke. | 10.2 rise vertical off the water → 11.2 crane up and tilt down over the debris → 12.2 → 13.2 arc toward the steamship → 14.2 orbit to the berg. |
| 5 | 15.2 | 912 | most likely the same iceberg | Ghost replay at night: sky to moonlit night, ghost liner scrapes along the berg, sparks and ice blocks falling onto the deck and into the sea, and red paint transferring (animated mask) to the ice. | 15.2 swing low alongside the hull → 16.2 race along the scrape → 17.2 push into the fresh red smear (the transition dive). |
| 6 | 18.2 | 1092 | When the film was developed | A darkroom with a red safelight. A technician's hand with tongs rocks a print in the tray; the iceberg image (a real render of beat 1) fades in; drying prints on a line; dripping. | 18.2 emerge from the liquid surface → 19.0 pull up and back across the trays. |
| 7 | 20.0 | 1200 | experts studied the image carefully | A 1912 office: wood desk, green lamp, two experts (MPFB, period suits) leaning in, one holding a brass magnifier over the print, the other pointing; a clock pendulum and smoke from a pipe in BG. | 20.0 fly through the doorway → 21.0 orbit over shoulders → 22.0 push down through the magnifier lens. |
| 8 | 22.3 | 1338 | red streaks lined up with the height of the hull | Explainer on a deep teal→navy gradient: the photo of the berg floats as a big print; a ghost liner hull slides in beside it; the dark-red hull band glows and a horizontal line sweeps to match the streak. | 22.3 emerge in front of the print → 23.3 dolly across as the hull slides in → 24.3 push to the matching band → 25.0 pull back. |
| 9 | 25.5 | 1530 | many believe this was the iceberg | Final: the berg alone in fog, slowly drifting and rotating; gulls; meltwater; swell. | 25.5 pull back out of the print into the real fog → 26.5 → 30.5 slow orbit, settle. |

`beats.json` is written from this table: frames 0, 120, 348, 612, 912, 1092, 1200, 1338, 1530.

## Assets (licences)
- **Humans:** MPFB2 / MakeHuman system assets (CC0): the steward, two deckhands, the darkroom tech and two experts. Shirt prints are patched out. Expressions use the face bones.
- **Sketchfab via `find_models.py` (CC-BY / CC0, credited in CREDITS.md):** the four-funnel liner (ghosted, so nothing names it), deck chair, bellows camera, magnifying glass, desk/lamp, crates, and an iceberg if one is good enough. Search running now.
- **Poly Haven (CC0):** dawn/overcast sky HDRI (2K), wood plank deck texture, painted metal, plaster wall, wood floor, snow/ice texture for the berg base colour and normals.
- **Procedural:** the ocean (Ocean modifier plus a physically based water shader), and the iceberg if no model is good enough. That means a heavily displaced voronoi/musgrave sculpt with ice SSS, crevasses and a wet band. No smooth blobs.

## Tricky shots and how
1. **Ghost liner (beats 2, 5, 8):** a real liner model with a fresnel-emissive translucent cold-blue shader plus faint volume. The hull red band is a separate material slot (or a z-gradient mask) so it can glow in beat 8.
2. **Red smear transfer (beat 5):** the berg material mixes in a red paint layer through an animated mask (empty-driven gradient along the scrape path × noise). The same mask stays on for beats 3 and 9. Sparks come from a particle emitter at the contact point; falling ice comes from rigid-body chunks baked, or keyframed chunks.
3. **Transitions:** smear → darkroom liquid, and magnifier → explainer. Each is at most 6 frames of macro-detailed surface with a match-move, so there are no blank frames.
4. **Photo print:** the image is a low-res render of the beat 1 composition, loaded as a texture with a developer-reveal mix animated 0→1.
5. **Steward with camera:** IK hands on the camera body, and the camera parented to a hand bone after the grab. Feet planted on the deck with an audit check.
6. **Size:** 1K textures (2K for the berg and hero deck), 2K HDRI, decimated liner and debris. Packed under **95 MB**, normal git, no LFS (the Batch 2 rule overrides the film brief's "LFS / 150 MB").

## Risks
- 4 CPU cores, so review stills are 270×480 at 8 samples only. The ocean is kept at a modest resolution.
- If the Sketchfab liner isn't usable, I'll build a hull from modelled sections, with the ghost shader hiding the fine detail.
