#!/bin/bash
# Profile every shot file, one process each, two at a time -> out/shot_stats.jsonl ; empty-Blender baseline -> out/shot_stats_base.txt
cd /home/user/Muhammed/projects/phone-banker; source ~/render_env/env.sh
: > out/shot_stats.jsonl
python -c "import bpy, resource; bpy.ops.wm.read_factory_settings(use_empty=True); print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024)" 2>/dev/null | tail -1 > out/shot_stats_base.txt
ls out/blend/{intro,sting,ch1,ch2,ch3}/*.blend | xargs -P 2 -I{} sh -c 'python edit/shot_stats.py "{}" 2>/dev/null | grep "^\[stats\]" | cut -c9- >> out/shot_stats.jsonl'
echo STATS_DONE
