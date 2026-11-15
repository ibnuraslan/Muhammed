# Dog pose helpers (rig from rig_quadruped.py; dog faces -Y in rest, feet on z=0)
import bpy, math
from mathutils import Vector, Quaternion, Euler, Matrix
R_=math.radians
def _q(rx=0,ry=0,rz=0): return Euler((R_(rx),R_(ry),R_(rz)),'XYZ').to_quaternion()
def dkey(dog, f, pose):
    """pose: dict bone -> (loc tuple or None, (rx,ry,rz) local degrees or None). Unlisted pose bones reset."""
    for pb in dog.pose.bones:
        loc, rot = pose.get(pb.name, (None, None))
        pb.location = Vector(loc) if loc else Vector()
        pb.rotation_quaternion = _q(*rot) if rot else Quaternion()
        pb.keyframe_insert("location", frame=f); pb.keyframe_insert("rotation_quaternion", frame=f)
def blend(a, b, t):
    out={}
    for k in set(a)|set(b):
        la,ra=a.get(k,(None,None)); lb,rb=b.get(k,(None,None))
        la=la or (0,0,0); lb=lb or (0,0,0); ra=ra or (0,0,0); rb=rb or (0,0,0)
        out[k]=(tuple(x+(y-x)*t for x,y in zip(la,lb)), tuple(x+(y-x)*t for x,y in zip(ra,rb)))
    return out
