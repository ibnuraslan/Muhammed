# Look: animated 3D, not a film (client, Nov 11 22:45 UTC). This overrides every earlier look note

The client says many films look **too realistic, like live-action film**, and that is dangerous for the channel: realistic injuries, weapons and disasters can read as real footage. The target is the reference channel's look, a **bright, clean 3D animation**, something like a polished game cinematic or an animated explainer. Nobody should be able to mistake a frame for a photograph.

**Exact target (client's words):** "animated style, but not too animated: close to realistic CGI, 3D animated." So: realistic CGI characters and objects with real proportions and detail, in the polish of 3D animation. Not cartoon, not Pixar-style exaggeration, not live-action film. Approved examples: HeadsetBullet v004, BellyFat v005, PrisonKeyCake v004.

**What stays:** detailed, believable *shapes*. "Not blocks" still applies: real models, correct anatomy, proper buildings and vehicles, no capsules or slabs. What changes is how those shapes are **surfaced, lit and photographed**.

## Do
- **Backdrops:**
  - Explainer, cutaway and macro beats sit on a **bright sky-blue gradient**: cyan `#4FC3F7` at the top to near-white `#E8F7FF` at the bottom. Not deep teal or navy, and not black.
  - Outdoor beats get a clear blue sky with a few soft clouds.
- **Lighting:**
  - Use high-key, soft and even light, with shadows lifted and readable.
  - Interiors are bright and clean.
  - Night or dark scenes, only when the story needs them, stay readable: blue-tinted, with the faces lit.
- **Colour:**
  - Saturated and clean. Use AgX with the look "Punchy" (or "Medium Contrast").
  - Use clear colour separation between characters, props and background.
- **Surfaces:**
  - Smooth and clean, stylised-realistic, with simple readable textures. Keep bump and normal strength low (about 0.3–0.4).
  - Use no grime, dirt, pores, wet-gore, photo-scanned grit or film-like wear on hero surfaces.
  - Use scanned assets only if they are softened: bump down, saturation up, roughness at least 0.35.
- **Characters:**
  - MPFB humans with smooth skin, clean simple clothes in solid colours, and expressive faces (brows, eyes, mouth), like CG animation characters.
  - Keep them clean, never sweaty or grimy.
- **Anatomy and cutaways:** use illustrated-realistic, colour-coded layers:
  - skin: peach
  - fat: yellow-orange, lumpy
  - muscle: red-pink with fibres
  - bone: cream
  - vessels: red and blue

  Make them glossy and clean, never wet or bloody.
- **Violence and danger:**
  - Show the impact and the consequence only: a bullet, a spark, a stylised crack or flash.
  - Keep it to small, clean red, with no realistic wounds and no realistic gore.
  - Explosions are bright stylised fire and smoke.
- **Camera:**
  - Keep the background readable: shallow DOF only on true macro moments (f-stop at least 5.6 elsewhere).
  - Use no film grain, lens dirt, chromatic aberration, vignette, handheld shake or heavy motion blur.

## Don't
- Dark, moody, cinematic grading; teal-orange "film" grading; heavy haze or volumetrics.
- Shallow-focus "photography" looks: blurred bokeh backgrounds on every shot.
- Gritty photoreal forests, rubble and blood.
- Real-looking wounds, injuries or corpses.

## Tool
`blender/pipeline/anim_look.py` gets a scene most of the way. It does not touch animation or geometry:

```
blender -b in.blend --python blender/pipeline/anim_look.py -- out.blend [--no-sky] [--sat 1.25] [--bump 0.35] [--exposure 0.0]
```

It changes:
- the colour look, to AgX Punchy
- the world as seen by the camera, to a sky gradient (use `--no-sky` if you have your own gradient backdrop)
- base colour saturation, up
- bump and normal strength, down
- roughness, to a minimum of 0.35
- the f-stop, to a minimum of 5.6
- motion blur, off
- volume density, halved
- lights, ×1.25

Afterwards:
- Recolour your own backdrop planes to the sky-blue gradient.
- Hand-fix any beat that still reads as a film.
- Check bright beats for blowout.

**Test:** pause any still. If it could pass as a photo or a movie frame, it's a reject. If it could pass as a clay toy or a diagram, it's also a reject. The target sits between them: a clean, bright 3D animation.

## Hands: top priority (client, Nov 11 23:00 UTC)
The client sees bad hands in most films. Each of these is a reject:
- **Joints bending the wrong way.** No finger, wrist or elbow bent backwards, twisted or past its natural range.
- **Hand or arm through the shirt, jacket or body.**
- **Hands merging or passing through each other.**
- **Hands that don't make sense for the action:** floating near a prop, or touching nothing while meant to grip.

Fix it this way:
1. **Limits.** Add Limit Rotation constraints (in local space) to every finger, thumb and wrist bone on all characters:
   - fingers: bend 0° to 90° forward, 0° backward, ±10° spread
   - thumb: a natural cone
   - wrist: ±60° flex, ±25° side
   - elbow: 0° to 145°, with no hyper-extension
2. **Relaxed default pose.** Fingers slightly curled, never flat-splayed, so idle hands look natural.
3. **Hand audit at C and D.** A BVH overlap check every 2 frames of:
   - each hand against the other hand
   - each hand against its own torso, clothes and head
   - each hand against other characters

   Re-key every flagged frame: move the hand out, or change the pose.
4. **Close-up pass.** Render a 270×480 close-up of every hand action (grips, touches, hands near the face or chest) and look at it. Fix anything odd.
5. **Grips.** Fingers wrap the object with visible contact, and the thumb opposes the fingers.

Report the hand-audit count (it must be 0, or explained) with the sheet.
