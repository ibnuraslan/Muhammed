MARY CELESTE - PART 3 - RenderStreet package

Blender:     5.2.2 (built and tested with 5.2.2; any 5.2.x should open it)
Engine:      Cycles, CPU (GPU is fine: no CPU-only features are used)
Output:      2560 x 1440, 100%, 24 fps, PNG 16-bit RGB, written to //../frames/<shot>/<shot>_####.png
Sampling:    64 max samples, adaptive (threshold 0.03), OpenImageDenoise, motion blur on (shutter 0.4)
Grade:       in the compositor of each .blend (bloom, cinematic look, vignette) - leave "Compositing" on
Frames:      clean - no cards, captions or labels (they are added in CapCut)

Layout:      shots/<shot>.blend    one scene per shot, camera and frame range set
             textures/             shared images, relative paths (//../textures/...); fonts packed
             SHOTLIST.csv / .txt   timings for the edit
Nothing to bake: people are live rigs with keyed poses, ships and props are keyed, bending ropes/lines are shape keys,
the FFT sea's clock is keyed. No simulation caches. Render each .blend's full frame range as set (start 1, end below).

Measured on this 4-core CPU box at these exact settings: about 11.9 min per frame at 2560x1440.
Total 3356 frames, about 666 CPU-box hours; a 32+ core farm node is roughly 6-10x faster.

Shot     frames   seconds
p3_01    1-119    4.96
p3_02    1-50     2.08
p3_03    1-66     2.75
p3_04    1-47     1.96
p3_05    1-75     3.12
p3_06    1-55     2.29
p3_07    1-41     1.71
p3_08    1-91     3.79
p3_09    1-33     1.38
p3_10    1-44     1.83
p3_11    1-48     2.00
p3_12    1-53     2.21
p3_13    1-53     2.21
p3_14    1-61     2.54
p3_15    1-42     1.75
p3_16    1-95     3.96
p3_17    1-68     2.83
p3_18    1-116    4.83
p3_19    1-70     2.92
p3_20    1-109    4.54
p3_21    1-31     1.29
p3_22    1-53     2.21
p3_23    1-94     3.92
p3_24    1-115    4.79
p3_25    1-111    4.62
p3_26    1-153    6.38
p3_27    1-49     2.04
p3_28    1-58     2.42
p3_29    1-61     2.54
p3_29b   1-94     3.92
p3_30    1-62     2.58
p3_31    1-143    5.96
p3_32    1-64     2.67
p3_33    1-89     3.71
p3_34    1-88     3.67
p3_35    1-90     3.75
p3_36    1-50     2.08
p3_37    1-81     3.38
p3_38    1-86     3.58
p3_39    1-68     2.83
p3_40    1-81     3.38
p3_41    1-63     2.62
p3_42    1-126    5.25
p3_43    1-110    4.58

Total: 3356 frames, 139.83 s
