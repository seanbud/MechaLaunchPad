# 11 — GitLab CI Pipeline

## Pipeline Stages

```
validate  ──►  unity_ingest  ──►  report
```

| Stage | Runner | Purpose |
|---|---|---|
| `validate` | Docker (Python 3.11 + Blender) | Run all validation rules |
| `unity_ingest` | Shell runner with Unity installed | Import FBX, generate prefab, render thumbnail |
| `report` | Docker (Python) | Aggregate results, upload artifacts, update status |

---

## `.gitlab-ci.yml`

```yaml
stages:
  - validate
  - unity_ingest
  - report

variables:
  PART_CATEGORY: ""      # Set dynamically from commit metadata
  ASSET_VERSION: ""
  CONFIG_DIR: "config"

# ────────────────────────────────────────────────────────────
# Detect part + version from branch name: submit/<Part>/<version>
# ────────────────────────────────────────────────────────────
.parse_branch: &parse_branch
  - export PART_CATEGORY=$(echo $CI_COMMIT_BRANCH | cut -d'/' -f2)
  - export ASSET_VERSION=$(echo $CI_COMMIT_BRANCH | cut -d'/' -f3)
  - export FBX_PATH="parts/${PART_CATEGORY}/${ASSET_VERSION}/${PART_CATEGORY}_${ASSET_VERSION}.fbx"
  - echo "Part=$PART_CATEGORY  Version=$ASSET_VERSION  FBX=$FBX_PATH"

workflow:
  rules:
    - if: '$CI_COMMIT_BRANCH =~ /^submit\//'

# ──────────────────────────────
# Stage 1: Validate
# ──────────────────────────────
validate:
  stage: validate
  image: registry.gitlab.com/mechalaunchpad/ci-blender:latest
  before_script:
    - *parse_branch
    - pip install -r requirements.txt
  script:
    - python scripts/ci_validate.py "$FBX_PATH" "$PART_CATEGORY" "$CONFIG_DIR"
  artifacts:
    paths:
      - validation_report.json
    when: always
    expire_in: 30 days

# ──────────────────────────────
# Stage 2: Unity Ingest
# ──────────────────────────────
unity_ingest:
  stage: unity_ingest
  tags:
    - unity       # Requires a runner with Unity installed
  needs:
    - job: validate
      artifacts: true
  before_script:
    - *parse_branch
  script:
    - |
      # Copy FBX into Unity project
      cp "$FBX_PATH" "unity-project/Assets/MechParts/${PART_CATEGORY}/"

      # Run Unity in batchmode
      Unity -batchmode -nographics -projectPath unity-project \
        -executeMethod MechPartImporter.ImportAndBuild \
        -part "$PART_CATEGORY" \
        -version "$ASSET_VERSION" \
        -logFile unity_import_log.txt \
        -quit

      # Verify outputs exist
      test -f "unity-project/Assets/Prefabs/${PART_CATEGORY}_${ASSET_VERSION}.prefab"
      test -f "unity-project/Assets/Thumbnails/${PART_CATEGORY}_${ASSET_VERSION}.png"
  artifacts:
    paths:
      - unity_import_log.txt
      - "unity-project/Assets/Prefabs/${PART_CATEGORY}_${ASSET_VERSION}.prefab"
      - "unity-project/Assets/Thumbnails/${PART_CATEGORY}_${ASSET_VERSION}.png"
    when: always
    expire_in: 30 days
  allow_failure: false

# ──────────────────────────────
# Stage 3: Report
# ──────────────────────────────
report:
  stage: report
  image: python:3.11-slim
  needs:
    - job: validate
      artifacts: true
    - job: unity_ingest
      artifacts: true
  script:
    - python scripts/ci_report.py
  artifacts:
    paths:
      - validation_report.json
      - preview.png
      - unity_import_log.txt
      - ci_report.json
    when: always
    expire_in: 90 days
```

---

## CI Docker Image

The `validate` stage uses a custom Docker image with:

- Python 3.11
- Blender 4.x (headless)
- Project `requirements.txt` dependencies

Dockerfile:

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    blender \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
```

---

## Artifacts Summary

| Artifact | Produced By | Consumed By |
|---|---|---|
| `validation_report.json` | `validate` | `report`, MechaLaunchPad (via API) |
| `unity_import_log.txt` | `unity_ingest` | `report`, debugging |
| `*.prefab` | `unity_ingest` | Unity project |
| `*.png` (thumbnail) | `unity_ingest` | `report`, MechaLaunchPad preview |
| `ci_report.json` | `report` | MechaLaunchPad (via API) |

---

## MVP Simplification

For the one-day build:

- **`validate`** stage runs fully with all Python-based rules.
- **`unity_ingest`** stage is **stubbed**: the script creates a dummy prefab and a placeholder thumbnail. The stage structure is real; the Unity call is mocked.
- **`report`** stage aggregates whatever is available.

This lets the pipeline run end-to-end even without a Unity runner.

### Stubbed Unity Ingest Script

```python
# scripts/ci_unity_ingest_stub.py
import os, sys, json

part = sys.argv[1]
version = sys.argv[2]

# Create dummy outputs
prefab_dir = f"unity-project/Assets/Prefabs/"
thumb_dir = f"unity-project/Assets/Thumbnails/"
os.makedirs(prefab_dir, exist_ok=True)
os.makedirs(thumb_dir, exist_ok=True)

# Dummy prefab (YAML placeholder)
with open(f"{prefab_dir}{part}_{version}.prefab", 'w') as f:
    f.write(f"# Stub prefab for {part} {version}\n")

# Dummy thumbnail (1×1 PNG)
import struct, zlib
def make_minimal_png(path):
    # Minimal valid 1x1 white PNG
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    # ... simplified for illustration
    with open(path, 'wb') as f:
        f.write(sig)  # In reality, write a complete minimal PNG

make_minimal_png(f"{thumb_dir}{part}_{version}.png")

# Write import log
with open("unity_import_log.txt", 'w') as f:
    f.write(f"[STUB] Unity import simulated for {part} {version}\n")
    f.write("Status: SUCCESS (stubbed)\n")

print(f"Stub ingest complete for {part} {version}")
```
