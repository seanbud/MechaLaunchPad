from validation.models import ValidationResult, Severity, FBXData

def check(fbx_data: FBXData, part_config: dict):
    """Checks total triangle count against part limits."""
    max_tris = part_config.get("max_tris", 999999)
    
    # Calculate current tris from the meshes list (allows for filtering)
    current_tris = sum(mesh.get("tris", 0) for mesh in fbx_data.meshes)
    
    if current_tris <= max_tris:
        return ValidationResult(
            rule_id="TRI_COUNT",
            passed=True,
            message=f"Triangle count ({current_tris}) is within limit ({max_tris})."
        )
    else:
        return ValidationResult(
            rule_id="TRI_COUNT",
            passed=False,
            severity=Severity.ERROR,
            message=f"Total triangle count ({current_tris}) exceeds the limit of {max_tris} for this part.",
            details={"current": current_tris, "limit": max_tris},
            fix_hint="Reduce polygon count using Decimate modifier or manual cleanup in Blender."
        )
