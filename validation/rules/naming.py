import os
import re
from validation.models import ValidationResult, Severity

def check(fbx_path, part_category):
    """Checks if the filename follows the convention: PartCategory_v###.fbx"""
    filename = os.path.basename(fbx_path)
    pattern = rf"^{part_category}_v\d{{3}}\.fbx$"
    
    if re.match(pattern, filename):
        return ValidationResult(
            rule_id="NAMING_VALID",
            passed=True,
            message="Filename follows convention."
        )
    else:
        return ValidationResult(
            rule_id="NAMING_VALID",
            passed=False,
            severity=Severity.ERROR,
            message=f"Filename '{filename}' does not match expected pattern '{part_category}_v###.fbx'.",
            fix_hint=f"Rename the file to something like {part_category}_v001.fbx"
        )
