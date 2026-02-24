import sys
import os
from app.services.blender_launcher import BlenderLauncher
from app.services.validation_service import ValidationService

def test_validation(fbx_path, category="LeftArm"):
    launcher = BlenderLauncher()
    service = ValidationService(launcher)
    
    print(f"Testing validation for {fbx_path} as {category}...")
    results, error = service.validate_fbx(fbx_path, category)
    
    if error:
        print(f"ERR: {error}")
        return

    print("\nResults:")
    all_passed = True
    for r in results:
        status = "PASS" if r.passed else f"FAIL [{r.severity.value}]"
        print(f"{status} [{r.rule_id}]: {r.message}")
        if not r.passed:
            all_passed = False
            if r.fix_hint:
                print(f"   Fix: {r.fix_hint}")
                
    if all_passed:
        print("\nSUMMARY: ALL CHECKS PASSED")
    else:
        print("\nSUMMARY: FAILED")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.test_validation <fbx_path> [category]")
        sys.exit(1)
    
    path = sys.argv[1]
    cat = sys.argv[2] if len(sys.argv) > 2 else "LeftArm"
    test_validation(path, cat)
