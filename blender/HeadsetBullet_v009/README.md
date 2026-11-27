# HeadsetBullet_v009: the from-scratch rebuild (batch 1, film 20)

**Status: approved by the client, relayed by the director on 2026-11-27, as built.** The client watched `review/preview.mp4` and approved this exact build.

My own independent reviewers still marked the last preview FAIL. The open notes are in `review/CHECK3.md`:
- the band passes his eyes for about 0.15 s at f991–1006
- his raised fists at f911–951
- how the slow-motion bullet reads

Watch the preview before rendering.

One boy, one headset, one bullet, one continuous camera. It's built to your voiceover (`HeadsetBullet_v009_VO.mp3`, the v008 recording), frames **1–1203** at 60 fps. The beats are timed to the recorded words (whisper word times), for example "smashed" at f31 and "hit the headset" at f516.

- Render settings: `SETTINGS.md`
- Credits: `CREDITS.md` (all third-party assets are CC0)
- Scripts in `scripts/`: 00 textures, 01 build, 02 animate, 03 package

## The film
- **Outside:** a cream house with a red tiled roof, blue shutters and flower beds. The camera chases the bullet to the casement window. The bullet cracks and shatters the closed pane (f45), and the shards fall and settle. The camera enters through the open half.
- **Inside:** a teen gaming at his desk, in a deep-blue room with magenta and cyan LEDs. He wears a red over-ear headset fitted to his head. The camera chases the slow-motion bullet toward his left ear cup. The DA KRAS FILMS poster sits on the back wall.
- **The hit (f525):** the cup cracks and dents, chips and sparks fly, and the camera pushes in on the lodged bullet. A short flash leads into the cross-section.
- **Ear-cup cross-section:** the bullet breaks the shell, squeezes the padding foam and hits the metal frame (sparks at f708). It tips and glances off. A flash leads back to the room.
- **Ricochet:** the bullet leaves the cup and hits the back wall (f835): a hole, plaster chips and sparks. He startles.
- **Removal:** palms on the outer faces of the cups, elbows forward. He lifts it up and forward, then holds it at chest height with both hands. His left hand supports the cracked cup, which faces the camera. He looks at it, turns to the hole in the wall, then back.

## Rig and contact rules
- One MPFB model all film: a real CC0 `male_casualsuit04` T-shirt and jeans with thickness, the chest flattened under the shirt, and the body hidden under the clothes.
- IK rotation limits on the knees (0–150°), elbows (straight to 150°) and hips (−20 to 125° flexion, ±35° abduction). Limit Rotation on the wrists and fingers.
- The headset is Child Of the head bone (fitted to the rest head) until the hands grip it. From then it's keyed in the world, with the hands solved to the cups every 2 frames.

## Render check: PASS
On the exact file `HeadsetBullet_v009_60fps.blend` (91 MB, md5 6b38cfc9764fee5746720b838f1282eb), opened with `blender --factory-startup -b`:
- No linked libraries and no unpacked images. The VO sound is packed.
- No drivers and no Python text blocks. No errors or warnings, apart from one Blender deprecation notice raised by the check script itself.
- Camera `CAM_Film`, 1080×1920 at 100 %, 60 fps, frames 1–1203, PNG to `//render/HeadsetBullet_v009_####.png`. The VO strip starts at frame 1. Filmic High Contrast, motion blur off.
- Test frames rendered at full resolution, 64 adaptive samples, on a 4-core CPU with no GPU:
  - f20 (exterior) in 176 s
  - f600 (impact flash) in 78 s
  - f1180 (the boy holding the cracked headset) in 273 s

  None is black, empty or pink.
