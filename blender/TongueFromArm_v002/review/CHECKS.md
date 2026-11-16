# Checks on TongueFromArm_v002_60fps.blend (the exact package)

- **Preview:** `preview.mp4` = `pipeline/preview.py` every 5th frame (281 frames, 270×480, Cycles 4 spp + OIDN) from this file, joined with the VO at 12 fps; contact pages `p01`–`p06`. Watched every page and the MP4 start to finish.
- **qa_check** (step 6, beats.json): only `CAMJUMP` ×18 = the 18 intended hard cuts. No EMPTY / FILL / INSIDE / BACKHEAD / HOVER / CLAW / FACEPRESS / PROPMOVE / ATTACH / ROLL / FAN.
- **clip_scan** (step 6): `BAD_RANGES []`.
- **limb_check** (step 6): ARMBODY only, "arm inside own torso" for 2–6 points per frame on the two seated patients (shoulder/upper-arm points of arms resting at the sides). This is the known shoulder false positive; no arm visibly enters a body in the preview. No ARMBACK, no PROPHEAD.
- **body_prop_cross** (step 6, `body_prop_cross.json`, all chair / arm board / bed / blanket / sheet / pillow / table / door-frame props; counted only within the shot's own set):
  - OR (S01, S05, S13): her right little-fingertip rests on the chair arm (a few edges). Resting contact, no visible crossing.
  - Ward (S14–S19): her legs, hips and feet are under the blanket and sit a few cm into the mattress; her fingertips dip a few mm into the soft blanket top; the blanket's top edge starts at her waist. All of this is under or inside the opaque blanket. The preview shows no limb through the blanket or bed.
- **Package:** 81 MB, all images and the VO packed (factory-startup: 0 unpacked files), frames 1–1404, 60 fps, 1080×1920. `package_for_farm.py` flags "must be ONE camera": intentional, the batch-2 brief asks for hard cuts with one camera per shot via markers.
