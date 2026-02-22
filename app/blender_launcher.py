import subprocess
import os
import sys

class BlenderLauncher:
    """Handles locating and launching Blender in background mode."""
    
    DEFAULT_PATHS = [
        r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
    ]

    def __init__(self, executable_path=None):
        self.executable_path = executable_path or self._find_blender()
        if not self.executable_path:
            raise FileNotFoundError("Blender executable not found. Please specify path.")

    def _find_blender(self):
        # 1. Check if it's already in PATH
        try:
            subprocess.run(["blender", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return "blender"
        except FileNotFoundError:
            pass

        # 2. Check common install locations
        for path in self.DEFAULT_PATHS:
            if os.path.exists(path):
                return path
        
        return None

    def run_python_script(self, script_path, blend_file=None, extra_args=None):
        """Runs a python script in Blender headless mode."""
        cmd = [self.executable_path, "--background"]
        
        if blend_file:
            cmd.extend([blend_file])
            
        cmd.extend(["--python", script_path])
        
        if extra_args:
            cmd.append("--")
            cmd.extend(extra_args)
            
        print(f"Executing Blender command: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr
