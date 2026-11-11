# EarInArm: changes since checkpoint B

## Fixes
- **Chair rig:** the chair parts were parented to a stale tilt matrix, so the whole seat sat 0.55 m too high and the patient was sunk into it. Fixed: seat top at 0.55 m, with the patient seated on it.
- **Look:** AgX High Contrast, exposure −1.9, and the studio cyclorama emission was lowered. Blocking was washed out.
- **Ears:**
  - All ear copies now have their front facing out: on the tray, in the pocket, in the forceps and in the tissue studio.
  - The old left ear is collapsed to a small stump by an `EarGone` shape key. Blocking showed the full old ear under the new one.
  - The grafted ear has a darker skin tint to match the head.
- **Bandage:** the halo-like wrap ring is gone. It's now a gauze pad with two tape strips.

## Acting and staging
- **Beat 1 shock:** the right hand flies to his mouth, and the left hand rises from below to the dressing, so the arm no longer covers his face.
- **Surgeon:**
  - For the arm work he stands behind the arm (+Y), and for the head work behind the headrest, so the camera's macro passes never enter his body.
  - His mask sits over his nose and mouth (it was over his eyes).
  - On the tray, his hands come in only after the camera has pulled out of the block. They lift away at 8.8–9.3 s to show the finished ear.
- **Nurse:** walks around the front of the chair instead of through the head shot.
- **Studio A glove:** trimmed to the hand, smaller, and kept at the frame edge until it cuts the block.
- **Vessels and stitches:**
  - The join vessels are thin, curved, and in front of the ear (by the ear canal), and they hide once stitching starts.
  - The stitches run along the ear's front edge. The needle holder now points its needle at each stitch.
- **Arm board:** hidden while the patient sits upright (beats 1 and 9).

## Camera
- **DOF:** f-stop is keyed from camera–aim distance, so macros stay sharp: f/2.8 on wides, up to f/22 at 1–2 cm.
- **Fly-throughs:** shortened. The chest dive goes beside the surgeon's hand, not through it. The rib-studio membrane is a translucent sheet the camera actually passes through. The tissue-studio membrane is lit and starts 2.5 cm away, not inside the clip range.
- **Tray macro:** the camera comes out of the block from above, with a narrow lens so the block fills the frame on both sides of the jump.

## Audit
- The camera-inside test now flags frames where the first surface on the view axis is hit from behind.
- Foot hover is only flagged on planted feet.
