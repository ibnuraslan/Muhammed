# DrunkTrain_v001: plan (checkpoint A)

Film: 1080×1920, 60 fps, frames 1–2070 (34.5 s). Cycles CPU. One camera `CAM_Film` on one continuous spline, no cuts.
Script: our own 96-word script from `briefs/16_DrunkTrain.md`. Timed to the target beat times until the VO arrives; `beats.json` goes with the package for `retime_to_vo.py`.

## Sets
- **S1 rail line (real set).** A straight double-track suburban line: two steel rails (real rail profile: head, web and foot) on concrete sleepers over a gravel ballast bed (Poly Haven gravel texture plus scattered instanced stones that can bounce). Embankment grass, a chain-link fence, a row of houses and back gardens beyond, poles with overhead-line style cables (no text), and a low platform edge at the far end for beat 12. Bright daylight HDRI.
- **S2 x-ray studio.** The clean explainer look: a soft cyan-to-white gradient cyclorama placed right beside the rail set (about 30 m off the track). The camera reaches it by a push into his chest and comes out in the studio, with no cut. A ghost copy of the train front and a slow-motion replay of his body sit in the studio for beat 11.

## Characters (MPFB2, MakeHuman CC0)
- **Drunk man ("Lad")**: young, slim, generic. Bright tee and shorts (a casual suit tinted bright orange, with the trousers shortened by a mask on the body below the knee), sneakers, short hair. One rig is used for all beats. The rag-doll spin is keyframed through the IK control rig with overlapping, delayed limbs.
- **Bystanders**: a woman and an older man in casual clothes, plus a rail worker in a hi-vis vest (worksuit tinted fluorescent yellow-orange, with a hard hat parented Child Of to the head bone).
- **X-ray body**: a duplicate of Lad with a translucent skin shader (glass/transparent mix with fresnel). Inside it, procedural "muscle" ribbons (curve-based bundles along the bones with a striated red-pink texture) and a simple skeleton. Their loose, rope-like sway comes from a wave modifier and delayed bone keys.

## Props
- A freight locomotive with 2–3 wagons, with no livery text. The first choice is a CC-BY/CC0 Sketchfab/Objaverse GLB via `find_models.py`; any text decals get repainted plain. The fallback is a procedural locomotive (box hood, cab, headlights, a bogie with six wheels, buffers) with a dirty-paint and rust texture.
- An unlabelled green glass bottle, sparks (particle-free: instanced emissive streaks keyed per frame, because farm caches are not allowed), dust puffs (volume cubes plus billboards), gravel debris, and force arrows (emissive cyan meshes).

## Beat table (target start, frame = 1 + t·60)
| # | t (s) | frame | Line | On screen | Camera (one framing per ~1 s) |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | He stumbled drunk across the train tracks | Lad staggers across the sleepers, swaying with big off-balance steps, catches a toe on the rail and lurches. Birds lift off the fence; a dog barks behind a garden fence; laundry moves in the wind. | 0.0 medium from the front-left at hip height, weaving with him → 1.0 drifts right, crossing the rail line → 2.0 drops low as he trips |
| 2 | 2.5 | 151 | passed out with his head resting on the rail | He collapses onto the ballast and his head settles sideways on the railhead. Chest heaves with a snore; his hand flops; bottle rolls away. | 2.5 crane down to rail height → 3.5 slide along the rail toward his face (close) → 4.5 macro on his cheek on the steel, with snore breath |
| 3 | 5.5 | 331 | a cargo train came rushing toward him | Rack focus from his face down the rail to the headlight far off. The rail hums (micro-vibration), gravel jitters, and the locomotive looms with horn and headlight flare. | 5.5 rail-level macro → 6.5 rack focus to the train → 7.5 pull back low as the train grows → 8.5 whip toward him |
| 4 | 9.0 | 541 | It slammed into his head, spinning him around | The pilot (plough) hits; a burst of gravel and dust, motion blur, and his body spins like a rag doll, limbs trailing. No injury detail; his head is hidden in dust and blur at the impact. | 9.0 locked tight on the impact point, speed ramp → 10.0 orbit with the spinning body |
| 5 | 11.0 | 661 | dragging him beneath the train | Under the train: dark, wheels rolling, sparks off the brake shoes, and his tumbling silhouette among the bogies, lit by spark light. | 11.0 dive under the buffer beam → 12.0 skim beside him between the wheels → 13.0 track along a bogie with sparks → 14.0 rise to the side |
| 6 | 14.5 | 871 | finally screeched to a stop | Wheels lock and slide, sparks shower and the train rocks to a halt. A dust wave rolls out and slowly settles. | 14.5 low beside a locked wheel → 15.5 pull out along the train → 16.5 high over the stopped train as the dust settles |
| 7 | 17.0 | 1021 | witnesses were sure he was dead | Two bystanders and a rail worker in hi-vis run up along the ballast and stop, hands to their mouths, peering under the wagon. | 17.0 crane down into the group → 18.0 orbit past their faces → 19.0 push toward the gap under the wagon |
| 8 | 19.5 | 1171 | But then, he stood up | Under the wagon he stirs, crawls out on his hands and knees, then stands up wobbling and blinking. The bystanders stagger back. | 19.5 low at the wagon gap → 20.5 rise with him as he stands |
| 9 | 21.0 | 1261 | Because he was so drunk | A flash-back flourish: the image desaturates with a quick whip, and he is swigging from the unlabelled bottle on the track earlier (the same set, an earlier pose, warm tint). | 21.0 whip-pan around his head → 22.0 close on the bottle swig → 23.0 push to his chest |
| 10 | 23.5 | 1411 | his muscles were completely relaxed… limbs loose | Fly through his chest into the x-ray studio: the body is translucent, and loose relaxed muscles sway like rope from a dangling arm and leg. | 23.5 dive through the skin → 24.5 orbit the x-ray body → 25.5 macro on the loose arm muscles swaying |
| 11 | 26.5 | 1591 | his body moved with the train's force instead of fighting it | A slow-motion x-ray replay: a ghost train front pushes, cyan force arrows flow, and the limp body bends and rolls with them. A brief stiff "red" comparison ghost snaps rigid beside it, then fades. | 26.5 wide on the replay → 27.5 track with the arrows → 28.5 orbit → 29.5 push out of the studio → 30.5 fly back toward the rail set |
| 12 | 31.0 | 1861 | He walked away with only a few cuts on his hand | Back on the real line: he wanders off toward the platform, stops, and looks at his palm (three small clean scratches). The bystanders stare and the worker scratches his hard hat. Settle on his dazed grin. | 31.0 follow behind him → 32.0 swing around to the front → 33.0 close on the palm → 34.0 tilt up to the grin |

## Trickiest shots and how I'll do them
1. **The impact and the rag-doll spin (beat 4).** Keyframed rather than simulated, because the farm needs no caches. The root spins about 540° on a curved path with a damped wobble; arms and legs use delayed, overlapping keys (each one lags the torso by 3–6 frames), with the IK pole flips smoothed. Motion blur at 180°, a gravel and dust burst, and the camera orbits with the body. The head is never shown at contact, which is masked by dust and blur.
2. **Under the train (beat 5).** It must be dark but readable: spark streaks are the key light (emissive streaks plus a point light that flickers), with a cool fill. Wheels rotate by driver. His body is a silhouette that tumbles parallel to the train at the same speed, then slows.
3. **The continuous camera from the real set to the x-ray studio and back.** The camera pushes into the chest of a translucent duplicate (crossfaded with the real body over ~6 frames by material keying), then the studio set is placed so the camera emerges into it. Coming back, it flies out through the studio's open side and travels to the platform end of the rail set, so that move covers the distance.
4. **The flash-back (beat 9).** With one camera and no cut, a second Lad copy holds the earlier pose (swigging), staged beside the current one; a whip-pan hides the swap of which body is visible, plus a compositor-free colour shift done by keyed exposure and world tint.
5. **Contact.** Head on the railhead (the rail is a real height mesh, and the cheek is snapped to it), hands planted on the ballast when crawling, and feet planted while walking (`Human.walk`). The audit checks feet and hands against the ballast and rail surfaces, the head against the rail, and the camera inside geometry.

## Assets and licences (to confirm when fetched)
- Poly Haven CC0: a daylight suburban HDRI (2K), gravel/ballast, grass, concrete, rusty metal and brick textures (1K–2K).
- MPFB2 / MakeHuman: CC0 system assets for all humans and clothes.
- Locomotive and wagons: Sketchfab CC-BY via Objaverse if a clean one exists (credited in CREDITS.md and the description), otherwise procedural.
- Houses and fence: procedural or Poly Haven models.

## Risks I want flagged now
- The x-ray "muscles" will be stylised explainer anatomy (clean ribbon bundles), not a full anatomical muscle model, as there's no CC0 muscle mesh at hand.
- Time is tight (the package is due at 01:15 UTC). If beat 5 can't reach the bar, I'll keep it darker and shorter in readability rather than slip the schedule.
