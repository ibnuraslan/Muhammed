# BellyFat_v001 — plan (checkpoint A)

1080×1920, 60 fps, frames 1–1290 (21.5 s). One camera `CAM_Film`, one continuous spline move. Frame = 1 + 60·t.

## Core trick: one physical world, two scales
The cross-section set ("MACRO") is built in macro units and parented to an empty **at the impact point on her belly, scaled 0.025** (bullet ≈ 0.6 macro units = 1.5 cm real). The same bullet object flies through the supermarket at real scale and then through the tissue layers, so **the camera path is truly continuous in world space**: it zooms exponentially from metres down to millimetres (clip start animated).
- The macro set's top layer is a shirt-fabric patch that coincides with the real shirt. While the frame is filled with fabric (≈2.55 s, and again ≈20.4 s), the woman/store and the macro set + cyan studio dome swap render visibility. No cut and no camera switch: the move tilts over the fabric edge and reveals that it is the top of a cross-section block.
- Inside: clean explainer look. Soft cyan → white gradient dome, studio key/rim/fill area lights, realistic anatomy, no blood.

## Beat table
| # | t (s) | frame | Line | On screen | Camera (one framing ≈ 1 s) |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | A stray bullet struck her | Bright supermarket aisle, shelves of unbranded products, flickering tubes, a shopper with a cart in the background, a stocker on a ladder. Plus-size woman (MPFB, generic) with a basket reaches to a shelf. A bullet streaks in from off-screen right, in slow motion, with a heat-shimmer trail and dust motes stirring. | 0.0 low dolly down the aisle, woman mid-ground → 0.6 whip right onto the bullet as it enters → 1.0–2.0 ride alongside the bullet, 40 cm off it, her belly growing behind it |
| 2 | 2.0 | 121 | right in the stomach | Impact on her shirt: fabric ripple ring, her torso jolts, the basket swings, a can falls off the shelf. | 2.0 macro side-on of tip touching fabric → 2.3 swing to face the hole and dive → 2.55 frame filled with fabric (scale swap) → 2.8 tilt over the block edge: it is a cross-section |
| 3 | 3.0 | 181 | It pierced her skin, but started to slow down… | Layer stack: fabric, skin (dermis texture), thick yellow fat lobules, red muscle, glistening intestines. Skin dimples, then parts cleanly around the tip; the bullet enters the fat and decelerates (speed curve eases). | 3.0 side medium of the cut face → 4.0 low angle along the face → 5.0 push in to the tip → 6.0 slide back wider (all layers) → 7.0 rise to a high three-quarter |
| 4 | 7.8 | 469 | Layer by layer… like a cushion | Fat lobules squash away from the bullet and ripple outward in waves; translucent energy rings bloom behind the bullet and fade, each smaller than the last. | 8 tracking alongside → 9 behind 3/4 to see the rings → 10 front 3/4 looking back at the bullet → 11 macro on lobules squashing → 12 pull back |
| 5 | 12.6 | 757 | And by the time it reached deeper tissue | Red striated muscle ahead; the bullet barely creeps, the last weak ring. | 13 macro on the tip against the muscle → 14 drop low under the bullet |
| 6 | 14.8 | 889 | the bullet had lost most of its force, coming to a stop before it hit any organs | It stops just short of the intestines, which glisten and slide gently (peristalsis). | 15–19.5 orbit 300° around the stopped bullet, pushing in and out once |
| 7 | 20.1 | 1207 | saving her life | Pull up through the layers to the fabric (swap back) and out: she is alive and shocked, hand pressed to her side, basket dropped, the background shopper turning. Settle. | 20.1 fast rise to the fabric → 20.5 pull out from the shirt → 21.0 medium on her face and hand → 21.5 settle |

## Assets (all free)
| Asset | Source | Licence |
|---|---|---|
| Woman, background shoppers | MPFB2 + MakeHuman system assets (bodies, `female_casualsuit` clothes, skins, hair) | CC0 |
| Floor/wall textures, HDRI | Poly Haven (tiles, painted plaster, fabric) | CC0 |
| Shelves, products (boxes, cans, bottles), cart, ladder | Built procedurally in Python, plain colour labels, no text | ours |
| Tissue layers, lobules, muscle fibres, intestines, energy rings | Procedural in Python | ours |
| Bullet | Simple procedural copper-jacket slug, no cartridge or firearm | ours |
If a Sketchfab/Objaverse model (shopping cart) is clearly better, I'll add it with its CC-BY credit.

## Tricky shots and how
1. **Shirt → cross-section without a cut:** the scale-0.025 macro set at the impact point plus a visibility swap while fabric fills the frame (see above). The audit checks that camera speed has no jump at the swap frames.
2. **Fat compressing and rippling:** about 300 lobule meshes. Each one is keyed every 2 frames from a function of distance to the bullet tip (radial squash plus an outward travelling damped wave). Energy rings are emissive tori keyed for scale and alpha.
3. **Bullet deceleration:** one position curve, piecewise ease-out per layer: fast through skin, slowing through fat, creeping in muscle, 0 at 15.5 s.
4. **Woman acting:** MPFB IK rig (anim_lib `Human`) with feet planted throughout. Beats: reach, impact jolt with follow-through, then a hand on her side, a hunched shocked face and breathing. She is visible again only in beat 7, so the shock pose is set by then.
5. **Never gory:** no blood spray. A small dark scorch hole on the shirt, and a clean channel through the tissue.
