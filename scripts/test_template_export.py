import sys
import os
from app.blender_launcher import BlenderLauncher
from app.template_service import TemplateService

def test_export(part_category):
    launcher = BlenderLauncher()
    service = TemplateService(launcher)
    
    output_dir = os.path.join(os.getcwd(), "temp_exports")
    print(f"Testing template export for {part_category}...")
    
    path, error = service.generate_template(part_category, output_dir)
    
    if path:
        print(f"TEST PASSED: {path}")
        # Clean up
        # os.remove(path)
    else:
        print(f"TEST FAILED: {error}")
        sys.exit(1)

if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "LeftArm"
    test_export(part)
