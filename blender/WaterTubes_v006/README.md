# WaterTubes_v006: fixed and synced to your voiceover (READY TO RENDER)

This is Connect33's **WaterTubes_v005b** (branch `claude/connect33-water-tubes`, commit 4f6ede7). It is retimed so each story beat lands on its words in your recording `WaterTubes_v006_VO.mp3`.

Fixed (found by watching the moving preview):
- No hard sun-glint discs on the flood water.
- The camera stays clear of the tubes, the hedge and the porch posts. There is no skim along the water, and no giant blurred tube in front of the lens.
- He walks down off the porch on a clean path.
- Spray, rain and the flood ripples follow the retimed picture. Their geometry-node clocks are remapped (`pipeline/fix_scene_time.py`), so the slam spray fires when the water hits the tubes.

Director check: the full moving preview (every 5th frame) was watched start to finish, and the beat frames were checked in this synced file.

Render:
- Frames **1–1769** at 60 fps (29.5 s). Join the frames into a video at **60 fps**.
- Settings: `SETTINGS.md`. Credits: `CREDITS.md`.
