import os
import json

class StateManager:
    """Handles loading and saving persistent application session state."""
    def __init__(self):
        self.app_data_dir = os.path.join(os.path.expanduser("~"), ".mechalaunchpad")
        os.makedirs(self.app_data_dir, exist_ok=True)
        os.chmod(self.app_data_dir, 0o700)
        self.state_file = os.path.join(self.app_data_dir, "session_state.json")
        self.state = {
            "validated_parts": [],
            "ci_tracking": []
        }
        self.load_state()

    def load_state(self):
        """Loads state from disk if it exists."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    self.state["validated_parts"] = data.get("validated_parts", [])
                    self.state["ci_tracking"] = data.get("ci_tracking", [])
            except Exception as e:
                print(f"Failed to load state: {e}")

    def save_state(self):
        """Saves current state to disk."""
        try:
            # Create file with restrictive permissions (0o600)
            fd = os.open(self.state_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'w') as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            print(f"Failed to save state: {e}")

    def add_validated_part(self, category, filename, filepath, fbx_data):
        """Adds a part to the validated list if it isn't already there."""
        if not any(p["filepath"] == filepath for p in self.state["validated_parts"]):
            # Serialize the FBXData object so we can reconstruct it on startup
            fbx_dict = None
            if fbx_data:
                fbx_dict = {
                    "filename": fbx_data.filename,
                    "tris": fbx_data.tris,
                    "meshes": fbx_data.meshes,
                    "armature_name": fbx_data.armature_name,
                    "bones": fbx_data.bones
                }
                
            self.state["validated_parts"].append({
                "category": category,
                "filename": filename,
                "filepath": filepath,
                "fbx_data": fbx_dict
            })
            self.save_state()

    def remove_validated_part(self, filepath):
        """Removes a validated part by filepath."""
        self.state["validated_parts"] = [
            p for p in self.state["validated_parts"] 
            if p["filepath"] != filepath
        ]
        self.save_state()

    def add_tracked_ci(self, category, branch_name):
        """Adds a pipeline to the tracking list if not already present."""
        if not any(ci["branch_name"] == branch_name for ci in self.state["ci_tracking"]):
            self.state["ci_tracking"].append({
                "category": category,
                "branch_name": branch_name
            })
            self.save_state()
            
    def remove_tracked_ci(self, branch_name):
        """Removes a pipeline from the tracking list."""
        self.state["ci_tracking"] = [
            ci for ci in self.state["ci_tracking"]
            if ci["branch_name"] != branch_name
        ]
        self.save_state()

    def get_all_tracked_ci(self):
        """Returns all tracked CI pipeline contexts."""
        return self.state["ci_tracking"]
