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
13. **Every action needs contact + reaction.** A slam must land ON something, and that thing
    must react (objects jump, a burst, a shake, a bystander flinches). Arms swinging in mid-air
    read as nothing. Hammers hit something and spark. Window fitting needs the empty frame, then the pop.
14. **Backgrounds must never look alive.** Big flat or ambiguous shapes (building walls,
    roofs) sliding behind a moving camera read as moving objects. Put sky or clearly readable
    buildings behind the subject, or keep the camera still relative to them.
15. **No foreground slabs.** Wings, walls or table edges pointing at the camera become huge
    shapeless blocks. Frame around them (shoot the nose section, go higher).
16. **Props must read as what they are.** A scaffold without rails and braces looked like a
    table. If a prop could be mistaken for something else, add its defining details.
17. **Characters can't be behind geometry** that's taller than their waist (counters, tables,
    seat backs), or they vanish. Put them in front, or lower the geometry (`desk({top})`).
18. **Check the END frame of every camera move.** Pull-backs and pans drifted off the subject
    in 4 shots. The u=0.9 preview frame must still show the subject.
19. **Wide shots of tiny things don't work in 9:16.** For "two sides" beats, use the split
    screen (`S.splitScreen()`) instead of an aerial.
20. **Review the delivered video at 4 fps** (dense contact sheets), not 1 fps. Motion problems
    (sliding backgrounds, missing contact) only show up in sequences.

## Episode scorecard
| Date | Project | Score | Best shot | Worst shot | Notes |
|---|---|---|---|---|---|
| 2026-11-05 | example (round-windows p1) | "lovely" | – | – | first fully animated episode |
| 2026-11-06 | example v2 | (pending) | – | 02, 11 (v1) | full self-review, 13 shots fixed, see example/03-review.md |

## Feedback log
- 2026-11-06 · example · "analyze it properly first… a lot of mistakes… hitting the table… the orange dark brown thing continuously moving, supposed to be a building" → rules 13–20, a full shot-by-shot review (example/03-review.md), v2 render.
- 2026-11-05 · example · "this video is like image or presentation rather than the video I
  shared" → rule 1. "no i want claude to do!" → rule 2. Then "lovely" on the animated version.
