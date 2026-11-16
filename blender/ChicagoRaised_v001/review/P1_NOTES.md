# B27 ChicagoRaised: Phase 1 checkpoint notes

- **Plan:** `PLAN.md` has 22 shots in the reference order (`briefs/batch2/B27_ChicagoRaised_reference_1fps.jpg`, 37 s), timed to the reference seconds.
- **Still sheets:** `review/P1_sheet_3perShot_S01-S11.jpg` and `review/P1_sheet_3perShot_S12-S22.jpg` show the first, middle and last frame of every shot. They are 540×960, Cycles 8 spp + OIDN, after the anim_look pass, on the reference timing. Each label is the shot plus its film frame.
- **Contacts:** the summary is `review/body_prop_cross_summary.txt` (raw JSON is in the same folder).
- **Build:** `scripts/01_chars.py` → `02_sets.py` → `03_anim.py` → `pipeline/anim_look.py --no-sky` → `04_post_look.py`. A full rebuild takes about 5 min.
- **Phase 2:** `03_anim.py` takes a timing JSON of VO seconds per shot. Every action is keyed at 1× from its shot start. The S1–S7 crank crews run one continuous real-time cycle (one turn per 2 s), so any VO length just trims it. Nothing is stretched.

## Cast and sets
- **Characters:** 12 MPFB characters re-used from our packages, re-dressed in solid non-skin colours. All have the eye fix, the opened elbow IK limit, YXZ wrist limits with free twist, and hand limits. The horse is the rigged quadruped from WW1Assassination.
- **Hero building:** CC-BY Victorian corner block, recoloured cream, with blue curtain-glass windows. It rides on an empty: 1.6 m up at S1, rising 3 cm/s while cranking, 2.3 m in S8 and 2.85 m from S10 on.
- **Jacks:** 7 red cast-iron jacks under timber needles, each with a windlass crank. The two-handed grip bar sweeps a 0.12 m circle at waist height. The windlasses are removed from S8 on.
- **Cribbing and foundation:** cribbing stacks are crisscross timbers, keyed per shot to what fits under the needles. The brick foundation is built course by course.
- **Logo (1 placement):** DA KRAS FILMS (dark) on the shop sign of the hero facade. It is readable in S2, S9 and S13 and fully inside the frame wherever it shows. S10 and S14 were reframed so the logo is never cut by the frame edge.

## Fixed during P1 (found on my own 3-frame sheets)
- **Workers seen from behind:** all crank cameras moved to the building side, low and in clear lines under the needles, so faces read in S1, S4, S5 and S7.
- **Skin-coloured overalls:** the brown, rust, tan and khaki overalls read as naked bodies. They are now blue, dark green, grey, navy, slate, olive and denim.
- **Mis-placed props:** Blender 5's `transform_apply` defaults also applied location and rotation, which put the logo plane on the square floor, the lap book 300 m away and the bridge struts out of place. The lib now applies scale only.
- **Logo cut by the frame edge:** fixed in S3, S10 and S14.
- **S3:** a worker's body merged behind the Foreman's shoulder. The camera moved so the unmanned centre jack is behind him.
- **S8:** the camera had a jack in the lens. W2 is now under the building, pushing the timber toward the street, so his face reads from the street side.
- **S11:** the Mason was squatting with his back to camera. He now works from behind the wall, facing camera. A parked-rig key leak raised his hands at the cut; keys now end on the cut, the same fix as in S8 and S19.
- **S19:** the cough hand covered the face. It is now a palm toward the chest and a hand on the knee, with nothing at the face.
- **Flood street:** the water read as sand after anim_look (roughness 0.35). The post-look step restores dark glossy muddy water at specular 0.05.
- **Swamp:** rebuilt as mud/grass ground with teal pools and Geometry Nodes reed clumps (no blob trees).
- **Town:** now brick blocks plus clapboard houses with gable roofs; the smoke balls are gone.
- **Horse:** it was hidden in the source file; it is now visible.

## Known issues / unsure (please advise)
1. **Crank grips (S1, S2, S4, S5, S7): still crossing.** `body_prop_cross` reports the palm base (metacarpals 1/3/4) intersecting the 2 cm grip bar on every sampled frame, about 40–50 edges per hand. That is a deep palm overlap, not just a surface touch, and it is the main open contact fault. At 540 px it reads as hands on the bar. Plan: before Phase 2, try once more by setting the palm 1.5 cm further off the bar and closing the fingers onto it (wrap). If it is still not clean, re-stage simpler (LESSONS §2.15): frame the grip out in S1, and keep the hands small in the wide row shots.
2. **S6 seated contacts:** her thighs and spine sit into the armchair cushion and back, and the fingertips press 2–5 mm into the lap book. It reads as sitting and resting. I raised the seat 3 cm, sat her upright and lifted the book 3 cm; the crossings remain as cushion contact.
3. **S8:** the fingertips of the flat palms touch or press into the top of the timber while pushing. The hands are 1.8 cm above it; the curled fingertips still dip in.
4. **S11 first frame:** the brick is still descending and the right palm is not yet on it.
5. **The jacks' mechanism is plausible, not historical.** The real 1850s jacks were turned with iron bars. The windlass crank matches the reference (red crank jacks at waist height). Is that OK?
6. **S16 town and the flood-street Victorian houses are plain** (flat-painted, low detail). I can add clapboard texture and more variation in Phase 2 if the time allows.
7. **S22:** the river reflects a bright cyan sky, and the embankments read near-white in the sun. It still reads as a modern skyline with old blocks in front, with no text or logos on any tower.
8. **Faces:** the Mason (CaveRescue DiverC donor) has dark sleeve textures on his forearms that read as long work gloves. The Lady's head turn toward the window in S6 is small.
9. **Blend size:** the character file alone is 77 MB compressed, so the package will need texture down-sizing (1k) in Phase 2 to stay under 95 MB.
