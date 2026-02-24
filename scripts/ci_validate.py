#!/usr/bin/env python3
"""
CI Validation Runner — Standalone script for GitLab CI.

Runs all validation checks against extracted FBX JSON data.
Zero pip dependencies — uses only Python stdlib so it runs 
cleanly in a Blender Docker container.

Usage:
    python3 ci_validate.py <extracted_json_path> <category>

Exit codes:
    0 = All checks passed
    1 = One or more checks failed
"""

import json
import os
import re
import sys


def load_registry(registry_path):
    """Loads part_registry.json."""
    with open(registry_path, "r") as f:
        return json.load(f)


def load_extracted_data(json_path):
    """Loads the JSON output from blender_extract_validate.py."""
    with open(json_path, "r") as f:
        return json.load(f)


# ── Rule 1: Naming Convention ──────────────────────────────────────

def check_naming(fbx_path, category):
    """Checks if the filename follows the convention: Category_vNNN.fbx"""
    filename = os.path.basename(fbx_path)
    pattern = rf"^{category}_v\d{{3}}\.fbx$"
    
    if re.match(pattern, filename):
        return {
            "rule_id": "NAMING_VALID",
            "passed": True,
            "message": f"Filename '{filename}' follows convention.",
        }
    else:
        return {
            "rule_id": "NAMING_VALID",
            "passed": False,
            "message": f"Filename '{filename}' does not match expected pattern '{category}_v###.fbx'.",
            "fix_hint": f"Rename the file to something like {category}_v001.fbx",
        }


# ── Rule 2: Bone Parenting ─────────────────────────────────────────

def check_bone_set(meshes, part_config, category):
    """Checks if category-filtered meshes are parented to bones."""
    allowed_bones = set(part_config.get("bones", []))
    
    # Filter meshes to only those belonging to this category
    filtered = []
    ignored = 0
    for mesh in meshes:
        parent_bone = mesh.get("parent_bone", "")
        if parent_bone in allowed_bones or not parent_bone:
            filtered.append(mesh)
        else:
            ignored += 1
    
    results = []
    
    if ignored > 0:
        results.append({
            "rule_id": "BONE_SET_FILTER",
            "passed": True,
            "message": f"Category Filtering: Ignored {ignored} meshes belonging to other limbs/bones.",
        })
    
    # Check that filtered meshes have parent bones
    for mesh in filtered:
        parent_bone = mesh.get("parent_bone", "")
        mesh_name = mesh.get("name", "")
        if not parent_bone:
            results.append({
                "rule_id": "BONE_SET_VALID",
                "passed": False,
                "message": f"Mesh '{mesh_name}' has no parent bone. All authored meshes must be parented to a bone.",
                "fix_hint": "Parent the mesh to a bone in Blender (Ctrl+P -> Bone).",
            })
    
    # If no failures, add a pass result
    bone_failures = [r for r in results if r["rule_id"] == "BONE_SET_VALID" and not r["passed"]]
    if not bone_failures:
        if not filtered:
            results.append({
                "rule_id": "BONE_SET_VALID",
                "passed": False,
                "message": f"No meshes found belonging to the {category} category.",
                "fix_hint": "Ensure your meshes are parented to the correct bones for this limb.",
            })
        else:
            results.append({
                "rule_id": "BONE_SET_VALID",
                "passed": True,
                "message": f"All {len(filtered)} identified meshes are parented correctly.",
            })
    
    return results, filtered


# ── Rule 3: Triangle Count ─────────────────────────────────────────

def check_tri_count(filtered_meshes, part_config):
    """Checks total triangle count of filtered meshes against limits."""
    max_tris = part_config.get("max_tris", 999999)
    current_tris = sum(mesh.get("tris", 0) for mesh in filtered_meshes)
    
    if current_tris <= max_tris:
        return {
            "rule_id": "TRI_COUNT",
            "passed": True,
            "message": f"Triangle count ({current_tris:,}) is within limit ({max_tris:,}).",
        }
    else:
        return {
            "rule_id": "TRI_COUNT",
            "passed": False,
            "message": f"Total triangle count ({current_tris:,}) exceeds the limit of {max_tris:,} for this part.",
            "fix_hint": "Reduce polygon count using Decimate modifier or manual cleanup in Blender.",
        }


# ── Main Runner ────────────────────────────────────────────────────

def run_validation(json_path, category, fbx_path):
    """Runs all validation rules and prints structured results."""
    # Resolve registry path relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    registry_path = os.path.join(script_dir, "..", "validation", "part_registry.json")
    
    if not os.path.exists(registry_path):
        print(f"❌ FATAL: part_registry.json not found at {registry_path}")
        return 1
    
    registry = load_registry(registry_path)
    data = load_extracted_data(json_path)
    
    if "error" in data:
        print(f"❌ FATAL: Blender extraction failed: {data['error']}")
        return 1
    
    part_config = registry.get(category)
    if not part_config:
        print(f"❌ FATAL: Unknown part category: {category}")
        print(f"   Valid categories: {', '.join(registry.keys())}")
        return 1
    
    # Run all checks
    all_results = []
    
    # 1. Naming
    all_results.append(check_naming(fbx_path, category))
    
    # 2. Bone Set (also returns filtered meshes for tri count)
    bone_results, filtered_meshes = check_bone_set(data.get("meshes", []), part_config, category)
    all_results.extend(bone_results)
    
    # 3. Tri Count
    all_results.append(check_tri_count(filtered_meshes, part_config))
    
    # Print results
    print("\n" + "=" * 60)
    print(f"  VALIDATION RESULTS — {category}")
    print("=" * 60 + "\n")
    
    pass_count = 0
    fail_count = 0
    
    for r in all_results:
        if r["passed"]:
            print(f"  ✅ PASS [{r['rule_id']}]: {r['message']}")
            pass_count += 1
        else:
            print(f"  ❌ FAIL [{r['rule_id']}]: {r['message']}")
            fail_count += 1
            if r.get("fix_hint"):
                print(f"     Fix: {r['fix_hint']}")
    
    print(f"\n{'=' * 60}")
    total = pass_count + fail_count
    if fail_count == 0:
        print(f"  RESULT: PASSED ({pass_count} of {total} checks passed)")
        print("=" * 60 + "\n")
        return 0
    else:
        print(f"  RESULT: FAILED ({fail_count} of {total} checks failed)")
        print("=" * 60 + "\n")
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 ci_validate.py <extracted_json> <category> [fbx_path]")
        print("  extracted_json: Path to JSON from blender_extract_validate.py")
        print("  category:       Part category (e.g. RightArm, Head, Torso)")
        print("  fbx_path:       Optional, path to original FBX for naming check")
        sys.exit(1)
    
    json_path = sys.argv[1]
    category = sys.argv[2]
    
    # FBX path can be passed separately or inferred from the JSON data
    if len(sys.argv) > 3:
        fbx_path = sys.argv[3]
    else:
        # Try to get filename from the extracted JSON
        with open(json_path, "r") as f:
            data = json.load(f)
        fbx_path = data.get("filename", "unknown.fbx")
    
    exit_code = run_validation(json_path, category, fbx_path)
    sys.exit(exit_code)
