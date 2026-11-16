#!/bin/bash
# body_prop_cross per shot (step 3) on the given blend; rigs = the shot's people; props = held/touched items + touched set pieces
B=/opt/blender/blender-5.2.2-linux-x64/blender; D=$(cd "$(dirname "$0")" && pwd); F=$1; OUT=$2; mkdir -p $OUT
TIM=/tmp/claude-0/-home-user-Muhammed/0b019bde-e3b5-5ca9-9067-8cf46a4c300e/scratchpad/build/timing_used.json
PR="P_Paperclip,P_FishPen,P_Doorknob,P_CampStove,P_Generator,P_Keg,P_Snowmobile,P_Van,P_Contract,P_CondoKeys,P_VanKeys,P_HouseKeys,P_Guitar,P_SnowGlobe,P_MovieCamera,P_Clapper,P_Newspaper,P_TicketCard,HOME_Counter,HOME_CounterTop"
declare -A RIG=( [S01]=Hero,PenLady [S02]=Hero [S03]=Hero,KnobMan [S04]=Hero [S05]=Hero,Camper [S06]=Hero,Worker [S07]=Hero,KegGuy
 [S08]=Hero,KegGuy,Camper,Worker [S09]=Hero,SledGuy [S10]=Hero [S11]=Hero [S12]=Hero,VanGuy [S13]=Hero [S14]=Hero,Exec [S15]=Hero,Landlady
 [S16]=Hero [S17]=Hero,Rocker [S18]=Hero,Rocker [S19]=Hero,Rocker [S20]=Hero [S21]=Hero,Director [S22]=Hero,Director [S23]=Mayor,PenLady
 [S24]=Hero [S26]=Hero [S27]=Hero,Mayor [S28]=Hero [S29]=Hero )
for k in $(python3 -c "import json;print(' '.join(sorted(json.load(open('$TIM')))))"); do
  [ -z "${RIG[$k]}" ] && continue
  read a b < <(python3 -c "import json;v=json.load(open('$TIM'))['$k'];print(v[0],v[1]-1)")
  echo "$k $a $b ${RIG[$k]}"
done | xargs -P 3 -L 1 bash -c 'B='$B'; $B -b '$F' --python '$D'/bpc_run.py -- '$OUT'/bpc_$0.json 3 $1 $2 '$PR' $3 2>&1 | grep BPC_DONE | sed "s/^/$0 /"'
