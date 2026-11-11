# GameBoxBullet_v001 — PLAN (checkpoint A)

25.0 s, 1080×1920, 60 fps, frames 1–1500. One camera `CAM_Film`, one continuous Catmull-Rom spline (position + target + lens), no cuts, no markers.
No VO yet: built to the brief's target times; `beats.json` written for `retime_to_vo.py`.

## World layout (metres)
- Bullet line: x = 0, z = 1.30, travelling +Y.
- Street + lawn: y = -32 … 0. Asphalt road at y ≈ -28, sidewalk, lawn, low hedge, mailbox post, small tree, parked covered car, neighbour houses across the street, street lamp, fire hydrant.
- House front wall: outer siding face y = 0.00, studs + insulation, drywall inner face y = 0.16. Window to the left of the hit point (curtains move in the room).
- Bedroom: y = 0.16 … 4.5. Desk + monitor (abstract glow, no text) on the left, bed, shelves with console/gamepad, posters (procedural abstract art, no text), ceiling fan, desk lamp, LED strip.
- Young man (MPFB, generic, hoodie + jeans) stands at y ≈ 3.15 facing the wall, holding the box in both hands against his chest.
- Collector's box: 0.30 W × 0.38 H × 0.14 D, front face y = 2.900, back y = 3.040 → **halfway = y 2.970**.
  Layers front→back: rigid front cover (dark embossed abstract pattern, no logo) · disc tray with 2 discs · cardboard divider · manual pages (≈20 sheets) · disc in sleeve · cardboard insert (bullet stops here, exactly halfway) · art book · back cover.

## Beat table (camera framing changes every ~1 s)
| # | t (s) / frame | Line | On screen | Camera |
|---|---|---|---|---|
| 1 | 0.0 / 1 | A stray bullet was fired toward his house | Sunny suburban street, no shooter. Bullet streaks over the lawn, heat shimmer trail (refractive ripple + faint smoke trail), grass blades bend under it, leaves blow, a bird takes off. | 0–1 s: low wide behind & above bullet, house in frame. 1–2.5 s: drops to ride 0.6 m behind the bullet, skimming grass; slight roll. |
| 2 | 2.5 / 151 | tore straight through the wall | Bullet punches the siding: splinters, paint chips, dust burst on both sides, insulation fluff, drywall puff and cone of chunks inside. | Follows bullet INTO the hole (fly-through), short whip of dust, emerges inside the room. |
| 3 | 4.0 / 241 | heading right for his chest | Bedroom revealed: monitor glow, posters, fan, floating dust in light beams, debris still flying. The man holds the box at his chest, eyes start to widen. Extreme slow motion (bullet ~0.5 m/s). | 4–5 s: camera rises and swings wide to the side to show bullet + man in one frame. 5–6.5 s: pushes along the bullet toward the box front. |
| 4 | 6.5 / 391 | But it slammed into his brand new video game collector's box set | Impact at 6.6 s: bullet nose deforms (mushroom), shockwave ring, cover dents, the man's arms/torso jolt back (follow-through), dust/foil flakes. Then a slow orbit around the box showing the man's face reacting. | Push to close; 8–11 s: half orbit around the box front at 0.6–0.9 m (man's shocked face over the box top, monitor glow behind). |
| 5 | 11.0 / 661 | The thick case cracked | Macro: cracks spider out across the dark embossed cover (animated crack mask), cover bulges. | Dives to macro 8 cm off the cover, tracks the crack front. |
| 6 | 12.5 / 751 | the discs shattered | Cutaway: box side wall fades away (x-ray cutaway); bullet ploughs through the disc tray, discs shatter into glittering iridescent shards that fan out inside. | Slides around the box edge to the side cutaway (no cut: side panel dissolves as the camera passes it). |
| 7 | 14.0 / 841 | and layer by layer they soaked up the bullet's energy | Bullet pushes through cardboard divider, manual pages (pages bend in a bow wave), next disc. Each layer it meets glows/ripples; emissive energy rings expand behind the bullet and fade; bullet slows visibly (speed curve). | Tracks alongside the bullet in the cutaway, 15–20 cm off, slight dolly forward every second; lens 50→70 mm. |
| 8 | 18.0 / 1081 | By the time it was halfway through | Side cutaway of the whole box: bullet sits exactly at mid-depth; a soft highlight sweeps along the remaining half. | Pulls back to show the whole box section + his hands on the box. |
| 9 | 20.5 / 1231 | the bullet had stopped, buried deep inside | Bullet stops dead at y = 2.970; last ring fades; small debris settles. | Close orbit 120° around the buried bullet (cutaway). |
| 10 | 22.5 / 1351 | saving his life | Side panel returns (cutaway fades out). He lowers the box in shock (hands stay gripped), looks down at the hole, pulls a small breath, then looks up at the camera. Settle. | Pull out and up to a medium: his face, the box with the hole, the wall hole behind with daylight streaming through. Slow settle drift to end. |

## Assets (all CC0 or generated here)
- Poly Haven (CC0): suburban/park HDRI 2K; textures for grass, asphalt, concrete sidewalk, wood siding/planks, plaster/drywall, wood floor, fabric; models: shrub_01, tree_small_02, street_lamp_01, fire_hydrant, covered_car, gaming_console, gamepad, ceiling_fan, desk_lamp_arm_01, potted_plant_01, cardboard_box_01 (if they load in budget).
- MPFB2 / MakeHuman (CC0): the young man (young_caucasian_male skin, short hair, casual suit, shoes).
- Built procedurally here: house walls/studs/insulation, neighbour houses, bullet (plain projectile shape only), box and its layers, discs, pages, monitor (abstract glow), posters (procedurally generated abstract art, no text), debris/shards/dust particles, energy rings.

## Trickiest shots
1. **Wall fly-through (2.5–4 s):** camera rides 0.5 m behind the bullet; the siding has a pre-cut hole that opens on contact (splinter shards animated from the hole edge); camera clip start small and the hole widened to ~25 cm so the camera passes cleanly — checked numerically in the audit (camera never inside geometry).
2. **Cutaway without a cut (12.5 s):** the box's side panel and the layer edges use a cutaway alpha driven by one keyframed value; the camera moves around the box edge while it dissolves, so it reads as an x-ray reveal, not a switch.
3. **Grasp:** box is parented to an empty; both hand IK targets are on the box sides (fingers curled around the edges), so the box and hands always move together, including the jolt and the lowering in beat 10.
4. **Shatter + energy rings:** pre-fractured disc pieces (cell-split by planes) keyed with outward velocity + spin; rings are emissive tori scaled + faded per layer contact.
5. **Slow-mo bullet speed curve:** one f-curve; fast outside, extreme slow-mo inside, decelerating to zero at the halfway point.

## Risks
- Render time on 4 CPU cores: review stills only at 270×480 / 8 spp.
- MPFB finger posing: keep the grip simple (curled fingers, thumbs over the front edge) and check in a close-up still.
