import bpy
import sys
import os

def inspect_fbx(fbx_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx_path)
    
    print(f"Inspecting {fbx_path}")
    
    armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
    for arm in armatures:
        print(f"Armature: {arm.name}")
        for bone in arm.pose.bones:
            parent = bone.parent.name if bone.parent else "None"
            print(f"  Bone: {bone.name} (Parent: {parent})")
            
    print("Meshes:")
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            parent = obj.parent.name if obj.parent else "None"
            p_type = obj.parent_type
            p_bone = obj.parent_bone
            print(f"  Mesh: {obj.name} (Parent: {parent}, Type: {p_type}, Bone: {p_bone})")
            print(f"    Scale: {obj.scale}, MatrixWorld loc: {obj.matrix_world.to_translation()}")

    print("Actions:")
    for action in bpy.data.actions:
        print(f"  Action: {action.name} (Frames: {action.frame_range})")

if __name__ == "__main__":
    idx = sys.argv.index("--")
    inspect_fbx(sys.argv[idx + 1])
