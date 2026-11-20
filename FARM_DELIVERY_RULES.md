# Seldom — farm delivery rules (MANDATORY for every film, every part)

1. ONE render job per part. Never shot by shot.
   - Root has MASTER.blend; scene "MASTER" sequences all shots (Scene strips linked from //shots/Sxx.blend) in VO order.
   - User renders: MASTER.blend, scene MASTER, frames 1–N. Output //frames/.
2. Delivery = several NORMAL, INDEPENDENT .zip files, each < 300 MB.
   - Each zip opens alone with Windows "Extract All".
   - User extracts all zips into ONE folder, uploads that folder to RenderStreet.
   - NEVER: split archives, .zip.part00, .z01, .7z.001, 7-Zip volumes, or anything needing a command or extra software.
3. Test before sending: fresh plain unzip of all zips → open MASTER.blend → render 3 frames (start/mid/end).
4. Settings: 2560x1440, 24 fps, Cycles 64 spp adaptive + OIDN, motion blur, textures 2K max, no burned-in cards or captions.
5. Send with a one-line note: "Extract all zips into ONE folder → upload the folder → render MASTER.blend, scene MASTER, frames 1–N."
6. Also send the CapCut shot list (.txt + .csv).
7. MASTER.blend colour management MUST copy the shots exactly (view transform, look, display, exposure, gamma, sequencer colourspace). Verify: MASTER frame vs shot rendered at 100% then downscaled — pixel diff ~0.
8. MASTER scene MUST have a camera set (scene.camera), even though the sequencer drives the render. RenderStreet rejects files without one.
