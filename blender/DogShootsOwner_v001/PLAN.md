# DogShootsOwner: plan (Phase 1, before the VO)

ConnectB01. Branch `claude/connectB01-dog-shoots-owner`. 1080×1920, 60 fps, Cycles CPU.
Reference: `briefs/batch2/B01_DogShootsOwner_reference_1fps.jpg` (31 s, 1 frame/s). Client direction (Nov 15): match its
shot order, subjects, framing ideas and pacing, in our current look. Hard cuts, 1–2.6 s per shot.

Phase 1 timing is provisional: each shot is animated at 1× in its own frame range, about 30% longer than the matching
stretch of the reference. In Phase 2 the shot table in `scripts/shots.py` gets the VO frames and the build script is re-run:
every shot keeps its 1× animation and is only trimmed (or extended at 1×), never stretched.

## Cast and sets
- **Owner** (MPFB, reused from WaterTubes "Hero", olive-green jumper, dark trousers, plain tan cap, no logo). The same rig is
  moved between sets at the cuts.
- **Dog**: a real Labrador model (Sketchfab CC-BY, Yury Misiyuk), golden coat, our quadruped rig. Safe poses only: standing,
  walking, one paw lift, head/ears/tail motion, lying on its side (asleep). No sitting or sphinx pose (they deformed in tests).
- **Medics** (MPFB, reused from BelugaRescue "Keeper" and MonkeyHead "Surgeon" without gown/mask, both in blue scrubs).
- Sets, each far apart in one scene:
  1. **Truck cab** (x=0): crew-cab interior with a rear bench, two front seats (real CC-BY seat model), door panels, open
     windows onto blue sky and trees.
  2. **Anatomy** (x=100): real skeleton thorax (ribs, spine, scapulae hidden) and real lungs on the sky-blue gradient. Colour-coded,
     glossy, no blood.
  3. **Ambulance interior** (x=200): white box interior, stretcher, cabinets, open rear doorway.
  4. **Forest road + clearing** (x=300): asphalt road through fir trees (Poly Haven), the ambulance (CC-BY, its text removed),
     and a grassy clearing for the last beat.
  5. **Kennel** (x=400): white dog crate (CC-BY) on a steel table against a light wall.
  6. **Hospital room** (x=500): real hospital bed (CC-BY), pale walls, window, IV stand.

## Shot table (provisional frames, 60 fps)
| # | Ref s | Ref caption (for timing only) | Shot: who, what they physically do | Camera |
|---|---|---|---|---|
| 01 | 0–1 | "The dog" | Dog stands on the rear bench, pants, tail wags, turns head to camera. Shotgun lies on the bench beside it. | Between the front seats, eye level with the dog, 35 mm, slow push-in. |
| 02 | 1–3 | "on a loaded shotgun" | Close on the front paws and the gun on the bench. The dog shifts weight, lifts its left front paw and puts it down on the gun's grip/trigger-guard area. | Low on the bench, 45 cm from the paws, f/8, slow slide toward the paw. |
| 03 | 3–4 | "of a truck" | The gun barrel lies over the bench edge, its muzzle a hand's width from the back of the driver's seat. | Low macro along the barrel toward the seat back, f/8. |
| 04 | 4–6 | "and accidentally pulled" | Muzzle flash: a bright stylised orange star, a puff of smoke, the gun jolts 2 cm. | Side close-up of muzzle and seat back, small push on the flash. |
| 05 | 6–8 | "the trigger, tore through" | Low behind the driver's seat: the man's head above the headrest. A hole bursts open in the seat back (flash, fabric flaps, foam crumbs). He jolts and turns his head; his profile shows. | Low, looking up past the seat back at his head, 28 mm. |
| 06 | 8–9 | "the front seat" | Close on the clean hole in the seat back, a wisp of smoke drifting. | Slow push to the hole, f/8. |
| 07a | 9–11 | "and into a man's back" | Anatomy: the thorax seen from behind (spine, ribs, lungs behind). A small copper bullet with a glowing trail flies in. | Wide-medium, slow orbit. |
| 07b | 11–13 | "several ribs" | It hits a rib (yellow sparks, a clean crack line glows) and passes between the next ribs. Small yellow glints mark each hit rib. | Closer on the ribs. |
| 07c | 13–15 | "and tearing a hole in his lung" | The bullet stops in the lung; a small clean red ring glows on the lung surface; the lung deflates slightly. | Push to the lung, f/8. |
| 08a | 15–16 | "He managed to call" | Driver's seat: the man, in pain, holds the phone in his right hand at chest height and taps the screen with his thumb. Screen shows a plain green call icon. | Over the steering wheel, medium close, phone below his chin. |
| 08b | 16–17 | "911" | He lifts the phone a little (still below the face), talks into it, left hand on his side. | Closer on his face, phone in frame bottom. |
| 09 | 17–18 | "and was taken" | Ambulance interior: the man sits on the stretcher; medic A checks his shoulder (hand on his upper arm), medic B walks past. | Wide from the cab end. |
| 10 | 18–19 | "where he" | Outside the open rear doorway: both medics stand at the door, the man on the stretcher behind them. | Low, centred on the doorway. |
| 11 | 19–21 | "eventually (recovered)" | The ambulance drives toward camera on the forest road, lights flashing. | Low on the road, the van passes close. |
| 12 | 21–22 | "The dog was taken" | The ambulance drives away; **logo on the rear doors**. | Behind it, low. |
| 13a | 22–23 | "to animal control" | Dog stands half out of the white crate's open door, pants, looks around. | Front of the crate, eye level. |
| 13b | 23–24 | "to animal control" | Crate door closed, the dog behind the bars looks out, tail moving. **Logo on the plate on the crate top.** | Wider, slight high angle. |
| 14a | 24–25 | "back to his owner" | Hospital bed: the man sits up (cap on), the dog lies on its side on the bed against his legs, his hand resting on its back. He smiles, eyes on the dog. | Medium from the bed's side. |
| 14b | 25–26 | "back to his owner" | Closer: his hand strokes the dog's shoulder once, the dog's tail moves, its head on his lap. | Close two-shot. |
| 15a | 26–27 | "But unfortunately" | Forest clearing: the man stands alone, hands relaxed, looks down at the grass in front of him. | Low wide behind the grass. |
| 15b | 27–29 | "this dog, a few weeks later" | The dog lies on its side in the grass, eyes closed, as if asleep. Gentle, no wound, no blood. Leaves and grass move. | Slow, respectful push; dog in the lower third, man's legs out of focus behind. |
| 15c | 29–31 | "in an unrelated…" | The man's sad face, head bowed, a slow breath; he takes the cap off and holds it at his chest. | Medium close, slow push. |
| 15d | 31+ | (end) | Wide crane-up over the clearing: the man by the sleeping dog among the firs. | Crane up, ease out. |

Provisional total: about 46 s (the VO decides).

## Logo (DA KRAS FILMS), 2 placements
1. Ambulance rear doors (white surface, dark logo), shot 12, flat-on, over 20% frame width, at least 1 s, f/8+.
2. White plate on the top of the dog crate (dark logo), shot 13b.
Never on the man, the dog, the anatomy or the forest beat.

## Risky shots and their simplest safe staging
- **Paw on the trigger (02):** no toe or finger detail. The paw lands flat on the grip/trigger-guard area, which reads as "stepped on the gun". The camera is low and close on paw + gun only; the dog's body is out of frame top.
- **Shot through the seat (04–06):** the seat is solid all the time. No x-ray seat; the hole is a cut in the solid seat back, revealed with a flash.
- **Anatomy (07):** a clean cutaway (cream bones, pink-red glossy lungs, red ring for the hole) on the sky-blue gradient, with no skin or seat around it. No blood, no gore. Sparks are yellow glints.
- **Phone (08):** phone in the right hand's fingers (grip_object, Child Of the hand bone), always below the chin. The screen shows no numbers or text, only a green call icon.
- **Medic touch (09):** one hand on the man's upper arm only, from the near side, no arm crossing his body.
- **Dog on the hospital bed (14):** the dog lies on its side on top of the blanket (no sphinx pose), his hand rests flat on its back.
- **Dog's death (15):** off-screen. We only see the dog lying peacefully, eyes closed, in grass, like sleep. No wound, no blood, no gun in this beat (the reference shows him carrying a long gun here; we leave it out unless the director wants it on his shoulder).
- **Faces:** the man's face shows on 05 (turn), 08, 09, 10, 14, 15a, 15c. Eye fix + small catchlight on every MPFB character.

## Notes for the director
- MakeHuman's asset server (files.makehumancommunity.org) returns 502 from this container, so new MPFB characters with clothes
  could not be generated. The three humans are re-dressed copies of characters from our approved films.
- The dog rig is our auto quadruped rig; it handles standing, walking, a paw lift and lying on the side cleanly. Sitting deformed,
  so shot 01 has the dog standing instead of sitting (the reference has it sitting).
