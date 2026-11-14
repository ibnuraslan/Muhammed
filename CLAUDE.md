# Project notes for Claude

This repo holds a short-film studio: Blender packages of vertical Zack-D-style explainer films (1080×1920, 60 fps,
Cycles, one continuous camera, timed to the client's voiceover) that the client renders on RenderStreet.
Each render costs the client money, so a faulty file delivered = money lost.

**Before working on any film, read `blender/LESSONS_LEARNED.md`.** It lists every fault the client rejected,
the staging rules that avoid them, the mandatory checks, the review protocol and the 1–2 hour build pipeline.
Also read `blender/PRODUCTION_RULES.md`, `blender/STYLE_ANIMATED.md` and `blender/briefs/FINAL_PACKAGES.md`
(the source of truth for which package is READY or ON HOLD).

Non-negotiables:
- Never give the client a download link for a film you haven't watched as a moving preview start to finish
  (`blender/pipeline/preview.py` + `watch_pages.sh`), and send the preview MP4 with the link.
- Never approve from still sheets, scripts or a chat's self-report alone.
- Ask before long local renders. Never submit paid render jobs. Never ask for secrets in chat.
- Make changes in a new version folder (`<Film>_vNNN+1`) and keep the source version untouched.
- Blender: `/opt/blender/blender-5.2.2-linux-x64/blender` (headless, no GPU, so use Cycles for previews).
