# 03. CI and GitLab Integration

## The Problem
Artists shouldn't need a browser tab open to GitLab constantly refreshing to see if their pipeline passed testing. The UI must be self-updating and native.

## The Implementation

### `GitLabService.publish_asset`
When an artist publishes, the application does the heavy lifting:
1. Clones the remote repository (`https://gitlab.com/seanbud-group/MechaLaunchPad`).
2. Creates a structural tracking branch (`submit/Category/v00X`).
3. Copies the `.fbx` into the local repository layout.
4. Auto-commits and forcefully pushes the new branch to the remote server.

### The CI Pipeline Loop
**CRITICAL:** The remote repository *must* have a `.gitlab-ci.yml` file sitting in its `main` branch. 

If this file is missing, GitLab will not know what to do with the artist's new branches. By having a central YAML script in `main`, GitLab will automatically detect every new branch the app pushes up and immediately spawn a testing pipeline against that branch. 

### Asynchronous Polling (`CIPollingWorker`)
When a branch is pushed (or when the app restarts), the `CITab` natively spawns a `CIPollingWorker` thread (from `app/services/gitlab_service.py`). 

This keeps the main UI from freezing while we talk to the internet. 

- **The Flow:** The worker asks the GitLab API: *"Hey, what's the latest pipeline ID for branch `submit/RightArm/v010`?"*
- **The Loop:** It then pings that specific pipeline ID every 5 seconds. 
- **The Result:** It routes the results (Pending, Running, Success, Failed) back to the main UI thread via Qt Signals. 
- **Deep Tracing:** If a pipeline returns `failed`, the worker does *not* stop there. It automatically queries the `/jobs` endpoint for that specific pipeline, iterates through all the granular execution steps, and yanks the exact error strings from the job that caused the failure, formatting them cleanly into the UI log viewer for the artist to read.
