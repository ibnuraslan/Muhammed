# B16 TitanImplosion: Phase 1 plan

**Reference:** old style (a presenter at a mic, flat graphics on a blue grid, a flat sub icon). Per the brief and
`CONNECT_BRIEF_v2.md` we take only the story and the beat order and rebuild every scene in our current look
(bright 3D, real sets). The reference order is kept exactly: **sub in the deep → the "you might be wondering" moment
→ brain needs 100 ms for pain → eyes need 13 ms to see → the Titan implodes → eye-vs-sub comparison (the signal has
barely left the eye) → "truly an instant" → lights out for the victims.**

**Respect rules for a real disaster:** no passengers are ever shown, inside or out. The sub is a generic Titan-like
carbon/titanium submersible (no name, no text, no real logos). The implosion is **exterior only**: the hull caves in,
a short white flash, a bubble cloud; no debris of people, nothing gory. No logo in any sad beat.

The presenter is replaced by **one generic man ("you") on his sofa at home**, so the "if you were wondering" beat has
a real person acting it. He never touches a prop: his hands rest on his thighs the whole time (no grips at all).

Film timeline is provisional (clips 1.3× the expected beat length, 2691 frames). In Phase 2 `shots.json` gets the VO
frames and `scripts/02_build.py` is re-run: every action is keyed relative to its shot start at 1× speed, so trimming
to the VO needs no time-stretch.

| # | Beat / likely VO | Shot | Who / what, and what it physically does | Camera | Safe staging notes |
|---|---|---|---|---|---|
| 1 | "…told the five passengers of the Titan…" | **S01** 2.0 s | Sub descending through deep blue water, lamps on, props turning, marine snow | Wide 3/4 front, high, slow tilt down with the sub | Deep scene kept readable: blue gradient water, cool key + rim on the sub |
| | | **S02** 2.0 s | Close 3/4 on the viewport dome and front ring, lamps glowing | Slow lateral orbit + descend | Dome is opaque dark glass (no interior, no people) |
| 2 | "…passed away instantly from the implosion." | **S03** 2.0 s | Sub glides low over the seabed (sand, rocks), lamps on the sand | Low, near the seabed, tracking along | Nothing within 1 m of the lens |
| 3 | "And this is true. But if you were wondering…" | **S04** 2.0 s | Man on his sofa at home, watching TV (off screen), breathing; delivery box with **logo** beside the sofa | Wide-medium push-in from the TV side | **Logo placement #1** (dark logo on a cardboard box), flat to camera, ~19 % frame width, on screen 2 s |
| | "…just how instant they're talking about…" | **S05** 2.0 s | He leans forward, head tilts (wondering) | Medium, front, push-in | Hands stay on thighs (place_hand on ray-cast thigh top) |
| | "…let me explain." | **S06** 2.0 s | Close on his face; small head turn toward camera | Push-in close-up | Eyes: eye fix + camera catchlight |
| 4 | "It takes our brain 100 ms to process pain…" | **S07** 2.5 s | Clean 3D brain on the sky-blue gradient; a myelinated nerve runs in from lower left; a yellow signal pulse travels along it | Low 3/4, push-in | Anatomy colour-coded, glossy, no gore |
| | | **S08** 2.0 s | Pulse arrives; the brain glows warm and yellow pain sparks pop around it | Orbit around the brain | Sparks are stylised bolts (no text) |
| 5 | "…and it takes our eyes 13 ms to process visually." | **S09** 2.0 s | 3D eyeball; a beam of light flashes into the pupil; the eye turns slightly | 3/4 close | Beam is a thin glowing cone, apex at the pupil |
| | | **S10** 2.0 s | A signal pulse runs along the optic nerve to a brain | Wider, pans along the nerve | |
| 6 | "So when the Titan imploded, the high pressure caused…" | **S11** 2.0 s | Sub in the deep: hull caves in (shape key, 10 frames), white flash, bubble cloud bursts | Side 3/4, slow push | Exterior only, no people, short flash |
| | | **S12** 1.5 s | The crushed hull sinks slowly inside the bubble cloud | Reverse angle | No flying debris |
| 7 | "…the entire event to take less than one millisecond…" | **S13** 2.5 s | Comparison on the sky-blue backdrop: eye + optic nerve on the left, a small sub on the right; the sub crumples while the eye's pulse has barely started | Frontal, slow push-in | Same eye/sub models as S09–S11 (continuity) |
| | | **S14** 2.0 s | Closer: the pulse has moved only a few cm along the nerve; the crushed sub beside it | 3/4 close | |
| 8 | "…it was truly an instant." | **S15** 2.0 s | Man on the sofa lowers his eyes, quiet | Medium from the other side | No logo in frame (sad beat) |
| 9 | "Lights out for the victims." | **S16** 2.0 s | The sub in the deep; its lamps, dome glow and strobe go dark one by one | 3/4 front, slow push | Remains readable: blue water lit by the set key |
| | (end) | **S17** 2.0 s | Calm ocean at sunset, the support ship on the horizon, sun low | Slow push toward the ship | Respectful end card, no text |

**Logo:** one placement (S04, box beside the sofa). Every other beat is part of the tragedy, so no second placement.

**Risky shots and the simplest staging chosen**
- Victims: never shown. The sub stands for them; "lights out" is the sub's lamps going dark.
- Implosion: exterior only, a stylised cave-in plus a flash and bubbles. No interior, no debris field.
- Brain / eye timing: real 3D anatomy models (CC-BY) on the sky-blue gradient, with a travelling glow pulse instead of numbers or text.
- The man: no props in his hands at any time; seated pose with feet planted (IK) and hands resting on the thighs.
