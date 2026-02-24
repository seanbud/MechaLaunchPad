import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from app.services.validation_service import ValidationService
from app.services.gitlab_service import GitLabService
from validation.models import Severity

class TestBusinessLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need BlenderLauncher but can inject a mock if needed.
        # For an integration test, we use the real one since it's headless anyway.
        from app.services.blender_launcher import BlenderLauncher
        try:
            cls.launcher = BlenderLauncher()
            cls.validation = ValidationService(cls.launcher)
            cls.gitlab = GitLabService(repo_url="https://gitlab.com", token="dummy", project_id="123")
            # Override local repo path for testing so we don't mess up the real one
            cls.gitlab.local_repo_path = os.path.join(os.getcwd(), "test_mech_assets")
        except Exception as e:
            raise unittest.SkipTest(f"Failed to init services: {e}")

    def test_01_validation_failure(self):
        # Basic_Model.fbx is a full robot, validating it as a "LeftArm" should fail triangle/bone checks
        fbx_path = os.path.abspath(os.path.join("..", "data", "Basic_Model.fbx"))
        self.assertTrue(os.path.exists(fbx_path))
        
        results, fbx_data, error = self.validation.validate_fbx(fbx_path, "LeftArm")
        self.assertIsNone(error, "Should not have a hard extraction error")
        self.assertIsNotNone(results, "Should return rule results")
        
        # Check if any errors occurred
        has_errors = any(not r.passed and r.severity == Severity.ERROR for r in results)
        self.assertTrue(has_errors, "Basic_Model.fbx should fail specific category validation.")

    def test_02_validation_success_and_publish(self):
        # We have RightArm_v001.fbx which ideally passes
        fbx_path = os.path.abspath(os.path.join("..", "data", "RightArm_v001.fbx"))
        if not os.path.exists(fbx_path):
            self.skipTest("RightArm_v001.fbx not found for test")
            
        results, fbx_data, error = self.validation.validate_fbx(fbx_path, "RightArm")
        self.assertIsNone(error)
        
        has_errors = any(not r.passed and r.severity == Severity.ERROR for r in results)
        
        if has_errors:
            self.fail(f"RightArm_v001.fbx failed validation: {[r.message for r in results if not r.passed]}")
            
        # Ensure that fbx_data is returned correctly upon success
        self.assertIsNotNone(fbx_data)
        self.assertEqual(fbx_data.filename, "RightArm_v001.fbx")

        # Now test the Git integration logic locally (dry run / offline check)
        # We don't actually push to GitLab, but we can verify the staging logic.
        
        # Create a mock repo locally to avoid cloning
        os.makedirs(self.gitlab.local_repo_path, exist_ok=True)
        from git import Repo
        if not os.path.exists(os.path.join(self.gitlab.local_repo_path, ".git")):
            repo = Repo.init(self.gitlab.local_repo_path)
            # Create a dummy commit to establish main
            dummy_file = os.path.join(self.gitlab.local_repo_path, "README.md")
            with open(dummy_file, "w") as f:
                f.write("# Dummy Repo")
            repo.index.add(["README.md"])
            repo.index.commit("Initial commit")
            if "main" not in repo.heads:
                repo.create_head("main").checkout()
        repo = Repo(self.gitlab.local_repo_path)
        if "origin" not in repo.remotes:
            repo.create_remote("origin", url="https://gitlab.com/dummy/dummy.git")
        
        # Override ensure_repo to just return our mock
        self.gitlab.ensure_repo = lambda: Repo(self.gitlab.local_repo_path)
        
        # Prevent actual push
        # We will mock the push call inside publish_asset

        
        # We will mock the push call inside publish_asset
        original_push = __import__("git").remote.Remote.push
        def mock_push(self, refspec):
            return []
        __import__("git").remote.Remote.push = mock_push
        
        branch_name = self.gitlab.publish_asset("RightArm", fbx_data, fbx_path, "Test commit")
        self.assertTrue(branch_name.startswith("submit/RightArm/v"))
        
        # publish_asset cleanly restores 'main' at the end, which removes our new file from the working tree
        # Let's check out the new branch it created to verify
        self.gitlab.ensure_repo().heads[branch_name].checkout()
        
        # Verify file exists where it should
        target_path = os.path.join(self.gitlab.local_repo_path, "parts", "RightArm")
        self.assertTrue(os.path.exists(target_path))
        
        # Restore push
        __import__("git").remote.Remote.push = original_push

if __name__ == "__main__":
    unittest.main(verbosity=2)
