# Phase 3: Produce

Inputs: `02-storyboard.md`, `script.txt` with markers, `voice.mp3`.
Output: `projects/<slug>/animation.js` → previews → `out.mp4`.

## 1. Build what's missing (reusable!)
- New sets go in `animator/props.js` as `export function railroad(S, opts)`. Give each one a
  documented coordinate system (where the floor is, which way things face, the main stage
  position) in a comment, and add it to `references/engine-api.md`.
- New props: functions that return a `THREE.Group`, with handles in `userData` for animated parts
  (wheels, doors, gear, cracks).
- New poses, items or hats: extend `drawItem`, `drawHair` or the pose list in `animator/cast.js`.
- New recurring character: add to `DESIGNS` in `cast.js` **and** to `style-bible.md`.
- Look: toon materials (`toon(color)`), canvas textures for detail (stripes, rock layers, wood,
  signs), `S.sky({...})` presets from the bible. Keep geometry simple and the colours rich.
- Quick-test a new set alone: write a tiny shot that just shows it with an orbit camera, then preview it.

## 2. Write `animation.js`
Start from `templates/animation.js`. One function per storyboard shot, keyed by the marker id.

```js
'07': (S) => {
  // set + actors (runs once)
  S.sky({...}); office(S);
  const hero = new Char(S, 'hero', { pos: [-1.9, 0, -0.6] });
  // update (runs every frame): t = seconds, u = 0..1 through the shot
  return (t, u) => {
    hero.set({ armR: 1.25 + Math.sin(t * 14) * 0.15 });            // continuous motion
    S.camMove(u, [[-3.6, 2.5, 5.2], [-1, 1.9, -0.8]],               // [camPos, lookAt] start
                 [[-3.0, 2.2, 3.4], [-1.4, 1.9, -0.8]], ease.io, [46, 42]);  // end, fov start/end
  };
},
```
- Time actions with `u` + `seg(u, a, b)` so they fit any shot length. Use `t` only for loops
  (walk cycles, wobble, flapping).
- Ease everything (`ease.io`, `ease.out`, `ease.back` for pops). Linear only for steady tracking.
- Framing maths (fov 50, 9:16): visible half-width ≈ **0.26 × distance**, half-height ≈ 0.47 ×
  distance. A 2-unit character is a full-body medium shot at about 4.5 units, and a face close-up
  (look at y≈1.65) at about 2–2.6 units.
- Characters are billboards and always face the camera. Use `facing: ±1` for which way they look
  sideways, and `look` for where the face points.
- `S.shadowFocus(x, 0, z)` on the main action, or shadows vanish on big sets.
- Re-use set builders across shots; each shot builds its own fresh scene.

## 3. Preview loop (mandatory, at least 2 rounds)
```bash
python3 make_short.py projects/<slug> --preview              # all shots, stills at u=0.1/0.5/0.9
python3 make_short.py projects/<slug> --preview --shots 04,11 # just the ones you changed
```
Read **every** `projects/<slug>/preview_N.jpg` and run this checklist for each shot:

- [ ] The subject is in frame and readable at all 3 moments (nothing cropped by the narrow vertical frame)
- [ ] The subject is ≥ 1/4 of the frame height (except deliberate aerials/establishing shots)
- [ ] There's visible change between u=0.1 and u=0.9: the camera moved **and** something acted
- [ ] Nothing is blocking the subject (seat backs, walls, table legs, the camera inside geometry)
- [ ] Faces are out of the caption band (about 62–78% height) in close-ups
- [ ] Colours and cast match the style bible; team colours are correct
- [ ] It matches the storyboard's intent; the sound-off story still reads
- [ ] Continuity with the neighbouring shots (screen direction, who's where, props in hand)
- [ ] Every action has **contact + reaction** (what it hits reacts: jump, burst, shake, flinch)
- [ ] No big ambiguous background shape slides behind the camera move (it reads as a moving object)
- [ ] No foreground slab (wing, wall, table edge) covering more than ~1/5 of the frame
- [ ] Every prop reads as what it is (a scaffold has rails, a desk has things on it)
- [ ] The u=0.9 frame still shows the subject (pull-backs and pans love to drift off)

Fix, re-preview those shots, and repeat until every box is ticked. Note what you fixed. If the
same class of problem keeps appearing, add a lesson.

## 4. Full render
```bash
python3 make_short.py projects/<slug>        # run in the background; about 10 min per 40 s
```
Then check it:
```bash
ffmpeg -v error -i projects/<slug>/out.mp4 -vf "fps=1,scale=216:384,tile=10x5" -frames:v 1 projects/<slug>/final_sheet.jpg -y
```
Read the sheet. Check that the captions match the speech, that no shot is broken, and that the end holds.
Then the **dense motion review** (mandatory before delivery). 4 fps sheets show sliding
backgrounds, missing contact and drifting cameras that stills hide:
```bash
d=projects/<slug>/review; mkdir -p $d
ffmpeg -v error -i projects/<slug>/out.mp4 -vf "fps=4,scale=180:320" $d/f_%03d.jpg -y
for i in 0 1 2 3; do ffmpeg -v error -start_number $((i*40+1)) -i $d/f_%03d.jpg -frames:v 40 -vf tile=10x4 -frames:v 1 $d/sheet_$i.jpg -y; done
```
Read every sheet and write a shot-by-shot table (problem → general rule → fix) like
`example/03-review.md`. Fix and re-render before you deliver if anything fails. Use
`--rerender 06,11` so only the fixed shots are animated again (the others come from the shot cache).

## 5. Deliver
- SendUserFile the mp4 with a one-line caption.
- Tell the user, briefly: the shot count, the 2–3 shots you're proudest of, anything you know is
  weak, and the feedback question from SKILL.md.

## 6. Save
Commit `projects/<slug>/` (script, voice, analysis, storyboard, animation.js), engine changes
and skill updates. Never commit `out.mp4`, previews or `.cache` (they're gitignored). Push to the
working branch.
