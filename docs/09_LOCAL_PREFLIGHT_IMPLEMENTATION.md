# 09 — Local Preflight Implementation

## Architecture

The validation module is a standalone Python package (`validation/`) with no PySide6 dependency, so it can run both inside the desktop app and as a CLI tool in CI.

```
validation/
├── __init__.py
├── runner.py         # Orchestrates rules, returns ValidationReport
├── result.py         # ValidationResult, ValidationReport dataclasses
├── fbx_parser.py     # Wraps FBX SDK or uses an open-source parser
└── rules/
    ├── __init__.py
    ├── naming.py
    ├── materials.py
    ├── bone_set.py
    ├── bone_hierarchy.py
    ├── tri_count.py
    ├── transforms.py
    └── sockets.py
```

---

## FBX Parsing

### MVP Approach

Use **Blender's Python API** (`bpy`) headless to parse the FBX. This avoids requiring the Autodesk FBX SDK (proprietary).

```python
# fbx_parser.py
import subprocess, json, tempfile

BLENDER_SCRIPT = """
import bpy, json, sys

bpy.ops.import_scene.fbx(filepath=sys.argv[-1])

data = {
    "meshes": [],
    "bones": [],
    "sockets": [],
    "materials": set(),
}

armature = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        armature = obj
        for bone in obj.data.bones:
            data["bones"].append({
                "name": bone.name,
                "parent": bone.parent.name if bone.parent else None,
            })
    elif obj.type == 'MESH':
        mesh_info = {
            "name": obj.name,
            "parent_bone": obj.parent_bone if obj.parent_type == 'BONE' else None,
            "tri_count": sum(len(f.vertices) - 2 for f in obj.data.polygons),
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale),
            "materials": [
                slot.material.name if slot.material else None
                for slot in obj.material_slots
            ],
        }
        data["meshes"].append(mesh_info)
    elif obj.type == 'EMPTY' and obj.name.startswith("SOCKET_"):
        data["sockets"].append({
            "name": obj.name,
            "parent_bone": obj.parent_bone if obj.parent_type == 'BONE' else None,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
        })

# Serialize
json.dump(data, open(sys.argv[-2], 'w'), indent=2, default=list)
"""


def parse_fbx(fbx_path: str) -> dict:
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out_path = f.name

    subprocess.run([
        "blender", "--background", "--python-expr", BLENDER_SCRIPT,
        "--", out_path, fbx_path,
    ], check=True, capture_output=True)

    return json.load(open(out_path))
```

### Future: Pure FBX Parsing

For faster local checks without Blender, migrate to `openfbx` or Autodesk FBX Python SDK.

---

## Validation Runner

```python
# runner.py
from validation.result import ValidationReport, ValidationResult
from validation.rules import (
    naming, materials, bone_set, bone_hierarchy,
    tri_count, transforms, sockets,
)
from validation.fbx_parser import parse_fbx
import json

def run_preflight(fbx_path: str, part_category: str, config_dir: str) -> ValidationReport:
    """Run all local preflight checks. Returns a ValidationReport."""
    registry = json.load(open(f"{config_dir}/part_registry.json"))
    mat_whitelist = json.load(open(f"{config_dir}/material_whitelist.json"))

    fbx_data = parse_fbx(fbx_path)
    part_config = registry[part_category]

    results: list[ValidationResult] = []

    results.append(naming.check(fbx_path, part_category))
    results.append(bone_hierarchy.check(fbx_data, config_dir))
    results.extend(bone_set.check(fbx_data, part_config))
    results.append(tri_count.check(fbx_data, part_config))
    results.extend(transforms.check(fbx_data))
    results.extend(sockets.check(fbx_data, part_config))

    return ValidationReport(
        part_category=part_category,
        fbx_path=fbx_path,
        results=results,
        passed=all(r.severity != "ERROR" or r.passed for r in results),
    )
```

---

## Result Format

```python
# result.py
from dataclasses import dataclass, field, asdict
import json

@dataclass
class ValidationResult:
    rule_id: str           # e.g. "MAT_WHITELIST"
    passed: bool
    severity: str          # "ERROR", "WARNING", "INFO"
    message: str           # Human-readable
    details: dict = field(default_factory=dict)  # Extra data

@dataclass
class ValidationReport:
    part_category: str
    fbx_path: str
    results: list[ValidationResult]
    passed: bool

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    def save(self, path: str):
        with open(path, 'w') as f:
            f.write(self.to_json())
```

### Example JSON Output

```json
{
  "part_category": "LeftArm",
  "fbx_path": "/submissions/LeftArm_v001.fbx",
  "passed": false,
  "results": [
    {
      "rule_id": "NAMING_VALID",
      "passed": true,
      "severity": "INFO",
      "message": "Filename matches pattern.",
      "details": {}
    },
    {
      "rule_id": "TRI_COUNT",
      "passed": false,
      "severity": "ERROR",
      "message": "LeftArm has 18,200 triangles, exceeding the limit of 15,000.",
      "details": {
        "count": 18200,
        "max": 15000
      }
    }
  ]
}
```

---

## Blocking Publish on Failure

The PySide6 Publish tab reads the `ValidationReport`:

```python
# In publish tab
def on_publish_clicked(self):
    report = self._last_report
    if report is None or not report.passed:
        self.publish_button.setEnabled(False)
        self.status_label.setText("Fix validation errors before publishing.")
        return
    # proceed to git ops...
```

The Publish button is disabled by default and only enabled after a successful preflight run.

---

## CLI Entry Point (for CI)

```python
# scripts/ci_validate.py
import sys
from validation.runner import run_preflight

fbx_path = sys.argv[1]
category = sys.argv[2]
config_dir = sys.argv[3]

report = run_preflight(fbx_path, category, config_dir)
report.save("validation_report.json")

sys.exit(0 if report.passed else 1)
```

Usage in CI:
```bash
python scripts/ci_validate.py parts/LeftArm/v001/LeftArm_v001.fbx LeftArm config/
```
