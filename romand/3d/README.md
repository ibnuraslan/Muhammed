# Romand film: 3D kit (Seldom style v2)

Blender 5.2 Cycles, CPU. This kit builds on the approved look-test pipeline (`thumbnails_am/scenes/style_yellow.py` and
`crew.py` on branch `claude/thumbs-antwerp-mummy`) and the `antwerp_heist/3d/lib` library it uses (branch `claude/antwerp-heist`).

```bash
export ANTWERP3D=<checkout of claude/antwerp-heist>/antwerp_heist/3d
export AM_SCENES=<checkout of claude/thumbs-antwerp-mummy>/thumbnails_am/scenes
# (or SCRATCH=<dir> holding wt_antwerp/ and am/ checkouts)
OUT=/tmp/sb ./run_sb.sh sb_p1.py                 # P1 storyboard key frames, one Blender process per shot
SET=FOR OUT=/tmp/for.png blender -b --python set_sheet.py   # one establishing frame of a reusable set
KIT=<kit_v1 dir> RAW=/tmp/sb python3 sb_post.py 1           # overlays + contact sheet + PDF -> romand/review/p1/
```

| File | What it is |
|---|---|
| `rk.py` | Core: scene setup, palette (neutral greys; the yellow comes from the light), radial fade to the void, the faceless pale-clay mannequin (`person`: CC-BY "Eric Rigged 001" rig, clay clothes shells, blank egg head, poses incl. walk, carry, sit, car seat, bow, boot), the amber look (`look`: overhead fill + low moon, cool key + warm rim light-linked to the figures only), the red accent spot, camera helpers, house grade, luma check (`render_to_luma`: exposure trimmed so the mean luma lands at ~13). |
| `rprops.py` | Props: the Romand car (`car405`: Sketchfab CC-BY "1994 Peugeot 405 GLX (facelift version)" by Mehrdad995GTa, windows cut to glass, boot lid on a hinge, simple interior), pines and bare trees, gable houses, apartment/office blocks, furniture, TV, shelves, diploma frame, children's boots, banknotes, the RED accent props (nylon cord, tear-gas can), doctor's bag, flags, candles, explainer pawns and model house, fake light beams. |
| `rsets.py` | The reusable dioramas: FOR forest road + car, FTB phantom country house + dinner table, PAR Paris street, HPM the house in Prévessin-Moëns, HPI hallway, CLV the parents' house by the lake + garden table, WHO headquarters, UNI Lyon faculty + diploma wall, EXP explainer slab, CAF café, LIB library, HOT airport hotel, CRT assize court, PRI prison, ABB Fontgombault abbey. |
| `sb_p1.py` | Part 1 storyboard shots (one function per 3D shot). |
| `sb_post.py` | Kit overlays on each key frame, contact sheet, PDF. |
| `set_sheet.py` | One wide frame per set. |

Rules carried in code: faces never modelled (egg heads); one red accent per shot (`P['red']` + `accent()` spot);
mean luma ~12–14; no violence (the storyboard never poses a figure in an act of violence).

Credits (CC-BY 4.0): "Eric Rigged 001" (renderpeople), "1994 Peugeot 405 GLX (facelift version)" (Mehrdad995GTa).
Map outlines: Natural Earth 10m via world-atlas 2.0.2 (public domain / ISC), `romand/graphics/data/`.
