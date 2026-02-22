from validation.models import ValidationResult, Severity, FBXData

def check(fbx_data: FBXData, part_config: dict):
    """Checks if meshes have parent bones. Category filtering happens in the Runner."""
    results = []
    
    for mesh in fbx_data.meshes:
        parent_bone = mesh.get("parent_bone", "")
        mesh_name = mesh.get("name", "")
        
        if not parent_bone:
             results.append(ValidationResult(
                rule_id="BONE_SET_VALID",
                passed=False,
                severity=Severity.ERROR,
                message=f"Mesh '{mesh_name}' has no parent bone. All authored meshes must be parented to a bone.",
                details={"mesh": mesh_name},
                fix_hint="Parent the mesh to a bone in Blender (Ctrl+P -> Bone)."
            ))
            
    if not results:
        if not fbx_data.meshes:
             results.append(ValidationResult(
                rule_id="BONE_SET_VALID",
                passed=False,
                severity=Severity.WARNING,
                message=f"No meshes found that belong to the {part_config.get('name')} category.",
                fix_hint="Ensure your meshes are parented to the correct bones for this limb."
            ))
        else:
            results.append(ValidationResult(
                rule_id="BONE_SET_VALID",
                passed=True,
                message=f"All {len(fbx_data.meshes)} identified meshes are parented correctly."
            ))
        
    return results
