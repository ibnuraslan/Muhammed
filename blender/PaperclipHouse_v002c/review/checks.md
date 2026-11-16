# PaperclipHouse_v002c: checks on the packed file

All four checks were run on `PaperclipHouse_v002c_60fps.blend` exactly as committed (frames 1–2000).

| Check | Result |
|---|---|
| `body_prop_cross` (step 3, per shot with that shot's rigs; props: every P_* item and the kitchen counter) | **0 visible crossing frames in all 19 shots** |
| `clip_scan` (step 6) | **0 bad ranges** (no hand into hip, no body-to-body overlap) |
| `qa_check` (step 6, beats.json) | BACKHEAD 1, INSIDE 11, CAMJUMP 18, PROPMOVE 4: all explained below |
| `limb_check` (step 2) | ARMBODY 407 hits; none is a visible fault (explained below) |

## qa_check flags (none is a fault)
- **CAMJUMP 18:** the 18 hard cuts between the 19 shots.
- **PROPMOVE 4:** props repositioned across a hard cut for the next shot's layout. No prop moves inside a shot.
- **INSIDE 11** (frames 1561–1621): the camera sits inside the sky-blue dome of the explainer stage, by design.
- **BACKHEAD 1** (frame 121): the partner PenLady in ¾ back view; the hero faces the camera.

## limb_check
- **2-point hits (84):** the documented shoulder false positive.
- **3–6 point hits:** only on two kinds of arm, both close to the shoulder:
  - raised arms in the party (S08) and the house reveal (S28)
  - the handshake arm in S03, S05 and S21

  In every one of these frames the watched preview shows the upper arm outside the chest. The hits are the deltoid vertices that the checker classes as torso.
