# Batch 1 rebuild brief (applies to every rebuild chat)

You are rebuilding ONE batch 1 film FROM SCRATCH, to a premium standard. The client approved these three rebuilds; match their approach and quality and look at their scripts:
- `claude/rebuild01-ear-in-arm`, `blender/EarInArm_v015/`
- `claude/rebuild02-monkey-head`, `blender/MonkeyHeadTransplant_v015/`
- `claude/rebuild03-lego-in-nose`, `blender/LegoInNose_v013/`

## Read first
- `CLAUDE.md`
- `blender/LESSONS_LEARNED.md`. Read the end of it especially: the lesson on staging contact work so it can be reached.
- `blender/PRODUCTION_RULES.md`. Read the end of it especially: LOGO placement, and fast-render plus zero-error checks.
- `blender/STYLE_ANIMATED.md`. Read the end of it especially: the deep, rich COLOUR grade.
- `blender/briefs/<NN>_<Film>.md`
- your film's section of `blender/briefs/BATCH1_FAULTS_05-35.md` (every fault the client rejected)
- `blender/briefs/RECURRING_FAULTS.md`
- `blender/briefs/FIX_RECIPES.md` (R1–R9; ignore R10's cut-away)

Reuse the VO and timing from the latest package of your film. Find it on the `claude/connect<NN>-*` branch or in `blender/<Film>_v*/`.

## Creative direction
- ONE continuous camera, no cuts: a cinematic oner. Change scenes inside the move (push through an x-ray, a window, a dissolve-free whip).
- The camera travels close, so the key object fills about 1/3 of the frame at each story beat.
- A face is in frame in every wider moment. No torso-only or crotch-centred frames, and no static holds over 1 s.
- Deep, rich colour (AgX/Filmic high contrast, saturated sets, true primary props). Nothing plain or grey.
- The DA KRAS FILMS logo sits naturally in the scene, readable for at least 1.5 s.
- People: one model per character, real hair and faces, natural acting motion.
- CLOTHING (the client's #1 rejection): use REAL loose garment assets from the MPFB/MakeHuman community clothes library (files.makehumancommunity.org).
  - Separate tops and trousers with folds and volume away from the body, and the body hidden with delete groups.
  - Flatten the chest and crotch shape keys before dressing.
  - NEVER use shrinkwrapped or skin-tight body copies: they read as onesies, muscle suits or nudity.
  - Arms bent 15–30° with idle motion. A lying patient's whole body is under a loose drape (no neck blocks).
  - Bodies must be SOLID: never hollow inside clothes, gowns or drapes. Drapes and garments get solidify thickness and no open edges. No holes at trouser crotches. Check with close renders.

## Contact rules (the cause of most rejections)
- Stage every hand and tool contact so it can be reached with 1 cm or more of clearance from every body before animating.
- Run the hand/finger-vs-body, arm-vs-torso and tool-vs-hair audits on the BLOCKING pass. If they fail, change the staging, not the IK.
- Props are Child Of the hand bones and gripped properly. Objects rest ON surfaces. People sit and lie ON furniture.

## Hard rules
- Put the package in a new folder `blender/<Film>_v<next>/`. Push only to your outcome branch.
- No paid renders. Make one small preview per check: 270x480, every 5th frame, with the VO.
- Budget about $30. Plan once and don't explore endlessly.

## Self-QC
- Make frame pages with this command:
  ```
  ffmpeg -i preview.mp4 -vf "scale=270:480,drawtext=text='%{pts\:hms}':x=4:y=4:fontsize=18:fontcolor=yellow:box=1:boxcolor=black,tile=8x3" -vsync 0 p_%02d.jpg
  ```
- A fresh subagent gives a harsh PASS/FAIL on every page.
- Do at most 2 fix rounds.

## Delivery
- ALWAYS push `review/preview.mp4` after every check, pass or fail.
- Push the .blend only on PASS, or when the director relays client approval, and only with the "Render check: PASS" block in README.md.
- Report each push to the director (session_01XfwPSmLbHQF2WV66wM8mt5) via send_message.
