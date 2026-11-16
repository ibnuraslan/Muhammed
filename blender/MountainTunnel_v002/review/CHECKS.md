# Checks on the packed MountainTunnel_v002_60fps.blend (frames 1–1991)

- **clip_scan** (step 6): BAD_RANGES [] (0).
- **body_prop_cross** (step 3, every Chisel_/Hammer_/Stretcher_ pole and slat): chisels 0, stretchers 0.
  Hammer: 1 edge per frame (metacarpal1.R = thumb base on the handle) in the 8 strike shots. Constant through the swing (grip contact, not a pass-through). Open item.
- **limb_check** (step 2): ARMBODY only, all "arm inside own torso (2–5 pts)" at upperarm points next to the shoulder, on every rig in every frame
  (also on parked rigs) = the known shoulder false positive (LESSONS s4).
- **qa_check** (step 6, run with the marker camera per frame; the stock script keeps the frame-1 camera for the whole film):
  - CAMJUMP 21 = the 21 intended hard cuts.
  - PROPMOVE = falling rock chips (1a/4b/4c/10b/10c) and the pebbles breaking off under her foot (5b): debris under gravity, no hand expected.
  - EMPTY = aerial/map shots (1b, 6a, 7b, 10a) and wide shots where the man is small (2a, 4a, 9a): intended.
  - INSIDE 18 / BACKHEAD 3 at the first frame of 5a/5b/13a: checked on the preview, cameras are in open air (ledge view, path behind the villagers walking away).
  - FAN 62 = V1's right hand at the park position (rig parked off-screen, hidden). Not on camera.
