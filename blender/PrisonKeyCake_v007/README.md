# PrisonKeyCake_v007: farm package

**v007: hands pass (client, 23:00 UTC).** v007 is v004 with only the hands changed.
- Limit Rotation constraints (local space) on every finger, thumb and wrist of every rig: 768 constraints.
  - fingers: 0° to 90° forward only, ±10° spread
  - thumb: a natural cone
  - wrist: ±60° flex, ±25° side
  - Elbows are kept natural by the IK pole targets.
- Relaxed default hands: finger curl is at least 22° (thumb 14°) on all IK characters. The president and crowd rigs get a relaxed curl too.
- Hand audit (`../PrisonKeyCake_v001/scripts/audit_hands.py`, BVH every 2 frames: hand vs hand, hand vs own torso and head, hand vs other characters):
  - Before the pass it flagged **675 frames**; now it flags **8**. See `../PrisonKeyCake_v001/audit/hands_v007.txt`.
  - The 8 remaining frames are intended contacts:
    - the key slipped into his shirt pocket (1165)
    - the tin passing his chest on the way up to the window (1193–1195)
    - the knife hand brushing his belly while he cuts (1341)
    - both hands meeting at the cut cake (1353)
    - the forearm brushing his chest while he slaps the wall (985, 1001)
- Re-keyed fixes:
  - the sleeping guard's hands rest apart on his thighs instead of overlapping
  - the hands on the stool are wider
  - the box hand-off: the guard grips the near face from below, and only once the box reaches him
  - the slap hand is on the wall beside his head, not through it
  - he leans less while cutting the cake
  - the key is held slightly away from his chest
  - the key-press fingertips rest on the key and wax, not hovering
- Close-up check of the hand actions (270×480): key at the chest, key press, key into the cake, box grip, key in the lock, tin at the window, knife, key out of the cake.
- Review sheet (1 still per second): `../PrisonKeyCake_v001/stills/hands_v007_1s.jpg`.

**Unchanged from v004: animated look (client direction, 22:45 UTC).** v004 is v003 with the look changed from film-real to bright, clean 3D animation. Animation, geometry and camera path are unchanged.
- `pipeline/anim_look.py`:
  - AgX Punchy
  - sky-gradient world for camera rays (dims to a readable blue at night)
  - saturation ×1.25, bump ×0.35, roughness at least 0.35
  - motion blur off
- `PrisonKeyCake_v001/scripts/06_animlook_fix.py` covers the keyframed values the tool can't reach:
  - camera f-stop clamped to at least 5.6 (at least 4 on macro lenses)
  - keyed light energies raised
  - exposure: day 0.55, night 0.9, final day 0.25
- The prison is bright and clean:
  - soft bounce lights in the cell, corridor and foundry
  - a cool night fill on his face
  - lighter, cleaner brick and stone with less bump
  - no dust haze
- Review sheet (1 still per second): `../PrisonKeyCake_v001/stills/animated_v004_1s.jpg`.

This is the full 31.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `PrisonKeyCake_v007_60fps.blend`: the self-contained scene, 67 MB. Every texture is packed inside, and it is committed as a normal git file.
- `beats.json`: the start frame of each of the 10 beats, built to the brief's target times. When the VO arrives, the director retimes with `pipeline/retime_to_vo.py`.
- `SETTINGS.md`: render settings and suggested test frames. `CREDITS.md`: the CC-BY credit block for the video description (key, lock, cake, government building, crucible) plus CC0 provenance.
- `package_check_f200_lowres.jpg`, `package_check_f1350_lowres.jpg` and `package_check_f1860_lowres.jpg`: 270×480, 8-sample frames rendered from this packed file in factory-startup Blender. They show the package works; they are not a quality reference.

The source is `../PrisonKeyCake_v001/scripts`. Build order:
1. 01_build_humans
2. 02_build_scene (which runs 02b_costume and 02c_cake)
3. 03_animate (which runs 03b_life and 03c_details)
4. 04_camera
5. 05_optimize together with `pipeline/package_for_farm.py`

The audits are in `../PrisonKeyCake_v001/audit/`, and the review sheets are in `../PrisonKeyCake_v001/stills/`.

## Story beats (target times)
| # | Frame | s | Line starts | On screen |
|---|---|---|---|---|
| 1 | 1 | 0.0 | He got hold of the prison's master key… | Candle-lit cell; he glances at the door; a macro shows the key in his fingers; his fingertips press it into a tin of wax |
| 2 | 259 | 4.3 | making a perfect impression | Macro: the key lifts and leaves a key-shaped imprint; the camera rises through the window bars |
| 3 | 367 | 6.1 | The mold was smuggled out… | A visitor slips the tin into his coat pocket and crosses the yard, past exercising prisoners and a guard who waves him through the gate |
| 4 | 511 | 8.5 | and his allies used it to cast a metal copy | Through the gate tunnel into a foundry: crucible pour, sparks, smoke, and the mould opens on a glowing key |
| 5 | 685 | 11.4 | They hid the key inside a cake… | The key is pushed into a cake, which goes into a box; the box is handed to the guard, then a whip-pan back through the tunnel |
| 6 | 871 | 14.5 | But when he tried the key, it didn't fit | Night: lock macro of the key scraping in and jamming; his face as a guard's lantern passes under the door; he strains, slaps the door, and rests his forehead on it |
| 7 | 1057 | 17.6 | So he sent out another wax impression… | Second press; he leans over the table and passes the tin out of the window; he waits on the stool while the candle burns down and the moonlight moves |
| 8 | 1303 | 21.7 | And this time, the key worked | A dark iced fruit cake gets two cuts; the slice comes out, crumbs scatter, and he pulls the key from the cut; lock macro of the 90° turn as the bolt slides; relief on his face |
| 9 | 1429 | 23.8 | He passed through every locked gate… | The door swings; three double gates open one after another past a sleeping guard; he walks out into the night yard past a lantern patrol |
| 10 | 1681 | 28.0 | Years later, he became president of Ireland | Crane over the wall into warm daylight: an older him, generic, with grey hair, glasses and a dark suit, waves from government steps; big tricolour flags in the wind, a cheering crowd in hats and caps, and pigeons taking off |

## Known open items
- **Costume:** the clothes are MakeHuman's CC0 shirts and trousers, re-shaded so the denim reads as wool. There are no braces or waistcoat, and the shirt keeps its collar.
- **Whip-pan from the foundry to the cell window (14.0–14.8 s):** it is very fast (about 20 m/s) and is meant to read as motion blur. The day→night change is hidden inside it.
- **Short hand-reach gaps:** some grasps fall 3–17 cm short for a few frames during transitions, such as the guard waving and taking the box (frames 545–589). The window hand-off is fixed in v003. Elsewhere the hands follow the props.
- **Penetration count:** 244 hand/foot frame-hits, mostly fingertips 1–2 cm into held props or soft wax. There are 0 character overlaps and 0 head-item vertices through. See `../PrisonKeyCake_v001/audit/penetration_C.txt`.
- **The crowd:** it is FK only. Arms wave and heads turn, but the crowd's feet stay planted. It is two base characters with varied clothing colours, scale and hats.
- **The laundry:** it is stiff cloth planes with a Wave modifier.
- **Remaining built-in shapes:** a few small items are still our own geometry: the knife, flags, hats, sand mould and the small distant birds. The key, lock, cake, crucible, barrels, bucket and government building are real models.
- **Blank frames:** fixed in v003 (16.8 s and 23.4 s in the C sheets).
- **The camera near the window bars:** it passes within 5 cm of the bars twice (frames 363 and 893). This is the intentional fly-through.
- **No VO yet:** timing follows the brief's targets.
