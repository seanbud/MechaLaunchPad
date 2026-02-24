"""
GitLab CI Setup Script — Pushes pipeline configuration and validation scripts 
to the MechAssets GitLab repository.

Pushes 5 files to the remote repo's `main` branch via the GitLab Files API:
  1. .gitlab-ci.yml          — The real CI pipeline
  2. scripts/blender_extract_validate.py — Headless Blender FBX extractor
  3. scripts/ci_validate.py  — Standalone validation runner
  4. scripts/blender_render_thumbnail.py — Headless thumbnail renderer
  5. validation/part_registry.json — Part definitions + tri limits

Usage:
    python scripts/setup_gitlab_ci.py
"""

import os
import sys
import requests
from dotenv import load_dotenv


# ── .gitlab-ci.yml Content ─────────────────────────────────────────

GITLAB_CI_YAML = r'''stages:
  - validate
  - thumbnail
  - merge_request
  - deploy

# ── Stage 1: Validate the submitted FBX ─────────────────────────
validate_asset:
  stage: validate
  image: nytimes/blender:3.3.1-cpu-ubuntu18.04
  rules:
    - if: '$CI_COMMIT_REF_NAME =~ /^submit\//'
  before_script:
    - apt-get update -qq && apt-get install -y -qq python3 git > /dev/null 2>&1
  script:
    - |
      echo "============================================"
      echo "  MechaLaunchPad — Asset Validation Pipeline"
      echo "============================================"
      
      # Parse category and version from branch name: submit/Category/vXXX
      BRANCH="$CI_COMMIT_REF_NAME"
      CATEGORY=$(echo "$BRANCH" | cut -d'/' -f2)
      VERSION=$(echo "$BRANCH" | cut -d'/' -f3)
      
      echo "Branch:   $BRANCH"
      echo "Category: $CATEGORY"
      echo "Version:  $VERSION"
      
      # Locate the FBX file
      FBX_PATH="parts/${CATEGORY}/${VERSION}/${CATEGORY}_${VERSION}.fbx"
      
      if [ ! -f "$FBX_PATH" ]; then
        echo "❌ ERROR: FBX file not found at $FBX_PATH"
        exit 1
      fi
      
      echo "FBX Path: $FBX_PATH"
      echo ""
      
      # Step 1: Extract FBX data using headless Blender
      echo "Running Blender extraction..."
      EXTRACT_OUTPUT=$(blender --background --python scripts/blender_extract_validate.py -- "$FBX_PATH" 2>/dev/null)
      
      # Save extracted JSON to a temp file
      echo "$EXTRACT_OUTPUT" | sed -n '/RESULT_START/,/RESULT_END/p' | grep -v 'RESULT_START\|RESULT_END' > /tmp/extracted.json
      
      if [ ! -s /tmp/extracted.json ]; then
        echo "❌ ERROR: Blender extraction produced no output"
        echo "Blender output:"
        echo "$EXTRACT_OUTPUT"
        exit 1
      fi
      
      echo "Extraction complete."
      echo ""
      
      # Step 2: Run validation checks
      python3 scripts/ci_validate.py /tmp/extracted.json "$CATEGORY" "$FBX_PATH"

# ── Stage 2: Generate a thumbnail of the validated part ──────────
generate_thumbnail:
  stage: thumbnail
  image: nytimes/blender:3.3.1-cpu-ubuntu18.04
  rules:
    - if: '$CI_COMMIT_REF_NAME =~ /^submit\//'
  before_script:
    - apt-get update -qq && apt-get install -y -qq python3 git > /dev/null 2>&1
  script:
    - |
      BRANCH="$CI_COMMIT_REF_NAME"
      CATEGORY=$(echo "$BRANCH" | cut -d'/' -f2)
      VERSION=$(echo "$BRANCH" | cut -d'/' -f3)
      FBX_PATH="parts/${CATEGORY}/${VERSION}/${CATEGORY}_${VERSION}.fbx"
      THUMB_PATH="parts/${CATEGORY}/${VERSION}/thumbnail.png"
      
      echo "Generating thumbnail for $CATEGORY $VERSION..."
      blender --background --python scripts/blender_render_thumbnail.py -- "$FBX_PATH" "$CATEGORY" "$THUMB_PATH" 2>/dev/null || true
      
      if [ ! -f "$THUMB_PATH" ]; then
        echo "WARNING: Thumbnail generation failed, continuing without thumbnail."
        exit 0
      fi
      
      THUMB_SIZE=$(stat -c%s "$THUMB_PATH" 2>/dev/null || echo "unknown")
      echo "Thumbnail generated at $THUMB_PATH ($THUMB_SIZE bytes)"
      
      # Commit the thumbnail back to the branch
      # Must checkout branch first (CI clones in detached HEAD)
      git checkout -B "$BRANCH"
      git config user.name "MechaLaunchPad CI"
      git config user.email "ci@mechalaunchpad.local"
      git add "$THUMB_PATH"
      git commit -m "CI: Add thumbnail for ${CATEGORY} ${VERSION}" || echo "Nothing to commit"
      
      # Push using GITLAB_PAT (CI/CD variable) for proper auth
      if [ -n "$GITLAB_PAT" ]; then
        git push "https://oauth2:${GITLAB_PAT}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git" "$BRANCH" || echo "Push failed"
        echo "THUMBNAIL_URL=${CI_PROJECT_URL}/-/raw/${BRANCH}/${THUMB_PATH}"
      else
        echo "WARNING: GITLAB_PAT not set, cannot push thumbnail."
      fi
  artifacts:
    paths:
      - "parts/*/v*/thumbnail.png"
    expire_in: 30 days

# -- Stage 3: Auto-create and merge MR to main -------------------
auto_merge:
  stage: merge_request
  image: alpine:latest
  rules:
    - if: '$CI_COMMIT_REF_NAME =~ /^submit\//'
  before_script:
    - apk add --no-cache curl jq
  script:
    - |
      BRANCH="$CI_COMMIT_REF_NAME"
      CATEGORY=$(echo "$BRANCH" | cut -d'/' -f2)
      VERSION=$(echo "$BRANCH" | cut -d'/' -f3)
      
      if [ -z "$GITLAB_PAT" ]; then
        echo "ERROR: GITLAB_PAT CI/CD variable not set. Cannot create MR."
        echo "Add your GitLab PAT as a CI/CD variable named GITLAB_PAT in project settings."
        exit 1
      fi
      
      echo "Creating Merge Request: $BRANCH -> main"
      
      # Create MR using GITLAB_PAT (project CI/CD variable)
      MR_RESPONSE=$(curl -s --request POST \
        --header "PRIVATE-TOKEN: ${GITLAB_PAT}" \
        "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/merge_requests" \
        --data-urlencode "source_branch=${BRANCH}" \
        --data-urlencode "target_branch=main" \
        --data-urlencode "title=CI: Merge ${CATEGORY} ${VERSION}" \
        --data-urlencode "remove_source_branch=true" \
        --data-urlencode "squash=false")
      
      MR_IID=$(echo "$MR_RESPONSE" | jq -r '.iid // empty')
      
      if [ -z "$MR_IID" ]; then
        echo "MR creation response: $MR_RESPONSE"
        # Try to find existing MR
        MR_IID=$(curl -s \
          --header "PRIVATE-TOKEN: ${GITLAB_PAT}" \
          "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/merge_requests?source_branch=${BRANCH}&state=opened" \
          | jq -r '.[0].iid // empty')
      fi
      
      if [ -n "$MR_IID" ]; then
        echo "MR !${MR_IID} created/found. Setting to auto-merge when pipeline succeeds..."
        
        # Set MR to auto-merge when pipeline completes
        # Cannot merge immediately because THIS job is part of the running pipeline
        MERGE_RESULT=$(curl -s --request PUT \
          --header "PRIVATE-TOKEN: ${GITLAB_PAT}" \
          "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/merge_requests/${MR_IID}/merge" \
          --data "merge_when_pipeline_succeeds=true" \
          --data "should_remove_source_branch=true")
        
        MERGE_STATE=$(echo "$MERGE_RESULT" | jq -r '.state // .message // empty')
        echo "Auto-merge result: $MERGE_STATE"
        echo "MR !${MR_IID} will auto-merge to main when this pipeline finishes."
      else
        echo "Could not create or find MR for $BRANCH"
        exit 1
      fi

# ── Stage 4: Deploy to Unity (mocked — runs on main after merge) ─
deploy_to_engine:
  stage: deploy
  rules:
    - if: '$CI_COMMIT_REF_NAME == "main"'
      when: always
  script:
    - |
      echo "============================================"
      echo "  Deploy to Unity (Simulated)"
      echo "============================================"
      echo "Would scan for new FBX assets in parts/..."
      echo "Would clone Unity game repo..."
      echo "Would copy new assets to Assets/Models/{Category}/"
      echo "Would run Unity -batchmode to create prefabs + assign materials"
      echo "Deploy simulation complete."
      echo ""
      echo "✅ All pipeline stages completed successfully."
'''


# ── Script Logic ───────────────────────────────────────────────────

def push_file_to_gitlab(base_url, headers, filepath_in_repo, content, commit_message):
    """Pushes a single file to the GitLab repo via the Files API."""
    import urllib.parse
    encoded_path = urllib.parse.quote(filepath_in_repo, safe='')
    api_url = f"{base_url}/repository/files/{encoded_path}"
    
    data = {
        "branch": "main",
        "commit_message": commit_message,
        "content": content,
    }
    
    # Try creating first, then update if exists
    res = requests.post(api_url, headers=headers, json=data)
    
    if res.status_code == 400 and "exists" in res.text.lower():
        # File exists, update it
        res = requests.put(api_url, headers=headers, json=data)
    
    if res.status_code in (200, 201):
        print(f"  [OK] {filepath_in_repo}")
        return True
    else:
        print(f"  [FAIL] {filepath_in_repo} -- {res.status_code}: {res.text[:200]}")
        return False


def read_local_file(path):
    """Reads a local file as text."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def setup_gitlab_ci():
    load_dotenv()
    
    gitlab_url = os.getenv("GITLAB_URL")
    project_id = os.getenv("GITLAB_PROJECT_ID")
    token = os.getenv("GITLAB_PAT")
    
    if not all([gitlab_url, project_id, token]):
        print("[FAIL] Missing GitLab environment variables (GITLAB_URL, GITLAB_PROJECT_ID, GITLAB_PAT).")
        return False
    
    # Extract base URL
    if gitlab_url and gitlab_url.count('/') > 2:
        parts = gitlab_url.split('/')
        base_gitlab = f"{parts[0]}//{parts[2]}"
    else:
        base_gitlab = "https://gitlab.com"
    
    base_url = f"{base_gitlab}/api/v4/projects/{project_id}"
    headers = {"PRIVATE-TOKEN": token}
    
    # Resolve paths relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define files to push
    files_to_push = [
        {
            "remote_path": ".gitlab-ci.yml",
            "content": GITLAB_CI_YAML.strip(),
            "message": "CI: Update pipeline with real validation + thumbnail generation",
        },
        {
            "remote_path": "scripts/blender_extract_validate.py",
            "local_path": os.path.join(project_root, "scripts", "blender_extract_validate.py"),
            "message": "CI: Add Blender FBX extraction script",
        },
        {
            "remote_path": "scripts/ci_validate.py",
            "local_path": os.path.join(project_root, "scripts", "ci_validate.py"),
            "message": "CI: Add standalone validation runner",
        },
        {
            "remote_path": "scripts/blender_render_thumbnail.py",
            "local_path": os.path.join(project_root, "scripts", "blender_render_thumbnail.py"),
            "message": "CI: Add headless thumbnail renderer",
        },
        {
            "remote_path": "validation/part_registry.json",
            "local_path": os.path.join(project_root, "validation", "part_registry.json"),
            "message": "CI: Update part registry with current tri limits",
        },
    ]
    
    print(f"\n{'=' * 50}")
    print(f"  Pushing CI Pipeline to GitLab")
    print(f"  Project ID: {project_id}")
    print(f"{'=' * 50}\n")
    
    success_count = 0
    for file_info in files_to_push:
        if "content" in file_info:
            content = file_info["content"]
        else:
            local_path = file_info["local_path"]
            if not os.path.exists(local_path):
                print(f"  ❌ {file_info['remote_path']} — local file not found: {local_path}")
                continue
            content = read_local_file(local_path)
        
        if push_file_to_gitlab(base_url, headers, file_info["remote_path"], content, file_info["message"]):
            success_count += 1
    
    total = len(files_to_push)
    print(f"\n{'=' * 50}")
    if success_count == total:
        print(f"  [OK] All {total} files pushed successfully!")
    else:
        print(f"  [WARN] {success_count}/{total} files pushed. Check errors above.")
    print(f"{'=' * 50}\n")
    
    return success_count == total


if __name__ == "__main__":
    success = setup_gitlab_ci()
    sys.exit(0 if success else 1)
