"""Light wood on the hammer HANDLE (object z < 0.115) so the slim handle reads in the fist against dark rock.
exec'd by 03_shots.py; also runnable on a package: blender -b f.blend --python hammer_wood.py -- save"""
import bpy, sys
m = bpy.data.materials["cross_pein_hammer"]; nt = m.node_tree
if "HandleWood" not in nt.nodes:
    P = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); src = P.inputs['Base Color'].links[0].from_socket
    tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sp.inputs[0])
    lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.115; nt.links.new(sp.outputs['Z'], lt.inputs[0])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.name = "HandleWood"; mx.inputs['B'].default_value = (0.80, 0.58, 0.33, 1)
    nt.links.new(src, mx.inputs['A']); nt.links.new(lt.outputs[0], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], P.inputs['Base Color'])
    print("HANDLE_WOOD set")
if "--" in sys.argv and "save" in sys.argv[sys.argv.index("--"):]:
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, compress=True)
