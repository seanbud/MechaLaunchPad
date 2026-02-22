import bpy
import sys
import os
import json

def extract_data(fbx_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    try:
        bpy.ops.import_scene.fbx(filepath=fbx_path)
    except Exception as e:
        return {"error": str(e)}

    data = {
        "filename": os.path.basename(fbx_path),
        "tris": 0,
        "meshes": [],
        "armature_name": "",
        "bones": []
    }

    # Identify Armature
    armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
    if armatures:
        armature = armatures[0]
        data["armature_name"] = armature.name
        data["bones"] = [bone.name for bone in armature.data.bones]

    # Process Meshes
    total_tris = 0
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            # Get triangle count (evaluated depsgraph for modifiers)
            dg = bpy.context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(dg)
            mesh_eval = obj_eval.to_mesh()
            tri_count = sum(len(p.vertices) - 2 for p in mesh_eval.polygons)
            total_tris += tri_count
            
            # Find parent bone if any
            parent_bone = ""
            bone_matrix_inv = None
            if obj.parent and obj.parent_type == 'BONE':
                parent_bone = obj.parent_bone
                # Armature-space matrix of the bone
                # pose_bones[parent_bone].matrix is in armature space
                bone_matrix_inv = obj.parent.pose.bones[parent_bone].matrix.inverted()
            
            # Extract Vertex Data for Viewport
            vertices = []
            normals = []
            indices = []
            
            # Use mesh_eval (has modifiers applied)
            # vertices are in local space. obj.matrix_world converts to global.
            # Armature might have its own orientation. 
            # We want everything in Armature Space.
            armature = obj.parent if obj.parent and obj.parent.type == 'ARMATURE' else None
            if armature:
                # v_arm = arm.inv @ obj.world @ v.co
                matrix_to_arm = armature.matrix_world.inverted() @ obj.matrix_world
            else:
                matrix_to_arm = obj.matrix_world
            
            for v in mesh_eval.vertices:
                # 1. Transform vertex to armature space
                v_arm = matrix_to_arm @ v.co
                
                # 2. If parented to bone, transform to bone-relative space
                if bone_matrix_inv:
                    v_local = bone_matrix_inv @ v_arm
                else:
                    v_local = v_arm
                
                # 3. Use raw Blender Z-up coordinates
                vertices.extend([v_local.x, v_local.y, v_local.z])
                
                # Transform normal too (rotation part only)
                n_arm = matrix_to_arm.to_quaternion() @ v.normal
                if bone_matrix_inv:
                    n_local = bone_matrix_inv.to_quaternion() @ n_arm
                else:
                    n_local = n_arm
                normals.extend([n_local.x, n_local.y, n_local.z])
            
            for p in mesh_eval.polygons:
                # Simple fan triangulation for n-gons
                if len(p.vertices) >= 3:
                    for i in range(1, len(p.vertices) - 1):
                        indices.extend([p.vertices[0], p.vertices[i], p.vertices[i+1]])

            data["meshes"].append({
                "name": obj.name,
                "parent_bone": parent_bone,
                "tris": tri_count,
                # location/rotation in JSON are now less relevant but kept for debug
                "location": list(obj.location),
                "rotation": list(obj.rotation_euler),
                "scale": list(obj.scale),
                "vertices": vertices,
                "normals": normals,
                "indices": indices
            })
            
            obj_eval.to_mesh_clear()

    data["tris"] = total_tris
    return data

if __name__ == "__main__":
    try:
        idx = sys.argv.index("--")
        fbx_path = sys.argv[idx + 1]
        result = extract_data(fbx_path)
        print("RESULT_START")
        print(json.dumps(result))
        print("RESULT_END")
    except Exception as e:
        print(f"FAILED: {e}")
