# RingBullet — PLAN (checkpoint A)

Connect21 · branch `claude/connect21-ring-bullet` · folder `blender/RingBullet_v001/`
1080×1920, 60 fps, frames 1–1410 (23.5 s). Cycles CPU. **One camera, one continuous spline move, no cuts.**

## World layout (metres, MPFB humans face −Y)
- **Set:** the back office of a small antiques shop at night. Dark wood-panelled walls, a plank floor and a rug. There's a heavy desk with a green-glass banker's lamp, plus a bookshelf, a grandfather clock with a swinging pendulum, picture frames and plants. A rain-streaked window on the back wall shows the street, and a door in the right wall leads out to the street.
- **Man** ("Owner"): an MPFB male, middle-aged, bald, in `male_elegantsuit01` (jacket, white shirt, tie). He stands behind the desk at (0, 0), facing −Y. He wears a gold wedding band on the left ring finger (`finger4-1/2.L`, Child Of the bone).
- **Robber:** an MPFB male in near-black clothes, standing at (0.35, −2.4) facing +Y. We only ever see his back, shoulder and arm, as a silhouette against the lamp light, and **never his face**. His right arm is extended and holds a pistol (simple dark prop). The gun points at the man's head, **always side-on or away from camera, never at camera**.
- **Bullet path:** from the muzzle (≈0.2, −1.75, 1.62) to the ring on the raised left hand (≈0.05, −0.32, 1.63), in stylised slow motion with a time ramp. It is fast out of the muzzle, then crawls during the macro.

## Beat table (frame = 1 + t·60)
| # | t (s) | Frame | Line | On screen | Camera (one framing ≈ every 1 s, all on one spline) |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | The robber fired the gun straight at his head | Warm lamplit office. The man, terrified, is mid-flinch, and the robber's dark arm in the foreground holds the pistol. Muzzle flash at f30 with a smoke puff, a spent case tumbling out and dust motes. The bullet leaves the muzzle in slow motion. | 0.0: low over-the-shoulder behind the robber's arm, the man centred. 1.0: the camera slides forward along the arm to the muzzle as it flashes. 2.0: it picks up the bullet and **rides it**, bullet in the lower third of frame and the man's face growing ahead. |
| 2 | 2.7 | 163 | threw his hands up to cover his face | Slow motion: his hands snap up in front of his face, fingers spread. The gold ring glints (a light pulse and specular flash). Papers lift off the desk in the muzzle shockwave and the lamp sways. | 2.7: the camera peels off the bullet and arcs round to the **reverse** (in front of the man, bullet in the foreground). 3.7: medium close-up of his terrified face as his hands rise. 4.7: tilt down to the left hand rising. 5.7: push in on the ring glint. |
| 3 | 6.8 | 409 | instead of going through his skull | Macro: the bullet crawls toward the hand, with his face soft behind. A heat shimmer and dust surround it. | 6.8: macro behind the bullet, low. **Rack focus** from the bullet to the ring (DOF focus distance animated). 7.8: the camera slides to a side-on profile with the bullet, ring and face in a line. |
| 4 | 9.0 | 541 | the bullet hit his wedding ring | Impact on the ring: a burst of sparks, a white-gold metal flash and a light pulse on his face. The hand jolts back, his fingers splay and his head recoils. | 9.0: macro side-on at the moment of impact, with a small camera shake. 10.0: the camera eases back to a close-up as the hand is knocked back. |
| 5 | 11.0 | 661 | glanced off the metal and split into two pieces | Slow-motion macro: the bullet squashes (a deformation shape key), then splits into two fragments that fly apart in a V, each trailing a faint streak. Sparks fall. | 11.0: orbit around the ring, macro. 12.0: continue the orbit, showing the two fragments separating. 13.0: pull out to a close-up with the fragments heading toward the finger and the neck. |
| 6 | 14.4 | 865 | One piece lodged in his finger | Fragment A curls into the side of his middle finger and stops in it. A small dark nick appears, with **no blood**. He winces: eyes squeeze, head jerks and his shoulders hunch. | 14.4: track with fragment A to the finger. 15.4: rise to his wincing face, hand in the foreground. |
| 7 | 16.3 | 979 | the other went into his neck | Fragment B flicks past the side of his neck, leaving a small red mark (no blood). His right hand flies to his neck. | 16.3: quick **whip-pan** following fragment B to the neck. 17.1: settle on his hand clutching his neck. |
| 8 | 17.9 | 1075 | minor injuries and a dented ring | He slowly lowers the left hand and stares at it: the ring is dented and bent, and the nick is on his finger. His face shows disbelief. Blue and red police light starts pulsing through the window. | 17.9: close two-shot of the hand and face. 18.9: **orbit close** around the hand (macro on the dented ring). 19.9: continue the orbit to his face lit by the first blue/red wash. |
| 9 | 20.8 | 1249 | walked away okay | Bandaged finger and a small neck plaster (swapped in during the police-light wash). He walks past the desk and out of the door toward the flashing police lights outside: a blue/red glow, rain and the wet street. | 20.8: the camera pulls back and cranes up to wide. 21.8: he walks out of the door (planted feet, IK walk), seen from inside. 22.8–23.5: settle on the doorway glowing blue and red. |

`beats.json` is written from the frame column; `retime_to_vo.py` will warp to the VO later.

## Assets (all CC0 unless noted)
- **Humans:** MPFB2 / MakeHuman system assets (CC0). Clothes `male_elegantsuit01`, `male_casualsuit01` (robber, tinted near black), `shoes0x`. The owner is bald (no hair asset).
- **Poly Haven (CC0):** HDRI `warm_restaurant_night` (reflections only, 2K). Models: `wooden_bookshelf_worn`, `vintage_grandfather_clock_01`, `WoodenTable_02` or `metal_office_desk`, `book_encyclopedia_set_01`, `decorative_book_set_01`, `fancy_picture_frame_01`, `potted_plant_01`, `ArmChair_01`, `mantel_clock_01`, `tea_set_01`, `service_pistol` (kept dark, side-on, in shadow) and `medical_tape`. Textures: wood panelling, floor planks and plaster (1K–2K).
- **Procedural (ours):** bullet (modelled 9 mm round nose, copper/brass), fragments, wedding band plus a dented-band shape key, sparks and smoke particles, muzzle-flash emission card, rain on the window, bandage and plaster, banker's lamp shade if needed, window street backdrop and police-light rig (animated red/blue area lights, no vehicle branding).
- There are no logos, text or brand names anywhere. The pistol has no markings.

## Tricky shots and how
1. **Riding the bullet at macro scale (beats 1–5).** The bullet is modelled at real size (9 mm). The camera has a 0.002 m clip start, a 50–85 mm lens and real DOF. One camera on a Bezier/keyed path with continuous velocity, built from framing keys per beat, Catmull-Rom smoothed position and target, and tracked by an empty "aim" target. The slow-motion ramp is a 1D time curve for the bullet position along its path, so the camera and bullet stay locked.
2. **Rack focus (beat 3).** The camera DOF focus distance is keyed from the bullet distance to the ring distance over about 0.8 s.
3. **Hands up / fingers spread / ring.** IK hand targets from `anim_lib.make_human_ctrl` plus keyed finger curls (finger*-1/2/3). The ring is Child Of `finger4-1.L`, sized to the finger and checked numerically for no gap or penetration.
4. **Impact and split (beats 4–5).** The bullet object gets a squash shape key, then it is hidden and two fragment meshes take over from the same transform. Sparks are a particle emitter burst (or keyed tiny emissive streak instances) with a point-light flash.
5. **Injuries, kept clean.** The nick and neck mark are small decal planes, dark red-brown and matte, with no blood. The bandage is a thin cylinder sleeve on the middle finger and the plaster is a small rounded card on the neck, both Child Of the bones. They appear during the police-light wash.
6. **Walk-out (beat 9).** The `anim_lib.Human.walk` IK walk on a flat floor, with feet planted, toward the door. The camera cranes and pulls back so the move reads wide.
7. **Never the robber's face, never the gun at camera.** The camera path stays in the half-space behind the robber's shoulders or beside the gun. The audit checks the angle between the gun axis and the camera direction every frame, and that the robber's head is never in frame from the front.

## Audit (written for this film)
For every frame, the audit checks:
- foot hover and sink against the floor
- hand and ring penetration (BVH overlap)
- ring-to-finger gap
- bandage and plaster gap
- the camera inside geometry
- gun-at-camera angle
- robber face visibility

The counts are reported at C.

## Schedule
A 19:55 · B 23:15 · C 00:45 · D 01:30 (UTC)
