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
21. **The key action shot must be close.** The slam only worked once the boss filled about 60% of
    the frame (camera about 2.5-3 units away). Crowd shots need people at least 1/5 of the frame height.
    If an action is the point of the line, get close enough to feel it.
22. **Anatomy must be complete and correct (YouTube quality bar).** Never fake a crouch by sinking
    a character into the floor or hide legs with `sit` unless something really covers them. Use
    `kneel: 1` (one knee down) and `seat: 1` (sitting, knees bent). Every limb must exist and connect.
23. **Hands touch what they act on.** Use `aimR` / `aimL` with the world point (the vent, the paddle
    grip, the board). A held item's tip lands on the target. Arms swinging at fixed angles near an
    object read as fake.
24. **Props that cross 3D geometry are 3D, not drawn.** A paddle reaching past the raft tube into the
    water must be a 3D mesh (`alignBetween`), and the hands aim at its grip. Things drawn on the character
    canvas can't leave the character's plane.
25. **Zoom in during review.** Check every character at full resolution with crops (hands, feet, props):
    a 4 fps sheet hides missing legs and floating hands.
26. **Style: the user prefers the hand-drawn 2D illustrated look** (realistic proportions, detailed faces,
    ink outlines, dark palette) over the 3D toy look for horror and true crime. Use `Person` + `S.ink()`.
27. **More scenes, real sequences.** About 2 s per shot (39 shots in 78 s). Big moments get 3–4 shots
    (the arrest: police arrive → take cover → smash → rush → taser → kneel under flashlights). "Lame" means too few
    angles and actions.
28. **Hair that wraps the jaw reads as a beard** (bob haircut). Keep hair above the jawline.
29. **Analyse a reference at 2 fps with timestamps, full resolution, the WHOLE video.** For every shot
    write exactly what happens: who sits where (window vs aisle seat, the empty seat next to the victim),
    what the hands hold, the camera angle (from above, low side, behind), the action from start to end. Say
    plainly what a gore shot shows, then pick its clean replacement. A 1 fps low-res scan got 4 shots wrong.
30. **Story details carry the scene.** The empty seat next to the sleeping victim IS the setup; the hook shot
    is repeated at the end (loop). Missing these is a bad analysis, not a detail.
31. **"Copy the reference" means 100%: same shots, framing, action and blood.** Don't swap scenes for
    softer ones on your own. The only exception for real cases: never draw a real victim's body parts or
    mutilation; keep the same shot and put them out of frame or under the badge. Say so once, then build.
32. **No captions when the reference has none** (`--no-captions`). Merge narration into few TTS lines
    (several `[NN]` markers per line): every TTS line adds ~0.9 s of silence.
20. **Review the delivered video at 4 fps** (dense contact sheets), not 1 fps. Motion problems
    (sliding backgrounds, missing contact) only show up in sequences.

## Episode scorecard
| Date | Project | Score | Best shot | Worst shot | Notes |
|---|---|---|---|---|---|
| 2026-11-05 | example (round-windows p1) | "lovely" | – | – | first fully animated episode |
| 2026-11-06 | example v2 | (pending) | – | 02, 11 (v1) | full self-review, 13 shots fixed, see example/03-review.md |

## Feedback log
- 2026-11-10 · bus v3 · "did I ask you to censor or 100% as the reference?" → rule 31: same shots + blood, only the real victim's body parts kept off-screen. Rule 32.
- 2026-11-10 · bus v3 test · "your analysis is very poor… he's eating a heart… the person is sitting in the corner seat, not where the criminal sits" → rules 29–30, plan.md redone from a 2 fps timestamped pass.
- 2026-11-09 · bus 2008 · "I like this [illustrated] style… the one rendering is lame, not a lot of scenes, even the arrest" → rules 26–28, people.js, ink outlines, v2 with 39 scenes.
- 2026-11-08 · alcatraz test · "we get everything correct… the hand and digging the prison, the leg is not there" → rules 22–25. Kneel/seat poses, aimed hands and 3D paddles added to the engine; the test was rebuilt.
- 2026-11-06 · example · "analyze it properly first… a lot of mistakes… hitting the table… the orange dark brown thing continuously moving, supposed to be a building" → rules 13–20, a full shot-by-shot review (example/03-review.md), v2 render.
- 2026-11-05 · example · "this video is like image or presentation rather than the video I
  shared" → rule 1. "no i want claude to do!" → rule 2. Then "lovely" on the animated version.
