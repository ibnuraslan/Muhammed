# Phase 2: Storyboard

Goal: a shot list where every shot is interesting on its own, the sequence is always
moving, and a viewer with the sound off still follows the story.

Inputs: `01-analysis.md`, `timings.txt`.
Outputs: `projects/<slug>/02-storyboard.md` (use `templates/storyboard.md`), and `[NN]`
markers inserted into `script.txt`.

## Cutting rhythm
- One shot every **0.8–2.5 s**. Aim for about 20–26 shots in 40 s (about 1.6 s average). Never above 3 s.
- Cut **on** a strong word (noun, number, verb, name) or at the start of a clause, never
  mid-name ("the clickety | clack line" is wrong).
- Quick bursts (0.6–1.0 s) on punchy short phrases ("his face | goes purple").
- Longer holds (2–2.5 s) only where something is happening: a takeoff, an orbit reveal, a slam.
- Check every shot length against `timings.txt`. A 0.5 s shot can't hold a complex action.

## Each shot must define
| Field | Example |
|---|---|
| id + time range + words | `07  10.2–11.3s  "He's the youngest engineer"` |
| set | office (existing) / railroad (new) |
| shot size | ECU, CU, MCU, MS, WS, EWS, aerial, POV, insert |
| camera move | push in, pull back, orbit L→R, crane up, track along, whip pan, handheld shake, crash zoom |
| subject action | hero hammers spike, boss walks in, train passes camera, paper spins in |
| emotion / pose | hero `eyes:'half', mouth:'smile'`; boss `anger 0→1, steam` |
| props / FX | confetti, steam, dust, heat shimmer, crack |
| why it's interesting | "low angle on the rail: the train rushes over the camera" |

Rule: **two things move in every shot**: the camera, plus at least one subject (a character,
vehicle, prop or particles).

## Shot vocabulary (mix these)
- **Establishing aerial / EWS:** crane down from the sky onto the set (start of a section).
- **Hero MS/MCU:** the character doing the action the line describes.
- **Reaction CU:** face fills about 40% of the frame. Use these for emotions (anger, smugness, sadness).
- **Talking CU:** for every character voice line, the speaker with `talk: 1`, and a slight push in.
- **Insert / ECU:** an object detail (window, rail gap, blueprint, newspaper headline).
- **Low-angle power shot:** boss or rival towering over the camera.
- **Tracking shot:** the camera runs alongside a train, plane or crowd.
- **POV / impossible:** riding on a wheel, flying through a window, looking up from under a rail.
- **Metaphor shot:** a map, chart, money or clock (a stylised world, see shot 20 in the example).

## Sequence rules
- Shot 1 is the hook, the strongest image in the video. It shows the strange action
  from the first line, big and clear, already in motion on frame 1. No slow establishing shots.
- Never put two consecutive shots on the same set **and** the same angle/size. Alternate wide, close, wide.
- Have a character close-up at least every 4 shots. Faces hold attention.
- Keep screen direction: if the hero's train moves left→right, keep it left→right.
- At least **3 wow shots** from the crazy list, spread out (around 25%, 50% and 75% of the video).
- The final shot (cliffhanger): a slow ominous push in, something starting to change (a crack,
  heat shimmer, a light flicker), a tiny shake. The last frame holds about 0.5 s after the last word.
- Part 2: open with a fast 2–3 shot recap that mirrors part 1's key shots, then the twist.

## Caption-safe framing
Captions sit at about 62–78% of the frame height. In close-ups, keep eyes and mouth above about 58%.
Don't put the key action in the caption band.

## Variety check (fill this in at the bottom of the storyboard)
- Shot sizes used: count of each. No size above 40%.
- Sets used, and shots per set.
- Wow shots: list ids.
- Close-ups: list ids, roughly 4 shots apart?
- Every voice line covered by a talking close-up?
- Sound-off test: read only the "subject action" column. Does it tell the story?

## Then mark the script
Insert `[NN]` before the word each shot starts on, in `script.txt` (the words themselves must
stay exactly as spoken). Run `python3 make_short.py projects/<slug> --timings-only` and compare
the reported shot starts with your plan. Adjust if any shot is under 0.6 s or over 3 s.
