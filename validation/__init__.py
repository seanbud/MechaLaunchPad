import json
import os
from validation.models import FBXData, ValidationResult, Severity
from validation.rules import naming, bone_set, tri_count

class ValidationRunner:
    def __init__(self, registry_path=None):
        if not registry_path:
            registry_path = os.path.join(os.path.dirname(__file__), "part_registry.json")
        
        with open(registry_path, "r") as f:
            self.registry = json.load(f)

    def validate(self, fbx_path, fbx_data: FBXData, part_category):
        """Runs all validation rules against the extracted FBX data."""
        results = []
        
        part_config = self.registry.get(part_category)
        if not part_config:
            return [ValidationResult(
                rule_id="CONFIG_INVALID",
                passed=False,
                message=f"Unknown part category: {part_category}"
            )]
        
        # Add name for convenience
        part_config["name"] = part_category
        allowed_bones = set(part_config.get("bones", []))
        
        # 0. Filter meshes to the target category
        filtered_meshes = []
        ignored_count = 0
        for mesh in fbx_data.meshes:
            parent_bone = mesh.get("parent_bone", "")
            if parent_bone in allowed_bones or not parent_bone:
                filtered_meshes.append(mesh)
            else:
                ignored_count += 1
        
        if ignored_count > 0:
            results.append(ValidationResult(
                rule_id="BONE_SET_FILTER",
                passed=True,
                severity=Severity.INFO,
                message=f"Category Filtering: Ignored {ignored_count} meshes belonging to other limbs/bones."
            ))

        # Create a filtered copy of FBXData for rules to consume
        filtered_fbx = FBXData(
            filename=fbx_data.filename,
            tris=fbx_data.tris, # Original total (rules should use mesh list now)
            meshes=filtered_meshes,
            armature_name=fbx_data.armature_name,
            bones=fbx_data.bones
        )
        
        # Rule 1: Naming
        results.append(naming.check(fbx_path, part_category))
        
        # Rule 2: Bone Set (Now checks filtered meshes for loose objects)
        results.extend(bone_set.check(filtered_fbx, part_config))
        
        # Rule 3: Tri Count (Now calculates from filtered_fbx.meshes)
        results.append(tri_count.check(filtered_fbx, part_config))
        
        return results, filtered_fbx
