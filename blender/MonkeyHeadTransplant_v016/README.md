# MonkeyHeadTransplant_v016 (= client-approved v015 + DA KRAS FILMS logo + fast-render settings): CLIENT-APPROVED

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
| `MonkeyHeadTransplant_v016_60fps.blend` | 43 MB. Everything is packed: images and the VO sound. `package_for_farm` reported no problems. See `SETTINGS.md`. |
| `MonkeyHeadTransplant_v016_VO.mp3` | The voiceover |
| `review/preview.mp4` | Preview made from this exact package: every 5th frame, 270×480, with the VO |
| `beats.json`, `CREDITS.md` | Synced beat frames and credits |
| `scripts/` | The build: `01_base` → `02_surgeon` → `03_layout` → `04_animate` (uses `camera_keys.json` and `layout.json`) → `pipeline/package_for_farm` |

## Watched-preview notes (final v016 preview)
- **Camera keys 1267–1656 re-aimed** (the director's request). From 20 s to the end, the surgeon is fully in frame and both his face and the monkey's face are in frame.
- **The framing is wider than check 1.** The monitor sits at the right edge from 21 to 24 s.
- **From about 24 s, the donor monkey's headless body shows at the left edge of the frame.** Its neck cap is skin-toned and there is no gore. Tightening the lens on keys 1447–1656 would crop it, at the cost of cutting into the surgeon.

## v016 changes (nothing else changed)
v016 is v015, which the client approved, plus two additions. The animation, camera (all keys), characters, lights, colour and the keyed exposure, XRay and Void values are untouched.
1. **Logo.** The DA KRAS FILMS logo is printed on the front of the surgeon's scrub cap. It reads in full at frames 611–796 (3.1 s), 81–200 and 391–456, and smaller from 1086 to the end. There is also a small label on the oscilloscope front. All of it was checked in the moving preview.
2. **Fast-render settings.** Max bounces went from 12 to 6 and transmission from 8 to 6. Transparent stays at 48, which the x-ray void needs. OIDN now uses the albedo and normal passes, Persistent Data is on, and Simplify is on (2048 px texture limit). The purge removed 4 hidden objects that were never animated or rendered (`Collar_BodyA`, `Instruments`, `Mayo_Instruments`, `Scope_LabelPlate`) and their unused data. `scripts/05_polish_logo_fastrender.py` + `scripts/polish_cfg.json` made this version from v015.

Before/after check at full resolution, frames 1, 828 and 1656: RMSE 0.0019, 0.010 and 0.008. The only visible difference is the cap logo. The x-ray void and the end dim look the same.

## Render check: PASS
Run on the exact packed `MonkeyHeadTransplant_v016_60fps.blend` with `blender --factory-startup -b` (Blender 5.2.2):
- Opens with no errors or warnings. The only console line is the container's "CUEW: no CUDA library" note: this container has no GPU, and the note says nothing about the file.
- 0 linked libraries, 0 unpacked images, fonts or sounds, no auto-run scripts, no invalid drivers.
- Camera `CAM_Film`. 1080×1920 at 100 %, 60 fps, frames 1–1656. PNG to `//render/MonkeyHeadTransplant_v016_####.png`. The VO sound strip starts at frame 1 (frames 1–1582).
- Cycles: 48 samples, adaptive 0.05, OIDN (albedo + normal), bounces 6/3/3/6, transparent 48, caustics off, Persistent Data on, Simplify on (texture limit 2048), 0 orphan data blocks.
- Test frames 1, 828 and 1656 rendered at full resolution. None is black, empty or pink. Time per frame: 180 s, 180 s and 175 s on 4 CPU cores.
- `review/preview.mp4` (270×480, every 5th frame, with the VO) was watched start to finish, all 7 contact pages.
