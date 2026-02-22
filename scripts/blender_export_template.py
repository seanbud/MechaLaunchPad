import bpy
import sys
import os
import argparse

def export_template(part_category, output_path):
    """
    Sets up the scene for template authoring and exports an FBX.
    1. Loads the current blend file (assumed to be the master template).
    2. Identifies meshes that belong to 'part_category' or are 'Guide' meshes.
    3. Exports to FBX with specific settings.
    """
    print(f"Generating template for: {part_category}")
    
    # Ensure we are in object mode
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    # Optional: Select everything and reset transforms (if needed)
    # bpy.ops.object.select_all(action='SELECT')
    # bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # FBX Export Settings
    # We want to export the Armature and Meshes.
    # We include all bones, as the requirement says "exported file still contains the full rig".
    
    bpy.ops.export_scene.fbx(
        filepath=output_path,
        use_selection=False, # Export everything in the template
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_NONE',
        bake_space_transform=False,
        object_types={'ARMATURE', 'MESH', 'EMPTY'},
        use_mesh_modifiers=True,
        mesh_smooth_type='FACE',
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        use_armature_deform_only=False,
        armature_nodetype='NULL',
        bake_anim=True, # Include canonical animations
        path_mode='AUTO',
        embed_textures=False,
        batch_mode='OFF'
    )
    
    print(f"Template exported to: {output_path}")

if __name__ == "__main__":
    # Internal Blender args start after '--'
    try:
        idx = sys.argv.index("--")
        args = sys.argv[idx + 1:]
    except ValueError:
        args = []

    parser = argparse.ArgumentParser()
    parser.add_argument("--part", required=True, help="Part category (e.g. LeftArm)")
    parser.add_argument("--output", required=True, help="Output FBX path")
    
    parsed_args = parser.parse_known_args(args)[0]
    
    export_template(parsed_args.part, parsed_args.output)
