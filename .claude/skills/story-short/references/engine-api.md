# Engine API (shorts-maker/animator)

Keep this file current: when you add a set, prop, pose or item, add a line here.

## Commands
```bash
python3 make_short.py projects/<slug> --timings-only          # time the voice, write timings.txt
python3 make_short.py projects/<slug> --preview [--shots 03,07] [--preview-at 0.1,0.5,0.9]
python3 make_short.py projects/<slug>                          # full render → out.mp4 (fills the shot cache)
python3 make_short.py projects/<slug> --rerender 06,11         # re-animate only these shots, reuse the rest (~1-2 min)
python3 make_short.py projects/<slug> --music music.mp3        # with ducked background music
```
Whisper timings and TTS are cached in `projects/<slug>/.cache/`, so re-runs are quick.
A file `scenes/NN.mp4|png` overrides animated shot NN.

## Episode file shape (`projects/<slug>/animation.js`)
```js
import { THREE, ease, seg, lerp, clamp, lerp3, rng, toon, basic, box, cyl, sphere, mesh, textPlane, canvasTex, noiseTex } from '/animator/engine.js';
import { Char } from '/animator/cast.js';
import { /* sets & props */ } from '/animator/props.js';
export const shots = { '01': (S) => { /* build */ return (t, u) => { /* animate */ }; }, ... };
```

## engine.js
- `alignBetween(mesh, [x,y,z], [x,y,z])`: stretch a Y-up cylinder/box between two points (paddles, poles, ropes).
- Maths: `clamp(x,a,b)`, `lerp(a,b,t)`, `seg(u,a,b)` → 0..1 local progress, `lerp3`,
  `rng(seed)` → deterministic random 0..1, and `ease.{lin,in,out,io,back}`.
- Materials: `toon(color, opts)` (shaded), `basic(color, opts)` (flat/emissive look).
- Meshes: `box(w,h,d,mat,pos,{rot,scale,cast})`, `cyl(rTop,rBot,h,mat,pos,{seg,rot})`,
  `sphere(r,mat,pos,{scale,seg})`, `mesh(geometry,mat,pos,opts)`.
- Textures: `canvasTex(w,h,(g,w,h)=>draw, [repeatX,repeatY])`,
  `noiseTex(base, [specks], n, size, repeat, seed)` for grass/gravel/rock.
- Signs: `textPlane('TEXT' | [lines], {w,h,bg,fg,font:'Display, sans-serif',size,radius,border})`.
- **Stage `S`:** `S.add(obj)`, `S.scene`, `S.camera`, `S.duration` (s), `S.shake` (units),
  `S.onUpdate(fn(t,u))`.
  - `S.sky({top,horizon,bottom,fog:[near,far]|null,sun:[x,y,z],sunColor,sunI,hemi,shadow,ground})`
  - `S.shadowFocus(x,y,z)`: centre the shadow box on the action.
  - `S.cloud([x,y,z], scale, seed)` → group.
  - Split screen: `const [A, B] = S.splitScreen()` gives a top half (A) and a bottom half (B), each a
    landscape camera. Move them with `S.camMoveOn(cam, u, [pos0, look0], [pos1, look1], easing, [fov0, fov1])`.
    Great for "two sides" beats.
  - Camera: `S.camAt(pos, look, fov)`,
    `S.camMove(u, [pos0, look0], [pos1, look1], easing, [fov0, fov1])`,
    `S.camOrbit(u, center, radius, angle0, angle1, height, easing, fov)`.

## cast.js: characters
`new Char(S, 'hero'|'boss'|'rival'|'extra'|designObject, { pos:[x,y,z], h:2, seed, hat, color, shadow:true })`
- `.set({...pose})`, `.pos(x,y,z)`, `.group` (THREE.Group), `.d` (design, can be edited).
- Pose keys:
  - `walking` 0..1 + `walk` (phase, e.g. `t*9`)
  - `armL`, `armR`: angle from hanging down (0) → out (1.57) → up (2.6–3.0)
  - `eyes`: dot | half | happy | wide | closed | angry
  - `mouth`: smile | flat | frown | smirk | grin | o | open | shout
  - `brow` -1 (sad) .. 1 (angry)
  - `anger` 0..1 (white→red→purple) · `steam` 0..1 · `sweat` 0/1 · `blush` 0/1
  - `talk` 0..1 (lip flap) · `hop` 0..1 (jump height) · `squash` (head squash)
  - `facing` ±1 · `look` -1..1 (face direction) · `lean` · `sit` (hides legs)
  - `armsCrossed` · `blink` (default on)
  - `kneel` 0..1 (one knee on the floor, front foot planted, toward `facing`) · `seat` 0..1 (sitting, knees forward)
  - `aimR` / `aimL`: `[x, y, z]` world point the hand (or the held item's tip) reaches. The elbow bends
    naturally and the item points along the reach. `null` goes back to the arm angles.
  - `hold` / `holdL`: pencil | hammer | suitcase | window | blueprint | newspaper | ticket | spoon | flashlight | folder | paddle
- Design fields (for new characters): `body` vest|suit|plain, `color`, `shirt`, `tie`,
  `bodyW`, `headR`, `hair` tuft|slick, `hairColor`, `hat` pilot|beret|bun|hair|cap|hardhat|none,
  `glasses` round|shades, `mustache` walrus|pencil, `brows` 'bushy', `bald`, `pencil`, `eyes`, `mouth`.

## props.js: sets (coordinate notes)
- `airfield(S,{runway,mountains,seed})`: grass to ±1200; runway along **x** at z=0 (36 wide);
  apron at z≈-70; hangars at z=-112; tower (150,-95). Clouds included.
- `hangar(S)`: floor ±60, **open front toward +z**, back wall z=-54, arch radius 30. Park
  the jet at `(0, groundY, -10)`. Point light inside.
- `scaffold(S, x, z, h, {w, d})`: blue steel tower, deck at `h` (stand chars at y = h + 0.06),
  yellow guard rails on 3 sides (open front), X braces and a ladder. Keep it clear of wings (x > 4 on a jet).
- `hangarFront(S, x, z, {name, color})`: hangar facade facing +z, with a big company sign in the team colour.
- `desk(S, x, z, {w, d, top})`: wooden desk (top height `top`, default 1.06; use 0.8 for a
  character standing behind it). `userData.jolt(k)` makes the items jump, k = seconds since the slam.
- `office(S,{windows})`: room x ±12, back wall z=-8 with 3 sky windows, wood floor, lamps,
  a blueprint poster on the left wall.
- `draftTable(S, x, z, {rot, tilt, windows})`: `.userData.board` (tilting board group).
- `terminal(S)`: checker floor, back wall z=-12 with a DEPARTURES sign, side walls x=±24.
- `counter(S, x, z, {name, color})`: airline counter with a hanging sign.
- `cabin(S,{windows:'square'|'round'})`: tube interior, aisle along x, seats at z=±1.35
  (facing +x), wall windows at z=±2.42. Shoot **across** the rows (camera z≈1.6 looking -z).

## props.js: props
- `makeJet({windows:'round'|'square', stripe, name, gear, scale})`: nose +x, length ≈36,
  span ≈30. `userData.windows` (+z side holders), `userData.gear`, `userData.groundY`.
- `newspaper({masthead, headline, sub, windows})`: a 3×4.1 plane.
- `confetti(S, n, [ax,ay,az], center, seed)`: falling, self-animating.
- `tumbleweed(S)`: roll it by setting its position/rotation.
- `crackOverlay(w,h,seed)`: plane; `.userData.setProgress(0..1)`.
- `impactBurst(S, {text:'BAM!'|null, size, color})`: a comic star that faces the camera, drawn on top.
  Call `.show(k)` every frame (k = seconds since impact; negative hides it). Use `text:null` for sparks/pops.
- Jet window slot: `jet.userData.windows[i].children[1]` is the glass (hide it for an empty frame).
- `glassTex()`, `blueprintTex(windows, title)`.

## Long-form / horror / investigation (16:9)
- Landscape: `node animator/render.js --size 1920x1080 <episode.js> <jobs.json>` (the page gets `?w=&h=`; `W`/`H` are live in engine.js).
  About 0.55 s per frame at 1080p → roughly 1 min of render per 3.5 s of video.
- `S.grade({vignette, grain, tint})`: film vignette + grain over the whole frame (horror look).
- `S.hud(obj, d)`: attach to the camera (titles); returns the visible {w, h} at distance d.
- `kits/night.js`: `nightSky(S, {fog, moon, stars, moonLight, hemi})`, `ocean(S, {amp, color})` (animated waves),
  `lightBeam(S, pos, {length, radius, spin, yaw, tilt, opacity})` (lighthouse/searchlight/flashlight cone),
  `flicker(S, light, {amount})`, `rain(S, {...})`, `cityLights(S, {z})`,
  `prisonIsland(S)` → {lampPos}, `prisonCell(S, {toilet})` (floor y=0, back wall z=-1.6 with a vent at x 0.55, bars at z=+1.6).
- `kits/investigation.js`: `evidenceBoard(S, {pos, items, links})` (photos = mugshots of any design, sticky notes;
  `.userData.setStrings(k)` grows the red strings), `mapPlane({w, h, draw, route, markers})` (`.userData.setProgress(k)`;
  helpers `land()`, `label()` for drawing coastlines), `caseFile({title, lines, stamp})` (`.userData.stamp(k)`),
  `titleCard(S, title, {sub, y})` (`.userData.fade(a)`).
- cast: `'detective'` (the Hero in a trench coat + fedora), `portraitCanvas(design, {label, mugshot, bg})`, items `spoon`, `flashlight`, `folder`.
- Example: `projects/alcatraz-escape/test.js` (the 4-shot look test).

## Road / true-crime kit
- `kits/road.js`: `duskSky(S, o)`, `prairie(S, {night, poles})` (highway along x at z=0, lanes z=±1.8),
  `makeBus({name, dest, lit})` (front +x, door on the +z side at x≈5.5; `userData.windows`, `door`, `tail`),
  `busInterior(S, {night})` (aisle along x, rows x=-5.4+i*0.95, seats face +x, window seats z=±0.95,
  aisle seats z=±0.5, cushion y=0.54; `userData.light` to flicker; the view scrolls),
  `policeCar(S, x, z, {rotY})` (strobing red/blue), `semiTruck(S, x, z)`, `glassShards(S, pos)` (`.userData.burst(k)`).
- `kits/investigation.js`: `censorBadge(S, {size, text})` (`.userData.show(k)`), `courtroom(S)` (bench at z=-4.8).
- cast: `silhouette: true` (a dark figure, glowing eyes, no face/mouth), `headphones: true`, items `crowbar`, `gavel`.
- Seated passenger in a bus seat: `pos: [row + 0.12, 0.22, z], seat: 1`.
- Dark scenes: hide the sky dome (`S.dome.visible = false; S.scene.background = ...`), or a daylight sky leaks in.

## Sound design (no audio files needed)
- `projects/<slug>/sound.json` + `python3 tools/sound_design.py projects/<slug>` → `music.wav` (drone, ducked
  under the voice) and `sfx.wav` (cues at full level). Cue types: sting, hit, glass, thud, zap, whoosh, shimmer;
  `heartbeat: {from, to}` speeds up between two shots. Run `--timings-only` first.
- `make_short.py` picks up `music.wav` and `sfx.wav` automatically (`--music-volume`, `--sfx`).

## Wishlist (build when a story needs it)
railroad + train, canyon walls, city street, factory, kitchen, castle, ship deck, night
lighting, rain, dust/smoke particles, heat shimmer, x-ray cutaway shader, map/chart metaphor set.
