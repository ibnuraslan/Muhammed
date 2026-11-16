# TitanImplosion_v003 (B16): built to the voiceover (director fix round 1)

Changes from v002 (director notes; only f796–1481 re-rendered and spliced into the preview):
- f941–1170: the implosion bubbles are translucent (rim-lit, ~70 % transparent, mixed sizes), rising and fading.
- f800–940 (S10): the eye stays whole in frame; the camera looks along the nerve from the eye to the brain and pushes in.
- f1171–1481 (S13/S14): a clear slow orbit and push-in instead of a near-hold; eye and sub stay whole in frame.

The file is `TitanImplosion_v003_60fps.blend`; the VO file keeps its v002 name.


Connect B16's film. It was built straight to `TitanImplosion_v002_VO.mp3` (30.3 s), so every shot starts on its word:
`1 + round(seconds × 60)` from the transcription in `TitanImplosion_v002_VO.words.json`. No retime, and no character
animation is time-stretched (the man's actions are keyed in seconds from each shot start).

Story (respectful: no passenger is ever shown; the implosion is exterior only; no logo in a sad beat):
| Frames | Shot | VO | Picture |
|---|---|---|---|
| 1–114 | S01 | "The five passengers inside the Titan" | The sub descending in deep blue water, lamps on |
| 115–232 | S02 | "died instantly when the" | Close on the navy viewport dome and front ring |
| 233–305 | S03 | "submersible imploded." | The sub gliding over the seabed |
| 306–373 | S04 | "But just how" | A man on his sofa at home (logo box beside the sofa) |
| 374–443 | S05 | "instant was it?" | He leans in, hands sliding to his knees, head tilted |
| 444–576 | S07 | "Your brain takes roughly 100 milliseconds" | 3D brain; a pain pulse runs along a nerve to it |
| 577–668 | S08 | "to process pain," | The brain glows, pain sparks pop |
| 669–799 | S09 | "while your eyes can process visual information" | A beam of light flashes into an eye |
| 800–940 | S10 | "in around 13 milliseconds." | The pulse runs along the optic nerve to the brain |
| 941–1062 | S11 | "The Titan's implosion happened" | Exterior: the hull caves in, white flash, bubbles |
| 1063–1170 | S12 | "…less than a single millisecond," | The crushed hull sinks in the bubble cloud |
| 1171–1325 | S13 | "meaning the entire sub collapsed" | Eye vs mini sub: the sub crumples on "collapsed" while the eye's pulse has barely started |
| 1326–1482 | S14 | "…faster than the human brain could even register…" | Closer: the pulse has hardly moved |
| 1483–1600 | S15 | "For the passengers inside," | The man exhales, leans forward, looks down |
| 1601–1728 | S16 | "there was essentially no time to see it," | The sub in the deep; its lamps, dome glow and strobe go out |
| 1729–1825 | S17 | "feel it, or react." | Calm sunset ocean with the support ship |

Logo: one placement, the dark DA KRAS FILMS logo on the cardboard box in S04 (≈19 % frame width, flat to camera).

Review: `review/preview.mp4` (every 5th frame, 270×480, Cycles 4 samples, with the VO) rendered from this exact
package and watched page by page; checks in `review/checks_summary.json` and `review/bpc_masked_*.json`.

Rebuild: `scripts/02_build.py` (docstring) with `shots.json`. Settings: `SETTINGS.md`. Credits: `CREDITS.md`.
