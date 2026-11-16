import bpy
m = bpy.data.objects["ManC.male_casualsuit04"].data.materials[0]
for l in m.node_tree.links: print("LNK", l.from_node.name, l.from_socket.name, "->", l.to_node.name, l.to_socket.name)
m = bpy.data.objects["ManC.body"].data.materials
print([x.name for x in m])
