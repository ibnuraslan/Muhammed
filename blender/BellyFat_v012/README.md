# BellyFat_v012

This build fixes the 13 points from the director's v011 frame-by-frame review. v010 and v011 are left untouched. It keeps the same VO, timing and frame range: **frames 1–1273 at 60 fps**, with the VO (21.0 s) packed. The film is built straight to the VO frames as 13 shots with hard cuts on one camera.

## Files
- `BellyFat_v012_60fps.blend`: the render file, 74 MB, everything packed. `SETTINGS.md` is the render sheet.
- `review/preview.mp4`: the preview, rendered with `pipeline/preview.py` from the exact package (every 5th frame, 270×480, 4 samples, with the VO). `review/pages/` holds the contact pages; I watched every page.
- `review/*.json`, `review/audit_hands.txt`: the check results for the package.
- `beats.json`, `CREDITS.md` (CC-BY intestine credit), `scripts/` (full rebuild: 01, 02, 03_shots, then anim_look, 05, shrink, 04 farm settings, package).

## The 13 points
1. **Origin and pose.** The opening is a medium close-up, so her face is larger. She reads the logo box, her weight shifts, and her free arm hangs relaxed with the elbow bent. The origin beat is a new shot (41–52): the bullet punches through the shop window, the crack spreads and shards fly. There is no shooter and no weapon.
2. **Near-empty frames, edge-cut bullet, white stub.** The crack is in frame from the first frame of its shot. The trail stub is deleted.
3. **Bullet static at the edge, woman out of frame.** The tracking shot (53–100) sits just behind the bullet. The bullet stays inside the frame and pulls ahead, she stays in frame down the aisle, and it converges on her belly. DOF is off here, so both the bullet and she are sharp.
4. **Empty-shirt close-up, speck, ring pop, sliding hand.** All gone. The impact is seen at the end of the tracking shot. The shirt hole grows during the impact frames instead of popping, and there is no hand insert.
5. **Reaction before the inside view, stiff arm, wound dot on the knee.** The film cuts straight to the inside after the impact. The reaction comes afterwards, with both hands on her belly. The glass shards that read as a dot are removed after the window shot.
6. **Pale capsule, halo, collar, floating red disc, thin layers.** No halo, no ring, no hole decal. The bullet is plain copper. The skin layers are tinted so they read as bands.
7. **About 7 s of static fat, bullet size popping.** Every inside shot uses the same side-on angle, distance and lens, so the bullet never changes size or shape. The camera half-follows, so the bullet visibly travels through each shot. Fat runs fast and steady (201–450), then the bullet slows through the fascia and muscle.
8. **Muscle slab blocking the lens.** The macro clip start is 55 % of the subject distance, so nothing can sit in front of the lens.
9. **Ring, floating bullet, white band.** No ring. The fascia is flush with the cut face and tissue-tinted, and a backing plane fills every gap between layers.
10. **Camera pops, layer jumps, fibres straightening.** The angle is the same in every inside shot, and the fibres part continuously, keyed every 2 frames through the stop.
11. **Static hold.** The bullet keeps decelerating until about frame 952, then holds 0.9 s before the cut out.
12. **Hand sinking in, arm in the shelf, face hidden.** Both hands are placed on her belly with `place_hand` and settled outward until they touch without going in. No hand reaches the shelf. The reaction camera is slightly low, so her lowered face is seen.
13. **Camera jump, doll eyes, no payoff, static ending.** The ending (1147–1273) is one continuous shot with no cut:
    - she checks her palm (nothing on it) and looks at the hole;
    - she straightens, breathes out, looks up and nods twice;
    - she pats her belly.

    The eyelids are relaxed rather than staring, the gaze follows what she looks at, and she blinks. The camera keeps pushing in slowly.

Logo: DA KRAS FILMS is on the box she holds (shot A) and on a box on the shelf behind her, which shows in D and the ending (over 4 s). Both are flat to camera and about 20 % of frame width.

## Checks (on the package)
- `clip_scan`: no bad ranges.
- `audit_hands`: 0 hand-in-hand, 0 hand-in-body, 0 hand-in-clothes, 0 hand-in-other, 0 wrist bends.
- `body_prop_cross`: only her left forearm grazes the underside of the held box (5 points, frames 1–89). The hand under the box hides it from the camera.
- `limb_check` ARMBODY: every flag is the `upperarm01` shoulder-joint segment inside the shoulder mass, the same rig false positive probed in v011.
- `qa_check`: every flag is expected:
  - CAMJUMP: the 4 hard cuts.
  - EMPTY: the window and inside shots, which have no character by design.
  - FILL and ROLL: the inside set, which has no horizon; skin is at the top of the frame.
  - PROPMOVE: the flying bullet and the glass shards.

## Known issues
- In the window shot the street outside reads as a dark grey through the glass. The crack is the subject.
- The stocker and his carton were removed from the store: in the long aisle view the carton crossed his chest.
- No full-resolution frame was rendered here, per the studio rule.
