import os
import time
import shutil
import requests
from dotenv import load_dotenv
from PySide6.QtCore import QObject, Signal, QThread
from git import Repo

load_dotenv()

class GitLabService(QObject):
    """
    Service to handle interactions with the GitLab repository.
    Handles cloning, committing, pushing, and polling the CI pipelines.
    """
    def __init__(self, repo_url=None, token=None, project_id=None):
        super().__init__()
        self.repo_url = repo_url or os.getenv("GITLAB_URL")
        if self.repo_url and self.repo_url.count('/') > 2:
            parts = self.repo_url.split('/')
            self.repo_url = f"{parts[0]}//{parts[2]}"
            
        self.token = token or os.getenv("GITLAB_PAT")
        self.project_id = project_id or os.getenv("GITLAB_PROJECT_ID")
        
        # Git Identity Configuration
        self.author_name = os.getenv("GIT_AUTHOR_NAME", "MechaLaunch Artist")
        self.author_email = os.getenv("GIT_AUTHOR_EMAIL", "pipeline@mechalaunchpad.local")
        
        # Determine local checkout path (e.g. ~/.mechalaunchpad/mech-assets)
        app_data_dir = os.path.join(os.path.expanduser("~"), ".mechalaunchpad")
        os.makedirs(app_data_dir, exist_ok=True)
        os.chmod(app_data_dir, 0o700)
        self.local_repo_path = os.path.join(app_data_dir, "mech-assets")
        
        # Inject PAT into HTTPS URL for auth
        if self.repo_url and self.token and self.repo_url.startswith("https://"):
            # If the user provided the base URL, we need to try to figure out the full project path from the env
            # But the user only gave us a project ID, not the namespace path (e.g. seanbud-group/seanbud-project)
            # We must fetch the full path from the API first.
            
            # Use a dummy initial auth_url; ensure_repo will resolve the real one via the API
            self.auth_url_base = self.repo_url.replace("https://", f"https://oauth2:{self.token}@")
        else:
            self.auth_url_base = None

    def _resolve_remote_url(self):
        """Fetches the actual project path from the GitLab API using the Project ID."""
        if not self.auth_url_base or not self.project_id:
            return None
            
        api_url = f"{self.repo_url}/api/v4/projects/{self.project_id}"
        headers = {"PRIVATE-TOKEN": self.token}
        try:
            r = requests.get(api_url, headers=headers)
            r.raise_for_status()
            data = r.json()
            # path_with_namespace looks like "seanbud-group/seanbud-project"
            path_with_namespace = data.get("path_with_namespace")
            if path_with_namespace:
                return f"{self.auth_url_base}/{path_with_namespace}.git"
        except Exception as e:
            print(f"Failed to resolve remote URL from API: {e}")
        return None

    def ensure_repo(self):
        """Ensures the repository is cloned and up to date locally."""
        if not self.auth_url_base:
            raise ValueError("GitLab URL or PAT is missing in environment.")
            
        full_auth_url = self._resolve_remote_url()
        if not full_auth_url:
            raise ValueError("Could not resolve Git repository URL from Project ID.")
            
        if not os.path.exists(os.path.join(self.local_repo_path, ".git")):
            Repo.clone_from(full_auth_url, self.local_repo_path)
            
        repo = Repo(self.local_repo_path)
        
        # Ensure we are on main branch before creating submissions
        if "main" in repo.heads:
            repo.heads.main.checkout()
        else:
            # Maybe the default branch is master or something else, but let's assume main.
            for ref in repo.remotes.origin.refs:
                if ref.name == "origin/main":
                    repo.create_head("main", ref).set_tracking_branch(ref).checkout()
                    
        # Pull latest main integration
        origin = repo.remotes.origin
        origin.fetch()
        origin.pull(repo.active_branch)
        return repo

    def publish_asset(self, category, fbx_data, fbx_filepath, commit_message):
        """
        Creates a submission branch from main, copies the asset, and pushes it.
        Returns the branch name created.
        """
        repo = self.ensure_repo()
        
        # Fix the user signature to the application rather than the local desktop user
        with repo.config_writer() as config:
            config.set_value("user", "name", self.author_name)
            config.set_value("user", "email", self.author_email)
        
        # Ensure we are currently on main so we branch from the latest state (with CI files)
        if "main" in repo.heads:
            repo.heads.main.checkout()

        # Find highest version number by checking all remote and local branches
        highest_v = 0
        prefix = f"submit/{category}/v"
        
        for ref in repo.remotes.origin.refs:
            if ref.name.startswith(f"origin/{prefix}"):
                num_str = ref.name.split(f"origin/{prefix}")[-1]
                if num_str.isdigit():
                    highest_v = max(highest_v, int(num_str))
                    
        for head in repo.heads:
            if head.name.startswith(prefix):
                num_str = head.name.split(prefix)[-1]
                if num_str.isdigit():
                    highest_v = max(highest_v, int(num_str))

        # Also check local directories just in case they were merged but branches deleted
        parts_dir = os.path.join(self.local_repo_path, "parts", category)
        os.makedirs(parts_dir, exist_ok=True)
        existing_versions = [d for d in os.listdir(parts_dir) if os.path.isdir(os.path.join(parts_dir, d)) and d.startswith("v")]
        if existing_versions:
            nums = [int(v[1:]) for v in existing_versions if v[1:].isdigit()]
            if nums:
                highest_v = max(highest_v, max(nums))

        next_ver_num = highest_v + 1
        version = f"v{next_ver_num:03d}"
        branch_name = f"submit/{category}/{version}"
        
        # Delete local branch if it somehow exists to strictly prevent zombie history
        if branch_name in repo.heads:
            repo.delete_head(repo.heads[branch_name], force=True)

        # Create fresh branch FROM MAIN
        repo.create_head(branch_name, repo.heads.main).checkout()
            
        # Create target directory
        target_dir = os.path.join(parts_dir, version)
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy FBX file
        filename = f"{category}_{version}.fbx"
        target_fbx_path = os.path.join(target_dir, filename)
        shutil.copy2(fbx_filepath, target_fbx_path)
        
        # Stage and commit
        rel_path = os.path.relpath(target_fbx_path, self.local_repo_path)
        repo.index.add([rel_path])
        repo.index.commit(commit_message or f"Submit {category} {version}")
        
        # Push to remote
        origin = repo.remotes.origin
        origin.push(refspec=f"{branch_name}:{branch_name}")
        
        # Restore back to main
        repo.heads.main.checkout()
            
        return branch_name

class PublishWorker(QThread):
    finished = Signal(bool, str, str) # success, message, branch_name
    progress = Signal(str)

    def __init__(self, service: GitLabService, category: str, fbx_data, fbx_filepath: str, message: str):
        super().__init__()
        self.service = service
        self.category = category
        self.fbx_data = fbx_data
        self.fbx_filepath = fbx_filepath
        self.message = message

    def run(self):
        try:
            self.progress.emit("Syncing local repository...")
            # We do a dry run check for env vars first to fail fast
            if not getattr(self.service, 'auth_url_base', None):
                raise ValueError("GitLab URL or PAT not configured in environment.")
                
            self.progress.emit("Staging validated asset...")
            branch = self.service.publish_asset(
                self.category, 
                self.fbx_data, 
                self.fbx_filepath, 
                self.message
            )
            self.progress.emit("Pushed to GitLab! Triggering CI/CD...")
            self.finished.emit(True, f"Successfully published to {branch}", branch)
        except Exception as e:
            self.finished.emit(False, f"Publish failed: {str(e)}", "")

class CIPollingWorker(QThread):
    status_updated = Signal(dict) # Dict containing pipeline info
    error = Signal(str)
    
    def __init__(self, service: GitLabService, ref: str):
        super().__init__()
        self.service = service
        self.ref = ref
        self.polling = True
        
    def run(self):
        if not self.service.repo_url or not self.service.token or not self.service.project_id:
            self.error.emit("GitLab credentials missing for CI Polling.")
            return
            
        base_url = f"{self.service.repo_url}/api/v4/projects/{self.service.project_id}"
        headers = {"PRIVATE-TOKEN": self.service.token}
        
        # Initial wait for GitLab to register the push and start the pipeline
        time.sleep(3)
        
        try:
            # 1. Get latest pipeline for ref (with retry loop for async GitLab spinning)
            pipelines = None
            max_retries = 10
            for attempt in range(max_retries):
                if not self.polling:
                    return
                    
                r = requests.get(
                    f"{base_url}/pipelines",
                    headers=headers,
                    params={"ref": self.ref, "per_page": 1}
                )
                
                # If 404 or empty list, it just implies pipeline hasn't spawned yet
                if r.status_code == 200:
                    pipelines = r.json()
                    if pipelines:
                        break # Found it!
                        
                # Otherwise, it hasn't initialized. Wait and try again.
                time.sleep(3)
            
            if not pipelines:
                self.error.emit(f"No pipeline found for branch: {self.ref} after waiting 30 seconds.")
                return
                
            pipeline_id = pipelines[0]["id"]
            
            # 2. Poll the specific pipeline until done
            while self.polling:
                pr = requests.get(
                    f"{base_url}/pipelines/{pipeline_id}",
                    headers=headers
                )
                pr.raise_for_status()
                data = pr.json()
                status = data.get("status")
                
                # Fetch detailed job errors if failed
                if status == "failed":
                    try:
                        jr = requests.get(
                            f"{base_url}/pipelines/{pipeline_id}/jobs",
                            headers=headers
                        )
                        if jr.status_code == 200:
                            jobs = jr.json()
                            failed_jobs = [j for j in jobs if j.get("status") == "failed"]
                            if failed_jobs:
                                details = []
                                for j in failed_jobs:
                                    details.append(f"- Job '{j.get('name')}' failed in stage '{j.get('stage')}'.\n  URL: {j.get('web_url')}")
                                data["error_details"] = "\n".join(details)
                    except Exception as e:
                        print(f"Failed to fetch job details: {e}")
                        
                self.status_updated.emit(data)
                
                if status in ("success", "failed", "canceled"):
                    break
                    
                time.sleep(5)
                
        except requests.exceptions.RequestException as e:
            self.error.emit(f"API Error: {str(e)}")
            
    def stop(self):
        self.polling = False
