import bpy
import sys
import os
import json
import mathutils

def extract_animation(fbx_path, output_json):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx_path)
    
    armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
    if not armatures:
        print("Error: No armature found.")
        return
    
    armature = armatures[0]
    
    scene = bpy.context.scene
    start_frame = int(scene.frame_start)
    end_frame = int(scene.frame_end)
    
    animation_data = {
        "start_frame": start_frame,
        "end_frame": end_frame,
        "frames": []
    }
    
    # We also want to know if the Armature has a world scale/rotation
    arm_world_mat = list(armature.matrix_world.col[0]) + list(armature.matrix_world.col[1]) + \
                    list(armature.matrix_world.col[2]) + list(armature.matrix_world.col[3])
    animation_data["armature_world_matrix"] = arm_world_mat

    for f in range(start_frame, end_frame + 1):
        scene.frame_set(f)
        frame_bones = {}
        for bone in armature.pose.bones:
            # Raw armature-space matrix
            mat = bone.matrix
            # Flatten to column-major for OpenGL
            col_major = []
            for i in range(4):
                for j in range(4):
                    col_major.append(mat[j][i])
            frame_bones[bone.name] = col_major
            
        animation_data["frames"].append(frame_bones)
        
    with open(output_json, "w") as f:
        json.dump(animation_data, f)
    print(f"Animation extracted to {output_json}")

if __name__ == "__main__":
    idx = sys.argv.index("--")
    fbx_path = sys.argv[idx + 1]
    output_json = sys.argv[idx + 2]
    extract_animation(fbx_path, output_json)
