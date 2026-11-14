# Ch4–5 redo: render plan (14 replacement shots, 2961 frames, 5 workers)

Each patch replaces the shot with the same id in the delivered master `nvidia_ch45.blend`. It has **exactly** the
frame count of the shot it replaces and drops into the master timeline at the same in/out frames.

Each patch is a small self-contained `.blend`, built like the c5_17 patch: a `PATCH_<ID>` master scene plays the
baked shot scene(s) as sequencer strips, so colour and brightness go through the same path as the master. Settings:
AgX, plain house grade, Cycles 32 samples, adaptive 0.05, denoise, 1920×816, 24 fps, PNG frames. Everything is
packed and there are no external files.

c4_01 is the split screen. Its two halves are separate 960 px scenes placed left and right, with a 4 px dark divider
and the CHAPTER 4 card on top, using the same card and timing as the master. c5_01 carries the CHAPTER 5 card, also
with the same timing. The delivered `nvidia_ch45_title_overlay.mov` still lines up on both.

## Shots, measured cost

The seconds per frame below were measured here on a 4-core CPU container. One full-quality middle frame was rendered
per patch, and the figure includes the time to load the patch.

| Shot | Patch file | Frames | Master in–out | s/frame | Est. hours | Content |
|---|---|---|---|---|---|---|
| c4_01 | `c4_01_patch.blend` | 249 | 1–249 | 116 | 8.0 | Split screen: man on the phone (night office) / reporter, CHAPTER 4 card |
| c4_03 | `c4_03_patch.blend` (2 parts) | 288 | 443–730 | 168 | 13.4 | Lobby, morning |
| c4_08 | `c4_08_patch.blend` | 114 | 1405–1518 | 63 | 2.0 | Binder, highlighter moving over a clause |
| c4_09 | `c4_09_patch.blend` | 297 | 1519–1815 | 72 | 5.9 | Printer feeding out a filing |
| c4_12 | `c4_12_patch.blend` | 196 | 2398–2593 | 139 | 7.6 | He walks out through the lobby glass doors at night |
| c4_14 | `c4_14_patch.blend` | 188 | 2785–2972 | 132 | 6.9 | Boardroom folder, CHAIR nameplate, turned chair |
| c4_18 | `c4_18_patch.blend` | 199 | 3571–3769 | 49 | 2.7 | Wall calendar, 8–11 crossed out, 12 circled, phone lights up |
| c5_01 | `c5_01_patch.blend` | 215 | 4103–4317 | 200 | 11.9 | Interview room + CHAPTER 5 card |
| c5_04 | `c5_04_patch.blend` | 155 | 4775–4929 | 169 | 7.3 | Interview room: passport slides away |
| c5_07 | `c5_07_patch.blend` | 248 | 5507–5754 | 157 | 10.8 | Interview room: empty chair, two-way mirror |
| c5_09 | `c5_09_patch.blend` | 136 | 5994–6129 | 178 | 6.7 | Interview room: passport slid back |
| c5_11 | `c5_11_patch.blend` | 197 | 6392–6588 | 157 | 8.6 | Container stacks at dusk, gantry crane |
| c5_14 | `c5_14_patch.blend` | 252 | 6984–7235 | 326 | 22.8 | Data hall, half the racks empty |
| c5_20 | `c5_20_patch.blend` | 227 | 8375–8601 | 95 | 6.0 | Port X-ray gate, truck pulls a container through |
| **total** | | **2961** | | | **≈121** | |

Every patch has a `<id>_patch.json` next to it with its frames, master in/out frames and sha256.
`patches.json` has all 14.

## Workers

The split is balanced by estimated render time (frames × s/frame), about 23–25 hours per worker on a 4-core CPU:

| Worker | Shots | Frames | Est. hours |
|---|---|---|---|
| **W0** (this session) | c5_14, c4_08 | 366 | 24.8 |
| **W1** | c4_03, c4_14, c4_18 | 675 | 23.0 |
| **W2** | c5_01, c5_04, c4_09 | 667 | 25.2 |
| **W3** | c5_07, c4_12, c5_20 | 671 | 24.4 |
| **W4** | c5_11, c4_01, c5_09 | 582 | 23.3 |

When a worker finishes early, it takes frames from the end of the busiest worker's last shot (`--first/--last`)
after agreeing on the range through the hub.

## How to render (every worker)

1. Check out `claude/nvidia-title-fix` and work in `nvidia_doc/`. You need Blender 5.x: either the Python module
   (`source ~/render_env/env.sh`, then `python`) or a `blender` binary (`blender -b -P scenes/render_redo.py -- <id>`
   also works, because the script reads its arguments from `sys.argv`).
2. W1 only: join the lobby patch first and check it:

       cd out/deliver/ch45_redo && cat c4_03_patch.blend.part* > c4_03_patch.blend && sha256sum -c c4_03_patch.blend.sha256

3. For each of your shots, run until it prints `DONE`:

       python scenes/render_redo.py <id>        # renders the frames not on disk yet, stops before 25 min

   Run it in a loop (`until python scenes/render_redo.py <id> | grep -q DONE; do :; done`) or once per turn.
   Frames go to `out/ch45_redo_render/<id>/f_NNNNN.png`. A frame is renamed into place only when it is complete,
   so stopping at any time is safe.
4. When all the frames exist, the same command writes `out/ch45_redo_render/<id>_redo.mp4`
   (H.264, CRF 16, yuv420p, 24 fps, no audio). Check its frame count matches the table:
   `ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 <file>`.
5. Commit each MP4 to **your own branch** and push it (MP4s only, never the PNG frames). Report the shot id, the
   frame count and the commit to the hub.

Any Blender 5.x can also render a patch directly: `blender -b <id>_patch.blend -a` writes frames to `//render/`.
