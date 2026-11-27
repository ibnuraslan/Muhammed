# Seldom style v2: approved by the user (from the next film onward)

Reference: style_study_v2/ on branch claude/style-study-v2 (one creator's 3D true-crime diorama style). The approved look test is thumbnails_am/review/style_yellow_v3_red_1080.jpg and live_test/ on branch claude/thumbs-antwerp-mummy.

## Look
- 3D dioramas floating in a black void, mostly high 3/4 overhead wides, very dark (mean luma about 12–14).
- The world is tinted ONE colour: ours is Seldom YELLOW (warm amber-gold, brown-black shadows, pure #E3FF00 only at the hottest highlights).
- Faceless pale-cream clay mannequins (blank egg heads) in pale-clay clothing (jackets, trousers, caps, gloves). They are lit by a neutral cool-white key plus a warm rim so they pop against the yellow world.
- ONE contrast accent on key evidence: red (white is also fine).
- Wet glossy floors, a heavy vignette, set edges fading into black.
- Overlays done in post: a top-centre date stamp (Oswald) and a top-left boxed section tag.

## Animation
- Fully animated: people walk, carry, sit and point, using motion capture with foot planting, no sliding and collision checks.
- HARD RULE: 0 clipping. No bags, limbs or props passing through doors, bodies or other objects. Check every frame, not just samples.

## Render (budget mode until the channel is monetised)
- Cycles, 960x540, 16 spp, adaptive sampling, OIDN, about 4 bounces, no volumes (fake fog in compositor).
- Upscale to 1080p (lanczos plus a light unsharp); overlays in post.
- Measured: about 9 s/frame on a 4-core cloud CPU. Upgrade to a better render after monetisation.
- Farm option: $39/month plan (4 workers, 80 vCores, up to 1080p).
