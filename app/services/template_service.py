import os
from app.services.blender_launcher import BlenderLauncher

class TemplateService:
    """Service for managing authoring templates."""
    
    def __init__(self, launcher: BlenderLauncher):
        self.launcher = launcher
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        project_root = os.path.dirname(self.base_dir)
        self.template_blend = os.path.join(project_root, "data", "BasicTemplate.blend")
        self.export_script = os.path.join(project_root, "scripts", "blender_export_template.py")

    def generate_template(self, part_category, output_dir):
        """Generates an FBX template for the given part category."""
        filename = f"{part_category}_Template.fbx"
        output_path = os.path.join(output_dir, filename)
        
        # Ensure output dir exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Build extra args for the script
        extra_args = [
            "--part", part_category,
            "--output", output_path
        ]
        
        success, stdout, stderr = self.launcher.run_python_script(
            self.export_script,
            blend_file=self.template_blend,
            extra_args=extra_args
        )
        
        if success != 0:
            print(f"Blender Error Code: {success}")
            print(f"Stderr: {stderr}")
            return None, stderr
            
        print(f"Successfully generated template: {output_path}")
        return output_path, None
