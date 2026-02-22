import bpy
import sys
import os

def inspect_fbx(fbx_path):
    # Clear existing data
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Import FBX
    if not os.path.exists(fbx_path):
        print(f"Error: File not found {fbx_path}")
        return

    bpy.ops.import_scene.fbx(filepath=fbx_path)
    
    # Find armature
    armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
    
    if not armatures:
        print("Error: No armature found in FBX")
        return
    
    armature = armatures[0]
    print(f"\nArmature: {armature.name}")
    print("-" * 30)
    
    # List bones
    for bone in armature.data.bones:
        parent_name = bone.parent.name if bone.parent else "None"
        print(f"Bone: {bone.name} (Parent: {parent_name})")

if __name__ == "__main__":
    # Get FBX path from command line args (after --)
    try:
        idx = sys.argv.index("--")
        fbx_path = sys.argv[idx + 1]
        inspect_fbx(fbx_path)
    except (ValueError, IndexError):
        print("Usage: blender --background --python inspect_rig.py -- <fbx_path>")
