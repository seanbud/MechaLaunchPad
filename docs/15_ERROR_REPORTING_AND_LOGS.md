# 15 — Error Reporting and Logs

## Unified Error Format

All errors — from local preflight, CI validation, Unity import, and git operations — use a consistent structure.

### Error Object

```python
@dataclass
class PipelineError:
    source: str        # "preflight", "ci_validate", "unity_import", "git", "api"
    rule_id: str       # e.g. "MAT_WHITELIST", "GIT_PUSH_FAILED", "UNITY_IMPORT"
    severity: str      # "ERROR", "WARNING", "INFO"
    message: str       # Human-readable explanation
    details: dict      # Context-specific data
    timestamp: str     # ISO 8601
    fix_hint: str      # Actionable suggestion for the artist
```

### JSON Representation

```json
{
  "source": "preflight",
  "rule_id": "TRI_COUNT",
  "severity": "ERROR",
  "message": "LeftArm has 18,200 triangles, exceeding the limit of 15,000.",
  "details": {
    "count": 18200,
    "max": 15000
  },
  "timestamp": "2025-03-15T10:30:12Z",
  "fix_hint": "Reduce mesh complexity in Blender (Decimate modifier or manual cleanup)."
}
```

---

## Severity Levels

| Level | Icon | Colour | Effect |
|---|---|---|---|
| `ERROR` | ❌ | Red | Blocks publish / fails pipeline |
| `WARNING` | ⚠️ | Yellow | Shown but does not block |
| `INFO` | ℹ️ | Blue | Informational |

---

## Display in PySide6

### Import / Validate Tab

Errors are shown in a `QTreeWidget`:

```
─ ❌ TRI_COUNT — LeftArm exceeds triangle limit
  └─ Count: 18,200 / 15,000
  └─ Fix: Reduce complexity in Blender

─ ✅ NAMING_VALID — File name matches pattern

─ ✅ TRI_COUNT — 12,340 / 15,000 (82%)

─ ⚠️ BONE_SET_VALID — 2 meshes on non-allowed bones (will be stripped)
  └─ GuideHead_Visor → mixamorig:Head (not in LeftArm set)
  └─ GuideTorso_Plate → mixamorig:Spine2 (not in LeftArm set)
```

### CI Status Tab

CI errors are fetched from `validation_report.json` (artifact) and displayed in the same tree format, prefixed with the source:

```
Pipeline #41 — ❌ FAILED

─ Stage: validate — ❌
  └─ ❌ TRI_COUNT — LeftArm exceeds triangle limit
     └─ Fix: Reduce complexity in Blender

─ Stage: unity_ingest — ⏭ SKIPPED

─ Stage: report — ⏭ SKIPPED
```

---

## Log File

MechaLaunchPad writes a local log file for debugging:

```
~/.mechalaunchpad/logs/mechalaunchpad.log
```

### Format

```
2025-03-15 10:30:12 [INFO]  Application started
2025-03-15 10:30:15 [INFO]  Template exported: LeftArm_Template_v001.fbx
2025-03-15 10:31:02 [INFO]  FBX imported: LeftArm_v001.fbx
2025-03-15 10:31:05 [ERROR] TRI_COUNT: LeftArm has 18,200 triangles, exceeding the limit of 15,000.
2025-03-15 10:32:00 [INFO]  Preflight passed (8/8 checks)
2025-03-15 10:32:10 [INFO]  Publishing LeftArm v001...
2025-03-15 10:32:15 [INFO]  Pushed to submit/LeftArm/v001 (sha: abc123)
2025-03-15 10:32:20 [INFO]  Pipeline #42 triggered
```

### Implementation

```python
import logging

logger = logging.getLogger("mechalaunchpad")
handler = logging.FileHandler("~/.mechalaunchpad/logs/mechalaunchpad.log")
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
```

---

## Error Examples by Source

### Preflight Errors

| Rule ID | Example Message |
|---|---|
| `NAMING_VALID` | Filename "leftarm_01.fbx" does not match pattern. |
| `MAT_WHITELIST` | Material "Chrome" not in approved set. |
| `MAT_NO_EMPTY_SLOTS` | Mesh "Plate_02" has empty material slot at index 1. |
| `TRI_COUNT` | LeftArm has 18,200 tris, limit is 15,000. Reduce by 3,200. |
| `TRANSFORMS_CLEAN` | Mesh "Panel" has unapplied scale (2.0, 2.0, 2.0). |

### Git Errors

| Rule ID | Example Message |
|---|---|
| `GIT_PUSH_FAILED` | Push rejected: remote ref updated. Pull and retry. |
| `GIT_AUTH_FAILED` | Authentication failed. Check PAT in .env. |
| `GIT_CLONE_FAILED` | Could not clone repo. Check URL and network. |

### CI / Unity Errors

| Rule ID | Example Message |
|---|---|
| `UNITY_IMPORT` | Unity reported: "FBX contains unsupported node type 'Camera'." |
| `PREFAB_GENERATION` | Prefab build failed: missing material asset for M_Glow. |
| `THUMBNAIL_RENDER` | Camera render returned 0-byte image. |

### API Errors

| Rule ID | Example Message |
|---|---|
| `API_AUTH` | GitLab API returned 401. Token may be expired. |
| `API_NOT_FOUND` | Pipeline not found for ref submit/LeftArm/v001. |
| `API_RATE_LIMIT` | Rate limited. Retrying in 60 seconds. |
