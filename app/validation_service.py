import json
from app.blender_launcher import BlenderLauncher
from validation import ValidationRunner
from validation.models import FBXData, Severity
import os

class ValidationService:
    def __init__(self, launcher: BlenderLauncher):
        self.launcher = launcher
        self.runner = ValidationRunner()
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.extract_script = os.path.join(self.base_dir, "scripts", "blender_extract_validate.py")

    def validate_fbx(self, fbx_path, part_category):
        """Extracts data using Blender then runs the validation logical rules."""
        # 1. Extract data using Blender
        success, stdout, stderr = self.launcher.run_python_script(
            self.extract_script,
            extra_args=[fbx_path]
        )
        
        if success != 0:
            print(f"DEBUG: Blender process failed with return code {success}")
            print(f"DEBUG: Stderr: {stderr}")
            return [], None, f"Blender extraction failed: {stderr}"
            
        # Parse JSON from stdout
        fbx_json = None
        try:
            # Blender output might have noise, find the marker
            lines = stdout.splitlines()
            if "RESULT_START" not in lines:
                print(f"DEBUG: RESULT_START marker not found in stdout.")
                print(f"DEBUG: Full Stdout: {stdout}")
                return [], None, "Blender extraction failed: Missing result marker."
                
            start_idx = lines.index("RESULT_START")
            json_str = lines[start_idx + 1]
            fbx_json = json.loads(json_str)
        except (ValueError, IndexError, json.JSONDecodeError) as e:
            print(f"DEBUG: JSON Parse Error: {e}")
            return [], None, f"Failed to parse Blender output: {e}"

        if "error" in fbx_json:
            return [], None, fbx_json["error"]

        # 2. Build FBXData object
        fbx_data = FBXData(
            filename=fbx_json["filename"],
            tris=fbx_json["tris"],
            meshes=fbx_json["meshes"],
            armature_name=fbx_json["armature_name"],
            bones=fbx_json["bones"]
        )
        
        # 3. Run logical rules
        results, filtered_fbx, = self.runner.validate(fbx_path, fbx_data, part_category)
        return results, filtered_fbx, None
