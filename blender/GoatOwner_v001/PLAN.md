# GoatOwner — PLAN (checkpoint A)

Connect32 · branch `claude/connect32-goat-owner` · 1080×1920 @ 60 fps · frames 1–2190 (36.5 s) · one camera `CAM_Film` on one continuous spline.

**Storage:** package under 95 MB as a normal git file, no LFS. This follows the launch message and the CONNECT_BRIEF "Package storage" section, which override the film brief's LFS/150 MB note.

## Set: one continuous farmyard (so the camera never needs to cut)
Here is the layout along +Y, as the camera travels:
- **Yard** (beats 1–6): dirt ground with Poly Haven scan textures and displacement. There is a broken split-rail fence (CC-BY fence model) and the tether post. A shed sits behind with an old barn/shed model.
- **Porch** (beats 7–9): a weathered farmhouse with a wooden porch and three steps, on a real model if one is found. Otherwise I'll build it from planks with Poly Haven wood textures and bevel/noise displacement.
- **Road edge** (beat 10): a livestock trailer and an official's pickup, with tape strung between fence posts.
- **Sanctuary pasture** (beat 11): green grass, sitting about 40 m beyond the farm, down a lane with trees. The camera cranes up and over the tree line to reach it, so there is no cut.

The HDRI starts as overcast, dusty farm daylight. Beat 3 is a keyed time-lapse: sun angle sweeps, autumn tint, then a cold grey tint, then back again. Beat 11 has warm golden-hour green.

## Beat table (frame = 1 + round(t × 60))
| # | t (s) | frame | Line | On screen | Camera (≈1 framing/s) |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | The owner would beat his goat with sticks | The man raises a stick over the tethered goat. The goat flinches and backs off, and the rope goes taut. His shadow falls over the goat. Dust, broken fence, a hen pecking. **No contact shown.** | Low dolly behind the fence rails → rises past them → over-shoulder of the man with the stick high |
| 2 | 3.1 | 187 | to make it aggressive… guard his property | The goat stands rigid with ears back, snorting at a passer-by walking along the fence (MPFB human). Head-down threat posture. | Orbit around the goat's head → the passer-by in the background with rack focus → back onto the goat's tense neck |
| 3 | 7.7 | 463 | this went on for a long time | Time-lapse with the goat tethered by the shed. Leaves blow, the light swings, the ground goes from dusty to wet and back. The goat's body shape key goes slightly thinner, with a subtle darkened scar patch on the coat. | Slow push along the shed wall with fast sun motion; shadows sweep |
| 4 | 10.5 | 631 | one day, the goat had enough | Macro on the eye, then lowered horns, then a hoof stamping with a dust puff. The man walks in from the background with the stick. | Push to an eye macro → tilt down to the horns → down to the hoof → the man soft in the background |
| 5 | 13.6 | 817 | charged forward and rammed its horns | Slow motion (keyed speed ramp): the goat charges and hits his midsection. He doubles over and a dust burst comes off his shirt. No blood. | Low ground-skimming track alongside the charge → orbit at impact |
| 6 | 18.8 | 1129 | Twice. | Quick second hit: he lurches back. | Whip-orbit 90° to frontal |
| 7 | 19.7 | 1183 | stumbled away… chased him onto the porch | He staggers up the porch steps clutching his stomach, the goat right behind. Hands on the rail. | Chase cam behind the goat → crane up the steps |
| 8 | 23.6 | 1417 | knocked him off | The goat butts him off the porch edge and he topples sideways. | Side profile at porch height, moving with the butt |
| 9 | 25.3 | 1519 | hit the ground hard and died within minutes | He hits the dirt with a dust burst, lies still (face down, distant), and the dust settles in the wind. | Slow pull away and up to a high wide shot; grass and dust moving |
| 10 | 28.9 | 1735 | the goat was captured | Two officials (MPFB, plain uniforms, no text) put a catch pole and rope on the goat and lead it up a trailer ramp. Tape flutters. | Descend from the high wide shot to eye level beside the trailer |
| 11 | 31.8 | 1909 | taken in by animal rescuers | Sanctuary pasture: a rescuer crouches and strokes the goat, and it eats from her hand. Other goats graze, butterflies, grass in the wind. | Crane up and over the tree line from the trailer → descend to the pasture → slow settle on the hand-feeding |

`beats.json` will carry these frames, ready for `retime_to_vo.py`.

## Assets (licences)
- **Goat:** the hendrikReyneke CC-BY goat (as in goat_rescue2), re-rigged with `pipeline/rig_quadruped.py`, with IK hooves. Extra pasture goats are instances.
- **Humans:** MPFB2 / MakeHuman CC0. The owner is a rough, unshaven middle-aged man in work clothes. There is one passer-by, two officials and one rescuer. Shirt prints get patched out.
- **Sketchfab CC-BY via Objaverse** (`find_models.py`), search running: farmhouse/porch, shed, broken fence, livestock trailer, pickup, catch pole, hen.
- **Poly Haven CC0:** dirt/brown mud, aerial grass, weathered planks, rock, a 2K HDRI (overcast farm sky plus a golden meadow), and tree models.

## Trickiest shots and the approach
1. **Abuse without contact (beat 1):** the stick only rises and holds at the top. The goat flinches *away* (keyed flinch with ears flat), and the man's cast shadow covers the goat. The camera stays behind the fence rails at the peak, so the downswing is never shown.
2. **Charge and impact (5/6):** I'll author it at real speed and slow it with a keyed time curve on all actions (slow-motion ramp). A dust particle burst at the contact point will be baked to keyed mesh instances, because farms don't take sims. The man's MPFB IK rig hinges forward at the spine. I'll check horn-to-shirt contact numerically, so there is no penetration.
3. **Off the porch (8/9):** a keyed fall arc, with the IK feet released. On landing there's a squash keyed on the root, a dust burst, then still. It is distant and face-down, with no injury detail.
4. **No cut into the sanctuary (10→11):** a crane over the tree line, with the HDRI/light blend keyed during the over-the-trees frames.
5. **Budget:** the decimated farmhouse plus 1K textures keep the pack under 95 MB.

## Checkpoints tonight (UTC)
A now · B 1 still/s sheet by 23:59 · C 0.2 s sheets + audit by 01:30 · D package `blender/GoatOwner_v002/` by 02:30.
