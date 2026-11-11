# RooseveltSpeech_v001: plan (checkpoint A)

Connect24 · branch `claude/connect24-roosevelt-speech` · 1080×1920 · 60 fps · frames 1–1500 (25.0 s) · Cycles CPU.

## Beat table (start frame = 1 + round(t × 60))

| # | t (s) | frame | Line | On screen | Camera (one framing per ~1 s, one spline) |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | The bullet hit him in what should have been a deadly spot, but | Night street, 1912: hotel façade with lit windows, gas street lamps, wet cobbles, open touring car with glowing headlamps. Crowd (~30 people, hats, coats) packed around the car, waving. Stout man (dark overcoat, moustache, round spectacles, generic face) stands in the car waving his hat. A silhouette in the crowd raises an arm, muzzle flash (light + flash card, no gun detail). Slow-mo bullet with heat-shimmer trail crosses the frame into his right chest. He jolts back, hat hand drops. | 0.0 high wide over the crowd, pushing in → 1.0 low between heads toward the shooter's flash → 2.0 whip along the bullet's path (follow cam, speed ramp) → 2.8 lands medium on his chest at impact |
| 2 | 3.1 | 187 | somehow, he stayed on his feet | He sways back, one foot slides back half a step and plants (IK-locked), grabs the car's seat-back rail with his left hand, straightens up. Crowd recoils: hands to mouths, people turning, a hat falls, aides grab for the shooter in the background. | 3.1 low angle on his feet planting on the car floor → 4.1 tilt/crane up his body → 5.0 medium-close on his face as he straightens |
| 3 | 5.6 | 337 | So how was that possible? | Freeze-frame feel: time ramps to ~3% speed. Crowd hangs mid-gasp, dropping hat hangs in the air, dust/rain motes suspended. Small hole and dark spot on the coat's right breast. | 5.6 slow orbit 90° around him at chest height → 6.6 drifting toward the coat breast, framing the hole |
| 4 | 7.4 | 445 | Well, Roosevelt had a thick, folded-up speech in his coat pocket, | Camera dives into the hole. X-ray porthole: coat and body fade to a ghost inside a soft sphere; a cyan-to-white studio gradient dome fades in around the chest. Real-scale breast pocket revealed: a thick folded paper manuscript (≈50 sheets, folded once, illegible pencil-grey line marks, no readable text). Slow rotate. | 7.4 push through the fabric → 8.4 macro on the pocket outline → 9.4 orbit the manuscript → 10.4 rise over its fold edge → 11.4 slide toward its side |
| 5 | 12.0 | 721 | along with a metal glasses case. | Beside the manuscript, a brushed-steel spectacle case (rounded hinge box) slides into highlight (rim light sweeps). | 12.0 lateral dolly from paper to case → 13.0 low over the case's hinge |
| 6 | 14.6 | 877 | The bullet tore through both, which slowed it down and | Slow-motion: the bullet enters the manuscript; sheets ripple and tear (stack of 50 separate sheets, each pushed and frayed in sequence), paper flecks spray, bullet visibly decelerates, then hits the steel case and dents it (shape key), spinning slightly. | 14.6 tracking alongside the bullet → 15.6 rack/push to the dent |
| 7 | 16.7 | 1003 | kept it from reaching his lungs. | Camera passes behind the case: ghosted ribs and pink lungs (clean anatomy, glossy), gently breathing. The bullet comes to rest in a red-tinted patch of chest muscle a few cm short of the lung; a soft glow ring marks the gap. | 16.7 slide down past the ribs → 17.7 orbit to side view showing bullet/lung gap → 18.7 begin pull-back |
| 8 | 19.8 | 1189 | And despite the wound, | Pull out of the chest: the gradient dome fades and the world returns, but we are now in an auditorium (set swapped while hidden by the dome). He stands at a wooden podium on a stage, lifts the bullet-holed manuscript high in his right hand (visible grasp), audience leans forward. | 19.8 fast pull-back out of the pocket → 20.8 medium-wide over the podium |
| 9 | 21.4 | 1285 | he insisted on finishing his 90-minute speech. | He speaks with big gestures, left fist raised; packed hall (balcony + floor seats) cheers, hats wave, flags and red-white-blue bunting sway, a wall clock's hands spin round (time passing), lights warm. | 21.4 orbit behind him to see the audience → 22.4 rising → 23.4 crane up high over the hall → 24.4 settle |

`beats.json` will hold these frames for the VO retime.

## Continuity trick for the one camera
- The street and the hall share the same origin: the stage floor height equals the car floor height, and the hero stands on the same spot.
- During beats 4–7 the cyan dome surrounds the chest and hides the outer world. Inside the dome, `hide_render` swaps street → hall, and the hero's pose changes while the camera is in macro on the paper. The camera never cuts or switches.
- Time ramp in beats 3–7: secondary motion (crowd, motes, flags) keyed at ~3% speed, so the world is "frozen" but still alive.

## Assets and licences
- **Hero + crowd:** MPFB2 / MakeHuman system assets (CC0).
  - Hero: heavy male, about 50, `male_elegantsuit01` tinted as the dark overcoat, `shoes02`.
  - Moustache, round wire spectacles and hat are procedural meshes, parented with Child Of to the head and hand bones.
  - Crowd: 5–6 MPFB variants (subdiv 0) duplicated to about 30 armatures, each with its own offset action. Fedoras from `fedora01`.
- **Textures and HDRI:** Poly Haven (CC0): cobblestone, brick/plaster façade, wood planks for the stage and podium, fabric, brushed metal, and a night HDRI.
- **Car, ribcage, lungs, podium, clock, street lamp:** Sketchfab models mirrored in Objaverse, CC-BY or CC0 only (search running now; credits go in `CREDITS.md`).
  - If no good match turns up, I build it procedurally:
    - touring car from lathe and box parts, with emissive headlamps
    - ribs from curve tubes
    - lungs from a remeshed metaball sculpt
- **Paper stack, glasses case, bullet, flags, bunting, wall clock:** procedural.
- No text, logos or brands anywhere. The flags are plain stripes and bunting with no emblem.

## Trickiest shots and how
1. **The bullet hit and slow-mo in a crowd (beat 1).**
   - The bullet is a small lathe mesh with an emissive streak and a refraction "shimmer" trail.
   - The follow-cam rides a spline parallel to the bullet path, speed-ramped so impact lands at about 2.8 s.
   - The muzzle flash is a 2-frame emissive card plus a point light on a silhouette figure (black shader). It shows no weapon detail.
2. **Dive into the coat (beat 3→4).**
   - The goat_rescue x-ray porthole shader runs on every hero material. It fades the body to a transparent cyan ghost within a radius around a chest empty.
   - A 0.6 m inverted gradient sphere fades in around the chest, so the camera stays physically continuous and real-scale.
3. **Bullet through 50 sheets (beat 6).**
   - 50 separate thin sheet meshes, each with a simple-deform plus shape-key bulge and a torn hole (boolean pre-baked), triggered sequentially as the bullet passes.
   - Paper-fleck particles.
   - The bullet speed curve decelerates. A dent shape key on the steel case.
4. **Anatomy (beat 7).**
   - Clean glossy ribs and lungs on the cyan gradient, the explainer look.
   - The lungs breathe slowly (scale key). The bullet rests a few cm in front of them.
   - No blood, only a dark red tint on the muscle around the bullet.
5. **Hall reveal and crowd (beats 8–9).**
   - Instanced MPFB crowd with offset cheer/clap actions on seats and in a balcony.
   - The hero has IK feet locked on the stage. The right hand grips the manuscript (Child Of to the hand bone after the grasp frame). The left fist is raised.
   - The clock hands spin on a driver. The camera cranes up and settles.
6. **Contacts.**
   - IK feet locked on the car floor and the stage. The left hand grips the seat rail in beat 2.
   - The hat is in the right hand in beat 1 and drops in beat 2. The hand grasps the manuscript in beat 8.
   - Spectacles and moustache are Child Of the head bone with a small offset.
   - The audit checks hand, foot and head-item BVH overlap, hover and sink, and that the camera stays out of geometry. Plus a 270×480 close-up pass on every contact.

## Schedule (UTC)
- **A:** this plan, about 19:55.
- **B:** blocking sheet at 1 still per second, 23:15.
- **C:** 0.2 s sheets plus audit, 00:45.
- **D:** package in `blender/RooseveltSpeech_v002/`, 01:30.
