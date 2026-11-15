# ToucanBeak v008: built to the client VO timing (Connect28)

- **File:** `ToucanBeak_v008_60fps.blend`, packed, normal git file. Frames **1–1932** (32.2 s) at 60 fps.
- **Picture:** the v007d picture the director approved, re-timed so each beat starts exactly on the director's VO frame. The intent is a 1:1 sync with no warp. `beats.json` has the new frames, and each beat's v007d frame is kept as `frame_v007`.

| Beat | Frame | Content |
|---|---|---|
| 1 | 1 | Toucan on the branch |
| 2 | 114 | The strike (stick whooshes in, no hand) |
| 3 | 266 | Can't eat (the fig) |
| 4 | 512 | Clinic, the scan |
| 5 | 625 | The vet at the monitor |
| 6 | 780 | Screen close-up: stump, wireframe, fill |
| 7 | 913 | Weighing the solid beak (913–1001), then back on the monitor (1002–1158): the heavy-beak demo bird's head is dragged down |
| 8 | 1159 | A long slow push on the printer building the beak (1159–1368), then the hollow cut-in (1369–1393) |
| 9 | 1394 | Lining the beak up on the stump (trimmed to 1.8 s) |
| 10 | 1501 | Gluing, then a cut to the wide shot of both vets |
| 11 | 1634 | The garden ending (to 1932) |

## How it was done
The v007 picture goes through a single edit list applied to every keyframe (`V008 RE-TIME` in `ToucanBeak_v001/scripts/04_anim.py`).

- **Clean cuts:** beat 9 and beat 10 are trimmed with clean cuts, not sped up.
- **Mostly 1:1:** most sections run 1:1 or within ±16%.
- **Two stretches:**
  - The vet-at-the-monitor shot (beat 5) is stretched 1.6×. It is a near-static medium shot.
  - The printer push is stretched 2.8×. This is the requested slow push; only the camera and the machine move.
- **No slow motion of acting:** no character action is played in slow motion.
- **Beat 7 extra time:** the director suggested the vet holding the solid beak to the toucan's head. That was tried twice. It put a hand on the bird's head and blocked the camera behind VetA's arm. Following the simplify rule, the extra 2.6 s is instead the on-monitor demo: the heavy beak drags the bird's head down, matching the VO "it would drag the bird's head down".

## Files
- **Preview:** `review/preview.mp4`, rendered from this exact package.
- **QA:** `review/qa_v008.json`.

## Checks on the packed file
- **Size:** 94.73 MB.
- **Factory-startup open:** 0 unpacked images, 0 libraries, frames 1–1932 at 60 fps.
- **Check still:** `package_check_lowres.jpg`, frame 1085 (beat 7, the head dragged down).
- **qa_check:**
  - CAMJUMP 12: single-frame intended cuts only (505, 623, 719, 858, 912, 1002, 1159, 1369, 1394, 1501, 1587, 1634).
  - 0: CLAW, FAN, HOVER, FACEPRESS, BACKHEAD, ROLL.
  - PROPMOVE / EMPTY / FILL / INSIDE: the same causes as v007 (intended moves; qa counts only human rigs; the non-rendering dust volume).
