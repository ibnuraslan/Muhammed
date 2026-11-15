# Lessons learned: 35 films built in parallel (Nov 11–14, 2026)

We built 35 short films at once so we could learn what fails. This file is that knowledge.
**Read it before starting any new film.** It's written so a new film takes **1–2 hours**:
stage it the safe way from the start, run the checks, watch it moving, and deliver once.

Specs (unchanged): 1080×1920, 60 fps, Cycles, RenderStreet-ready `.blend` package, one continuous
camera, bright animated-but-close-to-real CGI (`STYLE_ANIMATED.md`), timed to the client's VO.

---

## 1. What the client rejected (every one of these cost a paid render)

### Bodies and hands
- An arm or hand **through a body**: through the chest, the shoulder or the head, or a surgeon's arm "hugging" across a patient.
- An **arm bending backwards** behind the body ("he doesn't turn around, the arm bends behind").
- A **hand with no arm**: a glove floating beside an object, or a sleeve entering the frame with no body.
- **Deformed hands**: ring or "OK" claws, melted blob gloves, crushed gloves, splayed claws touching an ear.
- **Mannequin arms**: locked straight at the sides, straight out sideways, a T-pose while kneeling, an elbow locked across a table.
- **Legs through objects**: legs passing through a bin's iron chute bar, a hand poking out through a bin wall, hands through a flap.
- A hand on the **crotch or backside** (a pushing hand on someone's bottom).
- **Faces pressed** into walls or objects, clasped hands pushed into the mouth.
- A **Spider-Man pose**: climbing a smooth wall with the feet on nothing.
- **No head**: the framing cut off at the neck, so only a torso shows.
- **Hair covering the whole face** for the whole scene.
- **Black-hole eyes**: no white or iris.
- **Eyelid glitches**: black bars across the eyes during a blink.

### Props
- A prop moving **by itself**: a pen floating and "drawing" with no hand, a gavel floating, a bag hovering, a stamp jumping across a desk.
- A tool **into a face**: a tool stuck in the temple, a pen into the face, an ear pushed into the surgeon's eye.
- A worn item **off the body**: a mask hanging off the face, a cap floating.
- **Wrong orientation**: an ear attached facing backwards.
- **Clothes changing colour** between shots with no reason shown.
- Helmets that look like **pumpkins**. A prop must read as what it is.

### Camera and frames
- A **giant glove or hand** filling the frame.
- A **blurred arm** sweeping past the lens.
- **Blurry stretches**: macros at f/2–5.6, out-of-focus fly-throughs, a beige blur "inside the wall".
- **Empty frames**: a plain wall, black frames, floor only, a tablecloth filling the screen.
- The **camera inside** a body, a wall or a back, or passing through a table edge.
- The camera **rolled 90°**, so a lying person looks pinned upright to a wall.
- **See-through x-ray or glass** versions of solid things (a bin, a cup). Viewers read it as limbs passing through walls.
- **Black panels or triangles** sweeping across the frame (hidden objects still blocking the camera).

### Acting ("nonsense, very weird actions, not real actions")
- Every beat must be what a real person physically does, here, for a reason.
- No frozen poses, no snaps between poses, no sliding feet.

## 2. Staging rules that prevent those faults (build this way from the start)
1. **Fewest possible hand contacts.** Every grip on a small tool is a risk. Prefer:
   - an object resting on a tray or stand
   - a hand shown from a distance
   - a hand out of frame
   - a cut to the object alone

   Show a grip only when the story needs it.
2. **A held prop is IN the hand.** Use `hand_poses.grip_object` with a **Child Of the hand bone**, with **no offset gap** (fingertip within 1–2 cm of the tool body). The prop never moves unless a hand holds it. Never parent a prop to the wrist with an offset; that gives a floating pen.
3. **Every visible hand has its arm**, connected to a visible body or going off the frame edge.
4. **No arm crosses another person's body or face on screen.** Route the arm outside the other body, or move the camera.
5. **Worn items:**
   - Masks: shrinkwrap to the face (2 mm offset), then bind to the head bone. `qa_check` ATTACH must be 0.
   - Caps: Child Of the head bone.
6. **Wrists and fingers:**
   - Wrist limits are `((-60,60),(-50,50),(-35,35))` in `hand_poses.py`.
   - Run the wrist limit in **YXZ order with forearm twist free**. XYZ clamping produced 45 single-frame hand pops in one film.
   - Never hand-set finger angles. Use the `hand_poses.apply_pose` presets: relaxed, relaxed_even, pinch, pinch_tuck, wrap_grip, cup_hold, point, open_alarm, hold_flat_object.
7. **Elbows bend.** A reach uses about 85–100° at the elbow, not the 135°+ IK limit. Idle arms hang relaxed with a slight bend, hands on lap, knees or table.
8. **Contacts are real:** feet on the floor, seat on the chair, fingertips on the surface (not 4–6 cm inside the tablecloth).
9. **Natural pain acting:** one hand on the hurt place, the other on the knee or thigh above the knee. No elbow-up "wing" poses.
10. **Faces read.**
    - The acting character's face shows on every story beat: no back of the head, no hair curtain, no face cut off.
    - For MPFB hair, part the fringe or tilt the head up.
11. **The camera moves only through empty space.**
    - Never through or past bodies, arms, caps, tables or walls.
    - No "inside the wall" fly-throughs.
    - Whips go across empty space, at most 60° per frame.
    - Keep the horizon level: use Track To with world up, never Damped Track roll.
    - Build the path with PCHIP-style monotone interpolation (no overshoot loops).
12. **Focus:**
    - Macros at **f/8–f/11 or more** (f/5.6 left about 2 cm of focus and read as blur).
    - Nothing blurred or empty for more than 0.25 s.
    - A hero macro holds for at most about 1 s.
13. **No see-through or x-ray versions of solid props.** Show an inside only with a camera that is inside, or with a clean cross-section of anatomy.
14. **Visibility keys:** key `hide_viewport` together with `hide_render`, or hidden objects still block camera rays (black panels, FILL flags).
15. **Simplify rule:** if a hand, finger or prop action isn't clean after one retry, re-stage it simpler (frame the hand out, cut to the object, wider shot). Don't keep iterating the risky shot.

## 3. Technical recipes
- **Black-hole eyes (MPFB EnhancedEye):** the cornea uses refractive transmission. With caustics off, almost no light reaches the iris. Fix: set Principled transmission to 0 and mix in a Transparent BSDF driven by the old transmission value. The script is `blender/LegoInNose_v001/scripts/eye_fix.py` on branch `claude/connect03-lego-in-nose`, commit a44130b. Apply it to every MPFB character.
- **Black hairline, brows or lashes:** if a packaging or texture-shrink step re-saves images with `save_render`, alpha is dropped and hair, brow and lash cards render as black bands. Re-save with `Image.save()` (keeps alpha). Found by Connect20 (HeadsetBullet), commit c3af015.
- **MPFB vertex groups:** bodies also carry `Left/Right/Mid`, `HelperGeometry` and `JointCubes` groups. Pick the dominant group from **bone groups only**. Exclude helper and joint vertices from collision targets (`clip_scan.py` does this).
- **Glove material:** a real MPFB hand with a latex material and posed fingers, never inflated "sausage" gloves.
- **The cloud has no GPU.** Workbench fails (no libEGL). Preview with Cycles at 4 samples + OIDN (`pipeline/preview.py`).
- **VO sync:**

  ```
  retime_to_vo.py -- NN.anchors.json NN.mp3 out.blend
  ```

  Then pack with sounds and the render path set, and **update the frame range in SETTINGS.md**. Several packages shipped with a stale range.
  For a new film where the VO already exists, **build to the VO timing from the start** so no retime is needed.
- **Retime vs. Scene Time:** a VO retime warps keyframes and markers, but Geometry Nodes that read the *Scene Time* node (spray windows such as `Seconds > 21.3`, emitters, rain) keep the raw clock, so their events fire at the wrong moment. After every retime, run `pipeline/fix_scene_time.py -- anchors.json`. It keys those clocks to the original timeline and lists other raw-clock sources (frame drivers, particle start/end, Build/Wave modifiers) to check by hand. Better: drive one-off events from keyed values, not Scene Time thresholds.
- **Packages:** `<Film>_vNNN/` holding:
  - `<Film>_vNNN_60fps.blend` (all textures packed, under 95 MB, plain git, factory-startup check)
  - `<Film>_vNNN_VO.mp3`
  - README.md, SETTINGS.md (frame range!) and CREDITS.md
- **Disk:**
  - Delete scratch blends after use.
  - Prune remote-tracking refs of finished chats (`git update-ref -d` then `git prune --expire=now`).
  - Purge the pip and uv caches.

## 4. Mandatory checks (all on the packed file)
| Script | What it catches | Pass |
|---|---|---|
| `pipeline/clip_scan.py` | body-to-body intersections on camera | 0 bad ranges |
| `pipeline/qa_check.py out.json 6 beats.json` | EMPTY, FILL, INSIDE, BACKHEAD, HOVER, CLAW, FACEPRESS, PROPMOVE, ATTACH, ROLL, CAMJUMP, FAN | 0, or each remaining flag listed with its reason |
| `pipeline/limb_check.py out.json 2` | ARMBODY (arm inside a torso or another body), ARMBACK (wrist behind the shoulder plane), PROPHEAD (prop inside a head) | 0 visible. Hits on upperarm01 points 0–2 within 4 cm of the shoulder are known false positives. |
| `pipeline/body_prop_cross.py out.json 3 Prop1,Prop2` | legs, hands or clothes passing THROUGH thin props (bars, bin walls, flaps, doors, table and chair frames) | 0 visible crossings |

**The checks are not approval.** Every fault in section 1 the client found by watching. Several passed every script.

## 5. Review protocol: how a film gets approved
1. **Watch it moving, start to finish.**
   - Run `pipeline/preview.py` (every 5th frame, 270×480, frame number burned in).
   - Then run `pipeline/watch_pages.sh DIR 5 VO.mp3`.
   - Read **every** contact page (50 frames each). Still sheets every 0.5 s missed most faults.
2. **Zoom in** on anything doubtful: extract those frames at full preview size, or render 540×960.
3. **Look for section 1 on every frame:**
   - hands with arms
   - props in fingers
   - limbs outside bodies and props
   - faces, eyes, hair
   - blur, empty frames, roll
4. **Never approve from a chat's self-report or from numbers.** Chats said "watched start to finish" on films that still had the faults.
5. **Deliver only what you watched.** Every download link goes with the free preview MP4 (with VO) so the client can look before paying for a render.
6. **Status must be honest.** A film is READY only after step 1 on the exact delivered file. Mark everything else ON HOLD in `briefs/FINAL_PACKAGES.md`.

## 6. Fast pipeline for a new film (target 1–2 h)
1. **15 min, script → beats.** Script plus VO word timestamps (`pipeline/transcribe.py`) give the beat frames. Stage each beat with the **fewest bodies and hand contacts** that tell it (section 2).
2. **30 min, build.**
   - Use MPFB characters with the eye fix, latex gloves, a fitted mask and cap, and `hand_poses` presets.
   - Use real assets (`find_models.py`, `fetch_polyhaven.py`).
   - One camera on a smooth path through empty space, level horizon, f/8+ on macros.
3. **15 min, checks.** Run all four scripts in section 4, then fix the flags.
4. **20 min, watch.** Make the preview, watch every page, fix, re-preview the changed range.
5. **10 min, package.** Pack, set SETTINGS, README and CREDITS, push. Send the link **with the preview MP4**.

## 7. Director and chat workflow lessons
- Chats build; the director reviews. The director's job is to **watch**, not to trust reports.
- Fault notes always give **exact frames** (preview index and film frame) and the concrete fix, not "improve acting".
- Map times between versions through the VO anchors. State which timeline the frames are in.
- When the client has rendered a version, their list is the truth. Check it against the render and add your own findings to it.
- Never ship a version that's still in review. If the client is rendering an older faulty version, tell them immediately and name the clean replacement.
- Ask before any long local render or paid job. Never submit paid renders. Never ask for secrets in chat.

## 8. Final rounds (Nov 15): what still failed, and the blueprint for the next batch
The last 10 films needed 3–10 review rounds each. Almost every fault below passed the chats' own checks
and was caught only by watching. New films start from `pipeline/CONNECT_BRIEF_v2.md`.

### Faults found in the final rounds (add them to section 1)
- **Props above or off the body:** a phone held flat above the head like a plate, a placard floating behind a head, a diving mask flying onto a face with no hands on it, a 3D-printer nozzle floating beside the print. A held prop sits **in the fingers, below the hair line**, with its arm visible.
- **Hands from the frame edge:** a surgeon's hand touching a forehead with no body in frame; passengers' hands reaching in toward someone's back.
- **Bodies through set pieces:** legs through a bed's foot rail, a stretcher end through the carrier's torso, an arm through a seat back while hauling someone.
- **Lens blockers:**
  - windscreen frames and pillars, glass panes, sun visors
  - shelves at the start of a move
  - reed blades, a rock slab at a cave mouth, a gear bag
  - the tarp at the edge of a close-up
  - a mirror frame
  - a shoulder filling the bottom half of the frame
  - a man's face pushed into the lens

  Check the first and last frame of every shot, and every camera move through a set.
- **Faces:**
  - black-hole eyes on new rigs (add a small camera catchlight and check the eye material)
  - a bleached white face from a fill light at 25 W
  - teeth bared in a "smile" that reads as a grimace
  - a fringe covering one eye in every close-up
  - a background head merging with the hero's head
- **Mannequin arms on rigs whose rest pose is bent:** the MPFB rest elbow is about 46°. With an IK limit of min 0°, the arm can never straighten, so hand passes pushed the arms out sideways into an A-pose. Open the elbow limit per character, and check every walk, run and standing idle.
- **Skin-coloured clothes:** a flat-tinted tight suit read as a naked figure in the background. Check every crowd and background person in colour.
- **Render faults:**
  - blown-out white ballast with black holes (a fill light left on)
  - a black notch on shorts (a clothes delete-group that removed thigh skin)
  - a sleeve stretched into a skin sheet when the wrist aimed at the wrong place
  - a bright sky sheet on flood water at grazing angles (specular above 0.05)
- **Empty, black or blurred frames:** fades to black, murky water, empty sky between shots, empty windscreen views (about 7 s in one film), an empty pink plane at the end of a cross-section push, a ghosted double-exposure frame at a cut. Every frame shows a readable subject. Use hard cuts, never blends.
- **Static holds:** the client now rejects any hold over about 2 s with no movement: a frozen close-up, a static wide, a frozen boy holding a box. Give every shot an action (head turn, breath, push-in), or cut.

### Process lessons
- **Never pass a shot from its middle frame alone** (B10, Nov 15). A hand through a glass and a rod through a hand were visible only at the start and end of the shots. Every review, P1 included, looks at the first, middle and last frame of every shot, zoomed, plus `body_prop_cross` on every held prop.
- **Build to the VO from the start.** Put the beat frames at `1 + round(seconds × 60)` of the VO words, with `frame_end` just past the last word. Films built to the VO (28, 23) needed no retime. Retimed films played parts at 0.5–2.9× speed.
  - **Never time-stretch character animation.** Extend it at 1× instead: a longer swim path or walk, or a second angle.
  - Only camera-only shots (diagrams, cross-sections) may stretch.
- **Particles, Wave and Build modifiers and Scene Time do not follow a retime.** Remap particle `frame_start` and `frame_end` through the anchors (34: sparks, filings) and run `fix_scene_time.py`.
- **Preview economy:**
  - One full preview when the chat believes the film is clean.
  - After that, re-render only the changed ranges from the exact package and splice them in. Most chats got this right and cut a round from about 80 min to about 15 min.
  - The director diffs the new preview against the last one (`compare -metric RMSE` per frame) to confirm only those ranges changed.
- **No micro-tweak pushes.** One chat pushed hourly one-line script changes with no preview, and nothing could be reviewed. Batch every fix into one rebuild and push it with its preview.
- **Simplest re-stage wins.**
  - A shot that fails twice gets cut or replaced: drop the phone, cut the placard close-up, swap the windscreen shots for side shots, use a side medium instead of a foot-of-bed wide.
  - The VO carries the meaning; the picture only has to be clean.
- **Disk:**
  - Fetch chat branches only when reviewing, and prune them right after approval.
  - For one file, use a blobless bare clone (`git clone --filter=blob:none --bare`) plus `git show <commit>:<path>`, never a full fetch of a 10 GB branch.
  - Never `find -name "*.blend*" -delete`: it also deleted the `*.blend.anchors.json` sync records.
- **Keep the sync record of every delivered film** (`blender/briefs/sync/NN.anchors.json`), so previews and retimes can be rebuilt later.
