# 14 — Data Formats & Metadata

## Part Metadata JSON

Every submitted part includes a sidecar metadata file alongside the FBX.

### Filename Pattern

```
<PartCategory>_v<NNN>_meta.json
```

### Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "part_category",
    "version",
    "author",
    "created_at",
    "fbx_filename",
    "bone_set",
    "materials_used",
    "tri_count"
  ],
  "properties": {
    "part_category": {
      "type": "string",
      "enum": ["LeftArm", "RightArm", "Head", "Torso", "Legs",
               "HeavyGun", "LightGun", "BladeWeapon", "JetPack"]
    },
    "version": {
      "type": "string",
      "pattern": "^v\\d{3}$"
    },
    "author": {
      "type": "string",
      "description": "GitLab username or display name"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "fbx_filename": {
      "type": "string"
    },
    "bone_set": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Bones that have meshes attached"
    },
    "materials_used": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Subset of approved materials actually used"
    },
    "tri_count": {
      "type": "integer",
      "minimum": 0
    },
    "sockets": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Socket empties present in the file"
    },
    "description": {
      "type": "string",
      "description": "Optional artist notes"
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Optional tags for search/filter"
    }
  }
}
```

### Example

```json
{
  "part_category": "LeftArm",
  "version": "v001",
  "author": "artist_jane",
  "created_at": "2025-03-15T10:00:00Z",
  "fbx_filename": "LeftArm_v001.fbx",
  "bone_set": ["mixamorig:LeftShoulder", "mixamorig:LeftArm", "mixamorig:LeftForeArm", "mixamorig:LeftHand"],
  "materials_used": ["M_Metal", "M_Glow"],
  "tri_count": 12340,
  "sockets": ["SOCKET_L_ARM_WEAPON"],
  "description": "Gundam-inspired heavy forearm plates",
  "tags": ["gundam", "heavy", "angular"]
}
```

---

## Versioning Scheme

```
v<NNN>
```

- **Three-digit zero-padded**: `v001`, `v002`, `v010`.
- **Auto-incremented** by the tool: scans existing versions in the target directory, increments the highest.
- **Immutable**: Once published, a version is never overwritten. To fix, publish `v002`.

### Auto-Increment Logic

```python
def next_version(existing_versions: list[str]) -> str:
    if not existing_versions:
        return "v001"
    nums = [int(v.lstrip("v")) for v in existing_versions]
    return f"v{max(nums) + 1:03d}"
```

---

## `latest.json` (Asset Registry Pointer)

Stored at `mech-assets/latest.json` to quickly resolve the current best version of each part.

```json
{
  "LeftArm": {
    "version": "v002",
    "fbx": "parts/LeftArm/v002/LeftArm_v002.fbx",
    "meta": "parts/LeftArm/v002/LeftArm_v002_meta.json",
    "preview": "parts/LeftArm/v002/LeftArm_v002_preview.png",
    "ci_status": "passed"
  },
  "Head": null,
  "Torso": null,
  "Legs": null,
  "RightArm": null
}
```

Updated by the `report` CI stage after a pipeline succeeds.

---

## Preview Stitching via Metadata

The preview system reads `latest.json` to determine which FBX to load per part category:

```python
def resolve_stitch_parts(latest_path: str) -> dict:
    latest = json.load(open(latest_path))
    parts = {}
    for category, info in latest.items():
        if info and info["ci_status"] == "passed":
            parts[category] = info["fbx"]
        # else: use placeholder from template
    return parts
```

---

## Validation Report JSON

See [09_LOCAL_PREFLIGHT_IMPLEMENTATION.md](09_LOCAL_PREFLIGHT_IMPLEMENTATION.md) for the `ValidationReport` schema.

---

## CI Report JSON

Aggregated by the `report` stage:

```json
{
  "pipeline_id": 42,
  "branch": "submit/LeftArm/v001",
  "overall_status": "passed",
  "stages": {
    "validate": {
      "status": "passed",
      "validation_report": "validation_report.json"
    },
    "unity_ingest": {
      "status": "passed",
      "prefab": "Assets/Prefabs/LeftArm_v001.prefab",
      "thumbnail": "Assets/Thumbnails/LeftArm_v001.png"
    }
  },
  "timestamp": "2025-03-15T10:32:45Z"
}
```

---

## Config Files

### `part_registry.json`

```json
{
  "LeftArm": {
    "bones": ["mixamorig:LeftShoulder", "mixamorig:LeftArm", "mixamorig:LeftForeArm", "mixamorig:LeftHand",
              "mixamorig:LeftHandIndex1", "mixamorig:LeftHandMiddle1", "mixamorig:LeftHandRing1",
              "mixamorig:LeftHandPinky1", "mixamorig:LeftHandThumb1"],
    "max_tris": 15000,
    "required_sockets": ["SOCKET_L_ARM_WEAPON"]
  },
  "Torso": {
    "bones": ["mixamorig:Hips", "mixamorig:Spine", "mixamorig:Spine1", "mixamorig:Spine2"],
    "max_tris": 25000,
    "required_sockets": ["SOCKET_C_BACK_MOUNT"]
  },
  "Head": {
    "bones": ["mixamorig:Neck", "mixamorig:Head", "mixamorig:HeadTop_End"],
    "max_tris": 12000,
    "required_sockets": []
  }
}
```

### `material_whitelist.json`

```json
{
  "approved_materials": [
    "M_Metal",
    "M_Plastic",
    "M_Glow",
    "M_Detail",
    "M_Decal"
  ]
}
```
