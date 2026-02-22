import bpy
import sys
import os
import json

def extract_rig_transforms(fbx_path, output_json):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx_path)
    
    armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
    if not armatures:
        print("Error: No armature found.")
        return
    
    armature = armatures[0]
    bone_data = {}
    
    for bone in armature.pose.bones:
        # matrix is armature-space
        mat = bone.matrix
        
        # Flatten to column-major for OpenGL
        matrix_list = []
        for i in range(4):
            for j in range(4):
                matrix_list.append(mat[j][i])
            
        bone_data[bone.name] = {
            "matrix": matrix_list 
        }
        
    with open(output_json, "w") as f:
        json.dump(bone_data, f, indent=2)
    print(f"Bones extracted to {output_json}")

if __name__ == "__main__":
    try:
        idx = sys.argv.index("--")
        fbx_path = sys.argv[idx + 1]
        output_json = sys.argv[idx + 2]
        extract_rig_transforms(fbx_path, output_json)
    except Exception as e:
        print(f"FAILED: {e}")
