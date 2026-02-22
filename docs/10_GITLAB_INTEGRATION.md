# 10 — GitLab Integration

## Authentication

### Personal Access Token (PAT)

| Property | Value |
|---|---|
| Token scope | `api`, `write_repository` |
| Storage (MVP) | `.env` file in the tool directory, loaded via `python-dotenv` |
| Storage (future) | OS keyring via `keyring` package |
| Environment variable | `GITLAB_PAT` |

```ini
# .env
GITLAB_URL=https://gitlab.example.com
GITLAB_PAT=glpat-xxxxxxxxxxxxxxxxxxxx
GITLAB_PROJECT_ID=42
```

The app loads these on startup:

```python
from dotenv import load_dotenv
import os

load_dotenv()
GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_PAT = os.getenv("GITLAB_PAT")
PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")
```

---

## Git Operations Strategy

MechaLaunchPad uses **GitPython** to manage a local clone of `mech-assets`.

### Local Clone Lifecycle

1. **First launch**: Tool prompts for clone location (or uses a default like `~/.mechalaunchpad/mech-assets/`).
2. **On publish**: Tool ensures the clone is up-to-date (`git fetch` + `git pull`).
3. **Asset copy**: Validated FBX + metadata JSON are copied into the correct directory (e.g. `parts/LeftArm/v001/`).
4. **Commit + push**: Tool stages, commits, and pushes.

### Git helper module

```python
# app/gitlab/git_ops.py
from git import Repo
import os

class AssetRepo:
    def __init__(self, repo_path: str, remote_url: str | None = None):
        if not os.path.exists(os.path.join(repo_path, ".git")):
            self.repo = Repo.clone_from(remote_url, repo_path)
        else:
            self.repo = Repo(repo_path)

    def ensure_branch(self, branch: str):
        """Create and checkout a submission branch."""
        if branch in self.repo.heads:
            self.repo.heads[branch].checkout()
        else:
            self.repo.create_head(branch).checkout()

    def stage_and_commit(self, files: list[str], message: str) -> str:
        """Stage files, commit, return SHA."""
        self.repo.index.add(files)
        commit = self.repo.index.commit(message)
        return commit.hexsha

    def push(self, branch: str):
        """Push to origin."""
        origin = self.repo.remotes.origin
        origin.push(refspec=f"{branch}:{branch}")
```

---

## Branching Strategy

| Branch | Purpose |
|---|---|
| `main` | Latest blessed assets (merged after CI passes) |
| `submit/<Part>/<version>` | Per-submission branch, e.g. `submit/LeftArm/v001` |

### Publish Flow

1. `git checkout -b submit/LeftArm/v001` (from `main`).
2. Copy FBX + metadata to `parts/LeftArm/v001/`.
3. `git add`, `git commit -m "Submit LeftArm v001"`.
4. `git push origin submit/LeftArm/v001`.
5. CI triggers on push.
6. On CI success → merge to `main` (manual or auto-merge via API).

---

## Pipeline Triggering

Pushing to a `submit/*` branch automatically triggers the CI pipeline (via `.gitlab-ci.yml` rules):

```yaml
workflow:
  rules:
    - if: '$CI_COMMIT_BRANCH =~ /^submit\//'
```

No manual API call needed to trigger the pipeline — the push is sufficient.

---

## Polling CI Status

After pushing, the tool polls the GitLab API for pipeline status:

```python
# app/gitlab/client.py
import requests, time

class GitLabClient:
    def __init__(self, url: str, token: str, project_id: int):
        self.base = f"{url}/api/v4/projects/{project_id}"
        self.headers = {"PRIVATE-TOKEN": token}

    def get_latest_pipeline(self, ref: str) -> dict:
        r = requests.get(
            f"{self.base}/pipelines",
            headers=self.headers,
            params={"ref": ref, "per_page": 1},
        )
        r.raise_for_status()
        pipelines = r.json()
        return pipelines[0] if pipelines else None

    def poll_pipeline(self, pipeline_id: int, interval: int = 5) -> dict:
        while True:
            r = requests.get(
                f"{self.base}/pipelines/{pipeline_id}",
                headers=self.headers,
            )
            r.raise_for_status()
            data = r.json()
            if data["status"] in ("success", "failed", "canceled"):
                return data
            time.sleep(interval)
```

In the PySide app, polling runs on a `QThread` to avoid blocking the UI.
