cd /tmp/claude-0/b09
B=/opt/blender/blender-5.2.2-linux-x64/blender; F=/home/user/Muhammed/blender/ScaldingCoffee_v002b/ScaldingCoffee_v002b_60fps.blend; P=/home/user/Muhammed/blender/pipeline
run(){ timeout 3000 $B -b $F --python scripts/bpc_run.py -- chkb/bpc_$1.json 3 $2 $3 $4 $5 > chkb/bpc_$1.full 2>&1; grep -E "BPC_DONE|BPC_MISSING|Error|Traceback" chkb/bpc_$1.full; }
run B1 1 301 SpillCup_Rim,SpillCup,SpillLid,CarSeats,CarDoorP,CarDash,CarFloor,CarWheel,CarRoofLiner,CarDoorTrimFar GranC
run B3 727 1043 Bed,Mattress,BedWedge,Pillow,Blanket,IVStand,Bedside,DocBadge,DocClipboard GranB,Doc2,Nurse2
run B4 1044 1481 Cup_C4,Cup_C1,Cup_C5,Phone_C2,Phone_Hero2,FrontCounter,FrontCounterTop,BarTable,Tray0,Tray1 C1,C2,C4,Hero2,C5
run B5 1482 1642 BoardTable,BoardChair0,BoardChair1,BoardChair2,BoardChair3,BoardChair4,BoardCup,Sideboard BossA
run B6 1643 1808 DialKnob,TempDial,Brewer,BackCounter,BackCounterTop,FrontCounter,FrontCounterTop Employee
timeout 3000 $B -b $F --python $P/clip_scan.py -- chkb/clip.json 6 2>&1 | grep -iE "bad|range|done|Error|Traceback" | tail -5
timeout 3000 $B -b $F --python $P/qa_check.py -- chkb/qa.json 6 chkb/beats.json 2>&1 | grep -vE "^(Blender|Read|$)" | tail -25
timeout 3000 $B -b $F --python scripts/limb_check_noshoulder.py -- chkb/limb.json 4 2>&1 | grep -vE "^(Blender|Read|$)" | tail -12
echo CHECKS_DONE
