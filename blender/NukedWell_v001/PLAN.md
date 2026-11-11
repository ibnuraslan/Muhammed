# NukedWell_v001: plan (checkpoint A)

36.0 s, 1080×1920 at 60 fps, frames 1–2160. There is one camera, `CAM_Film`, on a continuous spline with a new framing about every second. Our script has 95 words. The beat start frame is `1 + round(t × 60)`.

## The set: one world, one cutaway
- **Ground:** a 1 km desert plain (Poly Haven `aerial_sand` / `dry_ground_rocks` / `cracked_red_ground`) with gentle noise displacement. The surface is at z = 0.
- **Cutaway:** the ground is cut along the plane **y = 0**. Behind it (y > 0) is a 400 m × 160 m **strata face** of layered rock: sandstone, red clay, grey shale, a dark cap rock and a porous gas reservoir at the bottom.
  - The layers come from UV.y, so they bend with the rock when it deforms in beat 10.
  - The ground's underside uses a *Backfacing → transparent* shader. When the camera "dives through the skin" (goes below z = 0) and looks at the face, the 9:16 frame stacks the surface world (derrick, fire, trucks, people, sky) above the underground cross-section. That is the vertical cross-section look, with no cut and no hidden-object trick.
- **Gas well (x = 0):** a steel casing runs from the reservoir (z ≈ −110 m) to a wellhead at the surface, sitting on the cut line so it shows in section. A derrick (procedural lattice, 38 m) stands beside it.
- **Device shaft (x = −14 m):** a concrete-lined bore down to z ≈ −70 m. The device is a **plain dark-green cylinder** (1.4 m × 7 m), lifting eye on top, no internals, hanging from a cable off a lattice crane. The concrete plug fills the shaft above it.
- **Everyone and everything on the surface stands at y > 0**, behind the cut line, so nothing is ever seen floating over the open section.

## Beat table
| # | t (s) / frame | Line | On screen | Camera (one framing per ~1 s) |
|---|---|---|---|---|
| 1 | 0.0 / 1 | The massive nuclear device was lowered down the shaft | The cable pays out and the green cylinder slides down the bore past glowing lamp rings. The derrick fire burns behind, and crew and trucks line the rim. | 0.0 low macro on the device top and cable, sliding down with it → 1.0 pull back and **sink through the ground skin** → 2.0 side-on cross-section, the device in the lit shaft, strata in frame → 3.0 drift down with it. |
| 2 | 3.2 / 193 | and then concrete was poured on top | A mixer truck at the rim; its chute pours a grey stream down the shaft; the plug rises above the device with dust puffs. | 3.2 tilt and crane up the shaft following the stream → 4.2 break the surface beside the chute, the drum turning → 5.0 orbit past the truck. |
| 3 | 5.7 / 343 | You see, three years earlier, | **Rewind.** Everything plays backwards: the concrete drains up, the device rises out, the trucks reverse, people walk backwards, and the fire shrinks back into the wellhead. The sun races backwards, and the sky goes from noon to dusk to a different morning (keyed HDRI mix). | 5.7 fast crane up and back to a high wide, with a slight roll as the "rewind" whoosh → 7.0 hold wide while the time-lapse plays → 8.0 swoop down toward the bare wellhead. |
| 4 | 9.0 / 541 | a gas well had erupted into flames, | In cross-section, bright gas pulses race up the casing from the reservoir, the wellhead shakes, and a burst of flame shoots out of the top. | 9.0 dive back below the skin beside the casing, tracking the gas up → 9.8 rise with it out through the surface as it ignites. |
| 5 | 10.3 / 619 | and a fireball over 400 feet tall had been burning nonstop. | A huge roaring fire column (~120 m, volumetric fire and black smoke) with heat shimmer, the derrick beside it for scale, and a few dwarfed figures. A fast day → night → day cycle runs while it burns (sun sweep plus exposure keys), with the fire lighting the desert at night. | 10.3 tilt up the full column → 11.5 orbit and pull wide → 12.5 night falls, low skim past the derrick → 13.5 dawn, rise. |
| 6 | 14.9 / 895 | Engineers tried to put it out with water, but it did nothing. | Two fire trucks and four crew in braced stances with hands on the hoses; water arcs into the base of the fire, white steam bursts, and the flame barely flickers and roars back. | 14.9 low behind the hose crew (over the shoulder) → 15.9 along the water arc → 16.9 into the steam cloud → 17.8 out the side, wider. |
| 7 | 18.5 / 1111 | And capping it with a lid only forced the gas to escape somewhere else. | The crane lowers a heavy steel cap onto the wellhead; the flame chokes for a beat. Then the ground cracks open in radial fissures, and new gas jets and flames burst out around the site. The crew backs away. | 18.5 close on the cap descending → 19.5 contact, flame choked → 20.5 pull up and out as cracks race across the ground → 21.5 wide high, flames in a ring. |
| 8 | 23.0 / 1381 | So finally, they sent down a nuclear bomb. | Soldiers and engineers in plain 1960s olive gear guide the green cylinder on its cable into the bore. Two have hands on the casing and one signals the crane. Fissure fires burn in the background. This is the same shot as the opening, now in context. | 23.0 orbit around the hanging device → 24.0 between two soldiers' shoulders → 25.0 drop down the bore with the device, speed ramp → 26.0 through the skin into the section. |
| 9 | 26.4 / 1585 | When it detonated, | Deep in the rock, a blinding white sphere expands and the strata glow orange around it. On the surface, the ground jolts up, a dust ring blasts outward and the crew stumbles. **No mushroom cloud.** | 26.4 side-on cross-section, flash → 27.2 shake and rise to the surface, the dust ring rolling under the camera. |
| 10 | 28.0 / 1681 | the enormous blast squeezed the earth around the well, | The pressure wave pushes the layered rock inward (shape-key wave on the strata face; the layers visibly bend), and the gas casing pinches shut at the blast depth. The gas pulses stop below the pinch. | 28.0 back down beside the casing → 29.0 push in to macro on the pinch → 30.5 pull back to show the whole bent section. |
| 11 | 31.6 / 1897 | sealing the pipe shut and finally putting out the fire. | On the surface, the fire column chokes, sputters and dies to a thin smoke wisp, and the fissure flames go out. The crew at a distance raise their arms and turn to each other. The camera rises over a calm golden desert. Settle. | 31.6 rise out of the ground under the dying column → 32.6 orbit to the crew reacting → 33.6 crane up → 35 high and settled, but still drifting. |

## Assets and licences
- **Poly Haven (CC0):**
  - HDRIs: `qwantani_noon_puresky`, `qwantani_dusk_2_puresky`, `qwantani_night_puresky` (2K)
  - Textures: `aerial_sand`, `dry_ground_rocks`, `cracked_red_ground`, `red_sand`, `rock_face`, `sandstone_cracks`, `brushed_concrete`, `rusty_metal_02`, `green_metal_rust`
  - Props: military crates, jerrycans, barrels, boulders, shrubs, dead trunk, searchlight, generator, compressor, radio, cement bags, binoculars
- **MPFB2 / MakeHuman (CC0):** 6 generic characters: soldiers in olive worksuits and engineers. No insignia, no headgear (to avoid head-item clipping).
- **Vehicles (fire truck, mixer truck, crane):** CC-BY or CC0 models from Sketchfab via Objaverse if suitable ones exist (the search is running). Otherwise I'll build plain procedural 1960s trucks. There are no logos on anything.
- **Built here:** derrick, crane, device cylinder, casing, cap, fissures, fire and smoke volumes, water arcs and steam, dust ring.

## Trickiest shots and the approach
1. **Surface ↔ cross-section with no cut.** The backfacing-transparent ground, the strata face at y = 0 and underground area lights that only reach the face. The camera literally descends through z = 0.
2. **Fire column (beats 5–11).** A tapered mesh with a Principled Volume: an animated 4-D noise drives density and blackbody emission, scrolling upward, with a smoke volume above. A point and area light carry the firelight onto the set. For the night it gets an exposure key. It is kept farm-cheap: one volume object, step rate 2.
3. **Rewind (beat 3).** Every keyed object in beats 1–2 gets mirrored keys over 343–540 (time-reversed copies). Sun rotation and HDRI mix keys sell the sky shift.
4. **Rock squeeze (beat 10).** A shape key on the subdivided strata face (radial inward displacement with a falloff) and a pinch shape key on the casing, both keyed with overshoot and settle.
5. **Human contact (beats 6, 8, 11).** The anim_lib MPFB IK rig: feet planted with `Human.key_foot`, hands keyed to points on the hose and device surface, and the audit checking hand-to-prop distance.
6. **Detonation (beat 9).** An emission sphere with scale overshoot, a point light of 1e6 W falling off, an orange glow on the strata (emission mask from the distance to the blast), a ground and prop jolt with camera shake, and the dust ring as an expanding torus volume.

## Checkpoints tonight (UTC)
B blocking at 23:00, C polish and audit at 00:30, D package in `blender/NukedWell_v002/` at 01:15.
