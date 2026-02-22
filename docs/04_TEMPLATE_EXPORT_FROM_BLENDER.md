# 04 — Template Export from Blender

## What the Template Contains

The template FBX is generated from `BasicTemplate.blend` and includes:

| Content | Present | Editable by Artist |
|---|---|---|
| Full mech armature (all bones) | ✅ | ❌ |
| All canonical animations (idle, walk, run, etc.) | ✅ | ❌ |
| Guide meshes for **other** parts | ✅ (in `GUIDE` collection) | ❌ (locked) |
| Placeholder meshes for the **selected** part | ✅ (in `<PartCategory>` collection) | ✅ (replace these) |
| Attachment slot empties (sockets) | ✅ | ❌ |

---

## Template Generation Process (MechaLaunchPad)

When the artist clicks **Export Template** for a part category (e.g. `LeftArm`):

1. **Load** `BasicTemplate.blend` via Blender Python (`bpy`), invoked headless.
2. **Tag collections**:
   - Rename the collection holding the selected part's meshes to the part name (e.g. `LeftArm`).
   - Move all other part meshes into a collection named `GUIDE`.
   - Lock the `GUIDE` collection (set `collection.hide_select = True`).
3. **Bone whitelist**: read `part_registry.json` to determine which bones belong to the part.
4. **Export FBX** with specific settings (see below).
5. **Emit** `<PartCategory>_Template_v001.fbx` to the user-specified directory.

### Blender Python Snippet (headless)

```python
import bpy, json, sys

part = sys.argv[-1]  # e.g. "LeftArm"
registry = json.load(open("config/part_registry.json"))

# Lock guide collections
for col in bpy.data.collections:
    if col.name != part and col.name != "Armature":
        col.name = f"GUIDE_{col.name}"
        col.hide_select = True

# Export
bpy.ops.export_scene.fbx(
    filepath=f"/tmp/{part}_Template_v001.fbx",
    use_selection=False,
    bake_anim=True,
    add_leaf_bones=False,
    apply_unit_scale=True,
    axis_forward='-Z',
    axis_up='Y',
    mesh_smooth_type='FACE',
    use_mesh_modifiers=True,
    bake_anim_use_all_actions=True,
)
```

---

## How Stripping Works

When the artist authors a part and re-exports:

1. The artist deletes placeholder meshes in the `LeftArm` collection and replaces them with custom meshes.
2. All custom meshes are parented to bones in the part's bone set.
3. On import into MechaLaunchPad, the tool:
   - Parses the FBX to enumerate all meshes.
   - Checks each mesh's parent bone against the bone whitelist.
   - **Keeps** meshes whose parent bone is in the whitelist.
   - **Strips/ignores** meshes on other bones (these are leftover guide content).

This means the artist doesn't need to manually clean up guide meshes — the pipeline handles it.

---

## FBX Export Settings

These settings must be used by both the template generator and the artist's final export:

| Setting | Value | Why |
|---|---|---|
| `axis_forward` | `-Z` | Unity convention |
| `axis_up` | `Y` | Unity convention |
| `apply_unit_scale` | `True` | Ensures 1 unit = 1 m |
| `use_mesh_modifiers` | `True` | Bakes modifiers (mirror, etc.) |
| `add_leaf_bones` | `False` | Prevents extra bones |
| `bake_anim` | `True` | Includes all animations |
| `bake_anim_use_all_actions` | `True` | All actions, not just active |
| `mesh_smooth_type` | `FACE` | Per-face normals |
| `use_selection` | `False` | Export everything |
| `global_scale` | `1.0` | No additional scaling |

---

## Requirement: Full Rig and Animation Set

The exported FBX must **always** contain:

- The complete armature hierarchy (all bones), even if the part only uses a subset.
- All canonical animation actions.

This is required so that:
- Unity can build a complete prefab from any single part file.
- The preview system can play animations on stitched mechs.
- CI validation can verify bone hierarchy integrity.
