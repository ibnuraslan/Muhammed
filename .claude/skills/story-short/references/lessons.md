# Lessons (read first, every time)

Everything learned from the user's feedback and from our own mistakes. These rules beat any
other instruction in the skill. Add new entries at the top of the log, and turn repeated issues
into rules.

## Rules
1. **Real animation only.** The user rejected zoom/pan over stills as "like an image or
   presentation". Every shot needs a moving camera **and** something moving in the scene.
2. **The user wants Claude to make everything:** no outside AI tools, paid services or asset
   downloads for the visuals. Build it in the engine.
3. **Match the reference format:** 1–3 word captions in the lower-middle, a cut every ~1.5 s,
   a narrator plus a character voice line, a cliffhanger ending.
4. **The vertical frame is narrow** (half-width ≈ 0.26 × distance at fov 50). Two things side by
   side need a lot of distance or a camera pan between them. Check in previews.
5. **Billboard characters get blocked** by anything in front of them (seat backs, table legs).
   Shoot across rows, not along them.
6. **No ACES tone mapping:** it washed the colours out. Keep `NoToneMapping` plus the encode boost.
7. **A one-platform scaffold reads as a table.** Use taller scaffolds or none.
8. **Tiny characters in wide aerials don't read.** Keep characters ≥ 1/4 of the frame height in most shots.
9. **Always preview before a full render** (27 s vs ~9 min).
10. **Edge TTS** (only when no voiceover is given) is flaky. Retries are built in. Valid
    voices: run `edge-tts --list-voices` (e.g. `en-US-DavisNeural` does NOT exist).
11. **The user's messages are short and casual.** Reply briefly, show the result, and ask one clear question.
12. **GitHub push** from the cloud session failed with 403 (no app access to
    `ibnuraslan/Muhammed`). Keep committing and remind the user. Don't loop on retries.

## Episode scorecard
| Date | Project | Score | Best shot | Worst shot | Notes |
|---|---|---|---|---|---|
| 2026-11-05 | example (round-windows p1) | "lovely" | – | – | first fully animated episode |

## Feedback log
- 2026-11-05 · example · "this video is like image or presentation rather than the video I
  shared" → rule 1. "no i want claude to do!" → rule 2. Then "lovely" on the animated version.
