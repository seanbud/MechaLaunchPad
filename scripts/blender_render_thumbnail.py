"""
Headless Blender Thumbnail Renderer — For GitLab CI.

Imports an FBX, isolates meshes belonging to the target category by
hiding all others, auto-frames a camera using bounding box, and renders
a 256x256 transparent PNG thumbnail.

Usage (run inside Blender headless):
    blender --background --python blender_render_thumbnail.py -- <fbx_path> <category> <output_png>
"""

import bpy
import sys
import os
import json
import math
from mathutils import Vector


def load_part_registry():
    """Loads the part_registry.json from the repo root."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    registry_path = os.path.join(script_dir, "..", "validation", "part_registry.json")
    
    if not os.path.exists(registry_path):
        print(f"WARNING: part_registry.json not found at {registry_path}")
        return {}
    
    with open(registry_path, "r") as f:
        return json.load(f)


def isolate_category_meshes(category, registry):
    """
    Hides all meshes that don't belong to the target category.
    Returns True if any meshes remain visible.
    """
    part_config = registry.get(category, {})
    allowed_bones = set(part_config.get("bones", []))
    
    visible_count = 0
    
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            parent_bone = ""
            if obj.parent and obj.parent_type == 'BONE':
                parent_bone = obj.parent_bone
            
            if parent_bone in allowed_bones:
                obj.hide_render = False
                obj.hide_set(False)
                visible_count += 1
            else:
                obj.hide_render = True
                obj.hide_set(True)
        elif obj.type == 'ARMATURE':
            # Keep armature visible but hide it from render
            obj.hide_render = True
            obj.hide_set(False)
        elif obj.type not in ('CAMERA', 'LIGHT'):
            obj.hide_render = True
            obj.hide_set(True)
    
    print(f"  Isolated {visible_count} meshes belonging to '{category}'")
    return visible_count > 0


def get_visible_bounds():
    """
    Computes the combined bounding box of all visible mesh objects.
    Returns (min_corner, max_corner) as Vector tuples.
    """
    min_corner = Vector((float('inf'), float('inf'), float('inf')))
    max_corner = Vector((float('-inf'), float('-inf'), float('-inf')))
    
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and not obj.hide_render:
            # Get world-space bounding box corners
            for corner in obj.bound_box:
                world_corner = obj.matrix_world @ Vector(corner)
                min_corner.x = min(min_corner.x, world_corner.x)
                min_corner.y = min(min_corner.y, world_corner.y)
                min_corner.z = min(min_corner.z, world_corner.z)
                max_corner.x = max(max_corner.x, world_corner.x)
                max_corner.y = max(max_corner.y, world_corner.y)
                max_corner.z = max(max_corner.z, world_corner.z)
    
    return min_corner, max_corner


def setup_camera(min_corner, max_corner):
    """
    Creates and positions a camera to frame the bounding box.
    Uses a 3/4 front angle (30° elevation, 45° azimuth).
    """
    center = (min_corner + max_corner) / 2
    size = max_corner - min_corner
    max_dim = max(size.x, size.y, size.z, 0.001)
    
    # Camera distance: enough to fit the bounding box with padding
    # FOV is roughly 39.6° for default 50mm lens
    fov_rad = math.radians(39.6)
    distance = (max_dim * 1.4) / (2 * math.tan(fov_rad / 2))
    distance = max(distance, 1.0)
    
    # 3/4 angle: 30° elevation, 45° azimuth
    elevation = math.radians(30)
    azimuth = math.radians(45)
    
    cam_x = center.x + distance * math.cos(elevation) * math.sin(azimuth)
    cam_y = center.y - distance * math.cos(elevation) * math.cos(azimuth)
    cam_z = center.z + distance * math.sin(elevation)
    
    # Create or get camera
    if "ThumbnailCam" in bpy.data.objects:
        cam_obj = bpy.data.objects["ThumbnailCam"]
    else:
        cam_data = bpy.data.cameras.new("ThumbnailCam")
        cam_obj = bpy.data.objects.new("ThumbnailCam", cam_data)
        bpy.context.scene.collection.objects.link(cam_obj)
    
    cam_obj.location = (cam_x, cam_y, cam_z)
    
    # Point camera at the center
    direction = Vector((center.x - cam_x, center.y - cam_y, center.z - cam_z))
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    
    # Set as active camera
    bpy.context.scene.camera = cam_obj
    
    print(f"  Camera placed at ({cam_x:.2f}, {cam_y:.2f}, {cam_z:.2f})")
    print(f"  Looking at center ({center.x:.2f}, {center.y:.2f}, {center.z:.2f})")
    print(f"  Distance: {distance:.2f}, Max dimension: {max_dim:.2f}")
    
    return cam_obj


def setup_lighting():
    """Sets up a simple 3-point light rig for a clean studio look."""
    # Remove existing lights
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)
    
    # Key light (warm, strong)
    key_data = bpy.data.lights.new("KeyLight", type='SUN')
    key_data.energy = 3.0
    key_data.color = (1.0, 0.95, 0.9)
    key_obj = bpy.data.objects.new("KeyLight", key_data)
    key_obj.rotation_euler = (math.radians(50), math.radians(10), math.radians(-40))
    bpy.context.scene.collection.objects.link(key_obj)
    
    # Fill light (cool, softer)
    fill_data = bpy.data.lights.new("FillLight", type='SUN')
    fill_data.energy = 1.0
    fill_data.color = (0.85, 0.9, 1.0)
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    fill_obj.rotation_euler = (math.radians(40), math.radians(-10), math.radians(60))
    bpy.context.scene.collection.objects.link(fill_obj)
    
    # Rim light (white, accent)
    rim_data = bpy.data.lights.new("RimLight", type='SUN')
    rim_data.energy = 2.0
    rim_data.color = (1.0, 1.0, 1.0)
    rim_obj = bpy.data.objects.new("RimLight", rim_data)
    rim_obj.rotation_euler = (math.radians(20), math.radians(0), math.radians(160))
    bpy.context.scene.collection.objects.link(rim_obj)


def setup_render(output_path):
    """Configures render settings for a fast transparent thumbnail."""
    scene = bpy.context.scene
    
    # Use Cycles with CPU — EEVEE requires GPU/OpenGL which headless containers lack
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16  # Low samples for speed, 256x256 doesn't need much
    
    # Resolution
    scene.render.resolution_x = 256
    scene.render.resolution_y = 256
    scene.render.resolution_percentage = 100
    
    # Transparent background
    scene.render.film_transparent = True
    
    # Output settings
    scene.render.filepath = output_path
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.compression = 50
    
    # Performance — disable what we don't need
    scene.render.use_motion_blur = False
    
    # Set a neutral world background (won't show with transparent)
    if scene.world is None:
        scene.world = bpy.data.worlds.new("ThumbnailWorld")
    scene.world.use_nodes = False
    scene.world.color = (0.05, 0.05, 0.06)


def render_thumbnail(fbx_path, category, output_path):
    """Main function: import FBX, isolate part, frame camera, render."""
    print(f"\n{'=' * 50}")
    print(f"  THUMBNAIL GENERATOR")
    print(f"  Category: {category}")
    print(f"  FBX: {os.path.basename(fbx_path)}")
    print(f"{'=' * 50}\n")
    
    # 1. Reset scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # 2. Import FBX
    print("  Importing FBX...")
    try:
        bpy.ops.import_scene.fbx(filepath=fbx_path)
    except Exception as e:
        print(f"  ERROR: Failed to import FBX: {e}")
        return False
    
    # 3. Load registry and isolate meshes
    print("  Isolating category meshes...")
    registry = load_part_registry()
    has_meshes = isolate_category_meshes(category, registry)
    
    if not has_meshes:
        print("  WARNING: No meshes found for this category. Rendering empty scene.")
    
    # 4. Compute bounds and frame camera
    print("  Framing camera...")
    min_corner, max_corner = get_visible_bounds()
    setup_camera(min_corner, max_corner)
    
    # 5. Set up lighting
    print("  Setting up lighting...")
    setup_lighting()
    
    # 6. Configure render
    print("  Configuring render...")
    setup_render(output_path)
    
    # 7. Render
    print("  Rendering thumbnail...")
    bpy.ops.render.render(write_still=True)
    
    if os.path.exists(output_path):
        size_kb = os.path.getsize(output_path) / 1024
        print(f"\n  ✅ Thumbnail saved: {output_path} ({size_kb:.1f} KB)")
        return True
    else:
        print(f"\n  ❌ Render failed — output file not created")
        return False


if __name__ == "__main__":
    try:
        idx = sys.argv.index("--")
        args = sys.argv[idx + 1:]
    except ValueError:
        args = []
    
    if len(args) < 3:
        print("Usage: blender --background --python blender_render_thumbnail.py -- <fbx_path> <category> <output.png>")
        sys.exit(1)
    
    fbx_path = args[0]
    category = args[1]
    output_path = args[2]
    
    success = render_thumbnail(fbx_path, category, output_path)
    if not success:
        sys.exit(1)
