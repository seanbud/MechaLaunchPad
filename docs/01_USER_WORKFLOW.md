# 01 — User Workflow

## Overview

The artist interacts exclusively through MechaLaunchPad and Blender. They never touch Git, CI configs, or Unity directly.

---

## Step-by-Step Flow

### 1. Choose Part Category & Export Template

1. Open MechaLaunchPad → **Export Template** tab.
2. Select part category from dropdown (e.g. `LeftArm`).
3. Click **Export Template**.
4. Tool generates `LeftArm_Template_v001.fbx` in a chosen directory.
   - Contains: full mech armature, all animations, all guide meshes (locked/greyed), meshes for other limbs marked as `GUIDE_*`.

### 2. Author in Blender

1. Open the template FBX in Blender.
2. Guide meshes for other parts are in a locked `GUIDE` collection — visible but not selectable.
3. Replace meshes inside the `LeftArm` collection:
   - Delete placeholder meshes.
   - Model / kitbash new meshes.
   - Parent each new mesh to the correct bone (rigid — no Armature modifier, just parent-to-bone).
4. Assign **only** approved materials: `M_Metal`, `M_Plastic`, `M_Glow`, `M_Detail`, `M_Decal`.
5. Save as `.blend`; export FBX via Blender's FBX exporter with the settings described in [04_TEMPLATE_EXPORT_FROM_BLENDER.md](04_TEMPLATE_EXPORT_FROM_BLENDER.md).

### 3. Import & Validate Locally

1. Return to MechaLaunchPad → **Import / Validate** tab.
2. Browse to the exported FBX (or drag-drop).
3. Tool auto-detects part category from filename or metadata.
4. Click **Run Preflight**.
5. Results appear inline:
   - ✅ Green checks for passing rules.
   - ❌ Red errors with fix instructions.
6. Artist fixes issues in Blender and re-imports until all checks pass.

### 4. Preview Stitched Mech

1. Switch to **Preview** tab.
2. The tool renders the full mech by stitching the new LeftArm with the latest approved versions of other parts (or placeholder proxies).
3. (Future) Toggle accessories on attachment slots.

### 5. Publish

1. Switch to **Publish** tab.
2. Fill in:
   - **Version** (auto-incremented, e.g. `v002`).
   - **Commit message** (free text).
3. Click **Publish**.
4. Tool copies the validated FBX + metadata JSON into the local repo clone, commits, and pushes to GitLab.

### 6. Monitor CI

1. Switch to **CI Status** tab.
2. Pipeline appears with stages: `validate → unity_ingest → report`.
3. On success: green badge, link to artifacts (thumbnail, prefab log).
4. On failure: red badge, failure reasons displayed inline with rule IDs and messages.

---

## Happy Path Example

```
Artist opens MechaLaunchPad
  → Exports LeftArm template
  → Opens in Blender, models a "Gundam-style" forearm
  → Parents meshes to mixamorig:LeftForeArm, mixamorig:LeftHand
  → Uses M_Metal + M_Glow
  → Exports FBX
  → Imports into MechaLaunchPad
  → Preflight: ✅ all 8 checks pass
  → Preview: looks great stitched with placeholder torso/head
  → Publishes as v001
  → CI runs: validate ✅ → unity_ingest ✅ → report ✅
  → CI Status tab shows green, thumbnail visible
```

## Failure Path Example

```
Artist exports FBX with a typo: material named "M_Metall"
  → Imports into MechaLaunchPad
  → Preflight:
      ❌ MAT_NAME_MISMATCH: Material "M_Metall" is not in the
         approved set [M_Metal, M_Plastic, M_Glow, M_Detail, M_Decal].
         Fix: rename the material to the closest match.
  → Publish button is disabled (blocking error)
  → Artist fixes in Blender, re-exports
  → Preflight: ✅ all checks pass
  → Proceeds to publish
```

---

## Key Principles

- **Publish button is gated**: cannot click until local preflight passes.
- **CI is source of truth**: local checks are a fast subset; CI can catch additional issues (Unity import errors).
- **Idempotent re-publish**: artist can re-publish the same part+version; the tool overwrites the previous commit on the same branch.
