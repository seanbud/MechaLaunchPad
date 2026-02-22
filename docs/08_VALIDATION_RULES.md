# 08 — Validation Rules

All rules are identified by a unique `RULE_ID`. The same rule definitions are used by both local preflight and CI.

---

## Local Preflight Rules

### `NAMING_VALID`

| Field | Value |
|---|---|
| **Checks** | Filename matches `<PartCategory>_v<NNN>.fbx` pattern |
| **Why** | Consistent naming is required for pipeline automation, version tracking, and Unity import |
| **Implementation** | Regex: `^(LeftArm|RightArm|Head|Torso|Legs|HeavyGun|LightGun|BladeWeapon|JetPack)_v\d{3}\.fbx$` |
| **Failure message** | `NAMING_VALID: Filename "{name}" does not match required pattern "<Category>_v<NNN>.fbx".` |

---

### `BONE_HIERARCHY_INTACT`

| Field | Value |
|---|---|
| **Checks** | The FBX contains the full canonical armature with correct bone names and hierarchy |
| **Why** | Parts must be interchangeable; a broken hierarchy prevents stitching and animation playback |
| **Implementation** | Parse FBX armature, compare bone names + parent-child relationships against `BasicTemplate.fbx` |
| **Failure message** | `BONE_HIERARCHY_INTACT: Missing bone "{bone}". Expected hierarchy: {expected_parent} → {bone}.` |

---

### `BONE_SET_VALID`

| Field | Value |
|---|---|
| **Checks** | All meshes are parented to bones in the part's allowed bone set; no meshes exist on disallowed bones |
| **Why** | Ensures the submission only contributes geometry to the correct body region |
| **Implementation** | For each mesh, get `parent_bone`. If not in `part_registry[category].bones` → flag for stripping. If zero meshes remain after stripping → error |
| **Failure message** | `BONE_SET_VALID: Mesh "{mesh}" is parented to bone "{bone}" which is not in the allowed set for {category}. It will be stripped.` (warning) / `BONE_SET_VALID: No meshes found on any allowed bone for {category}.` (error) |

---

## Future / Extra Rules (Not in MVP)

### `MAT_WHITELIST`

| Field | Value |
|---|---|
| **Checks** | Every material on every mesh has a name exactly matching the approved set |
| **Why** | Enforces a unified material pipeline |
| **Implementation** | Compare all materials against `material_whitelist.json` |
| **Failure message** | `MAT_WHITELIST: Material "{name}" on mesh "{mesh}" is not in the approved set.` |

### `MAT_NO_EMPTY_SLOTS`

| Field | Value |
|---|---|
| **Checks** | No mesh has an empty / unassigned material slot |
| **Why** | Prevents missing-material errors in Unity |
| **Implementation** | Iterate mesh material slots; check none are `None` |
| **Failure message** | `MAT_NO_EMPTY_SLOTS: Mesh "{mesh}" has an empty material slot at index {index}.` |

### `MAT_NO_DUPLICATES`

| Field | Value |
|---|---|
| **Checks** | No mesh has the same material assigned to more than one slot |
| **Why** | Indicates authoring error |
| **Implementation** | Check for duplicate material names per mesh |
| **Failure message** | `MAT_NO_DUPLICATES: Mesh "{mesh}" has duplicate material "{name}" in multiple slots.` |

---

### `TRI_COUNT`

| Field | Value |
|---|---|
| **Checks** | Total triangle count of meshes on allowed bones ≤ part category limit |
| **Why** | Performance budgets must be respected |
| **Implementation** | Sum face counts (triangulated) for all kept meshes. Compare against `part_registry[category].max_tris` |
| **Failure message** | `TRI_COUNT: {category} has {count} triangles, exceeding the limit of {max}. Reduce by {delta}.` |

---

### `TRANSFORMS_CLEAN`

| Field | Value |
|---|---|
| **Checks** | All meshes have applied transforms (loc=0, rot=0, scale=1); no negative scales, root is identity |
| **Why** | Unapplied transforms cause offset/scale issues in Unity |
| **Implementation** | Read each mesh node's local transform. Verify location ≈ 0, rotation ≈ 0, scale ≈ 1 (tolerance 0.001) |
| **Failure message** | `TRANSFORMS_CLEAN: Mesh "{mesh}" has unapplied transforms (loc={loc}, rot={rot}, scale={scale}). Apply transforms in Blender (Ctrl+A).` |

---

### `SOCKETS_PRESENT`

| Field | Value |
|---|---|
| **Checks** | All required socket empties for the part category are present and within transform tolerance of template |
| **Why** | Accessories depend on sockets being at the correct location |
| **Implementation** | Look up required sockets from `part_registry[category].required_sockets`. Verify each exists as an Empty node. Compare transform against template (pos ±0.01 m, rot ±1°) |
| **Failure message** | `SOCKETS_PRESENT: Required socket "{socket}" is missing or has been moved (delta_pos={dp}, delta_rot={dr}).` |

---

## CI-Only Rules

These run in addition to all local rules.

### `UNITY_IMPORT`

| Field | Value |
|---|---|
| **Checks** | FBX imports into Unity without errors |
| **Why** | Catches issues that only surface during actual Unity import (corrupt data, unsupported features) |
| **Implementation** | Unity batchmode `AssetDatabase.ImportAsset()`, parse console log for errors |
| **Failure message** | `UNITY_IMPORT: Unity import failed with error: "{error}"` |

---

### `PREFAB_GENERATION`

| Field | Value |
|---|---|
| **Checks** | Prefab is successfully created from imported FBX |
| **Why** | Ensures the asset is usable in the game project |
| **Implementation** | Run `MechPartImporter.cs` in batchmode; verify `.prefab` file exists |
| **Failure message** | `PREFAB_GENERATION: Failed to generate prefab for {category}_v{version}: "{error}"` |

---

### `THUMBNAIL_RENDER`

| Field | Value |
|---|---|
| **Checks** | A 512×512 preview thumbnail is rendered from the prefab |
| **Why** | Visual confirmation + catalogue browsing |
| **Implementation** | Unity batchmode camera render; verify output PNG exists and is > 0 bytes |
| **Failure message** | `THUMBNAIL_RENDER: Failed to render thumbnail: "{error}"` |

---

## Rule Severity

| Severity | Effect |
|---|---|
| `ERROR` | Blocks publish (local) or fails pipeline (CI) |
| `WARNING` | Shown to artist but does not block |
| `INFO` | Informational (e.g. tri count usage percentage) |

All rules in the tables above are `ERROR` severity unless noted.
