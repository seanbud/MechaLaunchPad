# 06 — Preview System

## Chosen Implementation: Option A

| Option | Pros | Cons | MVP? |
|---|---|---|---|

```python
import bpy, json

def stitch_and_render(parts_dict, output_path):
    """
    parts_dict: {"LeftArm": "/path/to/LeftArm_v001.fbx", ...}
    Missing keys use placeholder meshes already in template.
    """
    bpy.ops.wm.open_mainfile(filepath="templates/BasicTemplate.blend")

    for part, fbx_path in parts_dict.items():
        # Remove placeholder meshes for this part
        for obj in list(bpy.data.objects):
            if obj.type == 'MESH' and obj.parent_bone in BONE_SETS[part]:
                bpy.data.objects.remove(obj, do_unlink=True)

        # Import submitted part
        bpy.ops.import_scene.fbx(filepath=fbx_path)

        # Re-parent imported meshes to canonical armature
        armature = bpy.data.objects["Armature"]
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                obj.parent = armature
                # parent_bone is preserved from FBX

    # Render
    bpy.context.scene.render.filepath = output_path
    bpy.context.scene.render.resolution_x = 1024
    bpy.context.scene.render.resolution_y = 1024
    bpy.ops.render.render(write_still=True)
```

---

## Fallback Proxies

When a part has no submission yet, the template's placeholder meshes remain. These are simple low-poly stand-ins so the mech is always complete.

| Part | Proxy Source |
|---|---|
| LeftArm | `BasicTemplate.blend` → `LeftArm` collection |
| RightArm | `BasicTemplate.blend` → `RightArm` collection |
| Head | `BasicTemplate.blend` → `Head` collection |
| Torso | `BasicTemplate.blend` → `Torso` collection |
| Legs | `BasicTemplate.blend` → `Legs` collection |

---

## Showing Attachment Slots

Socket empties (e.g. `SOCKET_L_ARM_WEAPON`) are visualised as:
- Small coloured cubes (0.05 m) at the socket location in the render.
- If an accessory is toggled on, the accessory mesh replaces the cube.

---

## Preview Image in UI

The rendered PNG is loaded into the **Preview** tab as a `QPixmap` on a `QLabel`. The image is scaled to fit the available area while maintaining aspect ratio.

### Refresh Flow

1. Artist changes part selection or accessory toggle.
2. Clicks **Re-render**.
3. UI shows spinner overlay.
4. Blender subprocess runs (~5 s).
5. New image replaces old one.

---

## Future: Interactive Viewport

Post-MVP, replace the static image with an embedded 3-D viewport using one of:

- **Qt3D** (built into PySide6) — moderate effort.
- **pyOpenGL** widget — full control, more code.
- **pygfx** (Wgpu-based) — modern, but less mature.

The stitching logic remains the same; only the rendering backend changes.
