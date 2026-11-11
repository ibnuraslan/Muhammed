# Checkpoint C: polish notes

Sheets: `C_polish_0p2s_part0..3.jpg` (0.2 s, 270×480, 8 samples). Audit: `C_audit.txt` (`scripts/audit.py`, every 2nd frame).

## Audit (every 2nd frame, 765 frames)
- Shoe soles vs floor (hover/sink): 0 problems. His sole offset fixed (was −2.7 cm).
- Seat contact (ray test, body inside chair / gap over seat): 0 problems. Her hips used to lift off / push into the backrest during the recoil; the recoil is now spine + head only.
- Fingers through the table top: 0.
- Bullet under the floor: 0.
- Camera inside solid geometry: 1 frame (f257), the camera grazing the edge of the drywall hole on the fly-through. Not visible in the stills.

## Changed since B
- Chairs faced backwards (backrest toward the table). Fixed: all five chairs.
- Clothes: plain MakeHuman suits with no logo print (striped blouse + skirt; jacket + striped shirt + jeans).
- Floor/walls: the concrete foundation slab was covering the room floor (mottled look). Fixed; box-projected textures; brighter warm room, exposure −0.45.
- Wall break-through rebuilt: camera follows the bullet through a real hole in the siding (splinters lit by the leak light), into the stud bay (no insulation in that bay, studs + leak light read clearly), and out through the drywall hole looking at the couple.
- Camera spline: monotone cubic per axis (the speed ramp at the wall made Catmull-Rom overshoot into the wall). Floor/aim clamps.
- Tumbler: deeper teal powder coat, sits on the draped cloth (was floating 2 cm), handle toward her right hand; dent no longer punches through to the inner wall; condensation reads as glossy beads.
- Her hand now reaches the handle (cup moved 14 cm toward her); fingers through the handle loop; the cup is lifted with the hand. Left hand to her chest.
- Eyes no longer black (cornea shadow).
- Beat 4 and the rack focus now keep the bullet in frame and in focus (f555, f606).
- Impact flash and sparks toned down (were blowing out to white).
- Bullet lands clear of his shoe; floor bounce close-up at 60 mm.
- Birds take off from the roof ridge and street lamps flicker on in beat 1.

## Still open (working on)
- 0.0–0.6 s: bullet small in the frame on the street.
- 7.8–8.6 s orbit from her face to his: two in-between framings are mostly wall.
- X-ray dive (17.6–18.6 s): water and ripples read, ice cubes barely.
- 18.8–19.0 s soft (camera passing close to his reaching arm).
