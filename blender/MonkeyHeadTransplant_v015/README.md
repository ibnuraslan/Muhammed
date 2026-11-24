# MonkeyHeadTransplant_v015: CLIENT-APPROVED

> **Status: CLIENT-APPROVED** (relayed by the director on Nov 24). The client approved the check-1 cut of v014 and asked for no more rebuilding.

## What this package is
- The v014 **check-1** animation, built exactly from the check-1 scripts.
- It uses the v013 VO and timing: frames **1–1656**, 60 fps, 1080×1920, with one continuous camera and no cuts.

These safe changes were added on top:
1. **Oscilloscope (check-2 fix):**
   - Moved onto its cart behind the table, beside the surgeon, so it no longer blocks the lens.
   - Its printed textures are flattened, so no text shows.
   - Camera keys 1267 and 1360 are re-aimed so the monkey, the trace and the surgeon share the frame.
2. **X-ray (check-2 fix):** transparent bounces raised to 48, so no black shards show inside the transparent body.
3. **Lamp (check-2 fix):** the dome lamp is raised 40 cm, out of the top of the frame. The standing instrument racks are hidden.
4. **From 18 s:** the surgeon stands 18 cm to the side, so his cap no longer sits behind the monkey's head.
5. **Neck disc:** skin-toned instead of bright pink.

## Known look, accepted by the client
- **Stitching (7.5–10 s):** the needle holder reads as loosely held. The hand is splayed over the back of the neck, and the tool sits under the fingers. In the rig, the tool is Child Of the `wrist.L` bone, so it moves with the hand.
- **Head carry (3.6–4.8 s):** a glove passes in front of the donor head's face.

The later grip attempts (v014 `scripts/wip_round3`, `wip_round4`) failed the contact audit and are not used.

## Files
| File | Contents |
|---|---|
| `MonkeyHeadTransplant_v015_60fps.blend` | 43 MB. Everything is packed: images and the VO sound. `package_for_farm` reported no problems. See `SETTINGS.md`. |
| `MonkeyHeadTransplant_v015_VO.mp3` | The voiceover |
| `review/preview.mp4` | Preview made from this exact package: every 5th frame, 270×480, with the VO |
| `beats.json`, `CREDITS.md` | Synced beat frames and credits |
| `scripts/` | The build: `01_base` → `02_surgeon` → `03_layout` → `04_animate` (uses `camera_keys.json` and `layout.json`) → `pipeline/package_for_farm` |

## Watched-preview notes (v015 preview)
These are side effects of the cap shift. The monkey's face stays in frame in all of them.
- **21–24 s:** the surgeon is mostly at or off the left edge of the monitor shot.
- **22.0–22.6 s:** his raised arm enters at the left edge, with little of his body in frame.
- **26–27.6 s (ending):** he is half-cropped at the left edge.

If any of this matters, the fix is to re-aim camera keys 1267, 1360, 1447, 1560 and 1656 about 15 cm to the left. That would need one more preview.
