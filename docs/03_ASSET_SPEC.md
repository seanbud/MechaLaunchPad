# 03 — Asset Specification

This document defines the **contract** that every submitted part file must satisfy.

---

## File Format

| Property | Value | Rationale |
|---|---|---|
| Format | FBX (binary, 2020 compat) | Industry standard; Unity/Blender roundtrip |
| Fallback | — | glTF is reserved for future web preview |

---

## Naming Convention

```
<PartCategory>_v<NNN>.fbx
```

- `PartCategory` — PascalCase identifier matching `part_registry.json` (e.g. `LeftArm`, `Head`, `Torso`).
- `v<NNN>` — zero-padded three-digit version (e.g. `v001`).

Examples: `LeftArm_v001.fbx`, `Head_v003.fbx`

---

## Coordinate System & Units

| Property | Value |
|---|---|
| Up axis | Y-up |
| Forward axis | -Z forward |
| Unit | 1 unit = 1 metre |
| Scale | Apply all transforms; root scale = 1.0 |

---

## Rig & Binding Rules

1. **Full armature required** — The FBX must contain the canonical mech armature with every bone, matching the template exactly (names, hierarchy).
2. **Animations included** — All animations from the template must be present (idle, walk, etc.).
3. **Rigid binding only** — Meshes are parented to bones (parent-to-bone). No Armature modifier, no skin weights, no vertex groups used for deformation.
4. **Part bone whitelist** — Only meshes parented to bones in the part's bone set are kept. Meshes on other bones are stripped/ignored during validation.

### Bone Sets (defined in `part_registry.json`)

```json
{
  "Torso": {
    "bones": [
      "mixamorig:Hips",
      "mixamorig:Spine",
      "mixamorig:Spine1",
      "mixamorig:Spine2"
    ]
  },
  "Head": {
    "bones": [
      "mixamorig:Neck",
      "mixamorig:Head",
      "mixamorig:HeadTop_End"
    ]
  },
  "LeftArm": {
    "bones": [
      "mixamorig:LeftShoulder",
      "mixamorig:LeftArm",
      "mixamorig:LeftForeArm",
      "mixamorig:LeftHand",
      "mixamorig:LeftHandThumb1", "mixamorig:LeftHandThumb2", "mixamorig:LeftHandThumb3",
      "mixamorig:LeftHandIndex1", "mixamorig:LeftHandIndex2", "mixamorig:LeftHandIndex3",
      "mixamorig:LeftHandMiddle1", "mixamorig:LeftHandMiddle2", "mixamorig:LeftHandMiddle3",
      "mixamorig:LeftHandRing1", "mixamorig:LeftHandRing2", "mixamorig:LeftHandRing3",
      "mixamorig:LeftHandPinky1", "mixamorig:LeftHandPinky2", "mixamorig:LeftHandPinky3"
    ]
  },
  "RightArm": {
    "bones": [
      "mixamorig:RightShoulder",
      "mixamorig:RightArm",
      "mixamorig:RightForeArm",
      "mixamorig:RightHand",
      "mixamorig:RightHandThumb1", "mixamorig:RightHandThumb2", "mixamorig:RightHandThumb3",
      "mixamorig:RightHandIndex1", "mixamorig:RightHandIndex2", "mixamorig:RightHandIndex3",
      "mixamorig:RightHandMiddle1", "mixamorig:RightHandMiddle2", "mixamorig:RightHandMiddle3",
      "mixamorig:RightHandRing1", "mixamorig:RightHandRing2", "mixamorig:RightHandRing3",
      "mixamorig:RightHandPinky1", "mixamorig:RightHandPinky2", "mixamorig:RightHandPinky3"
    ]
  },
  "Legs": {
    "bones": [
      "mixamorig:LeftUpLeg", "mixamorig:LeftLeg", "mixamorig:LeftFoot", "mixamorig:LeftToeBase",
      "mixamorig:RightUpLeg", "mixamorig:RightLeg", "mixamorig:RightFoot", "mixamorig:RightToeBase"
    ]
  }
}
```

---

## Material Restrictions (Future / Not Validated in MVP)

Artists are expected to use these materials, but **validation is disabled for MVP** to streamline development.

| Material Name | Intended Use |
|---|---|
| `M_Metal` | Primary metallic surfaces |
| `M_Plastic` | Matte / plastic panels |
| `M_Glow` | Emissive accents (lights, visors) |
| `M_Detail` | Fine surface detail / secondary metal |
| `M_Decal` | Flat decal / insignia overlay |

### Validation Rules (Post-MVP)

- ❌ Additional materials beyond the five → fail.
- ❌ Material name differs from whitelist (case-sensitive) → fail.
- ❌ Any material slot on a mesh is empty / unassigned → fail.
- ❌ Duplicate material names on the same mesh → fail.
- ✅ Not all five must be used — a mesh may use a subset.

---

## Texture Constraints (Future — not MVP)

| Property | Requirement |
|---|---|
| Formats | PNG or TGA |
| Max size | 2048 × 2048 |
| Naming | `<MaterialName>_<MapType>.png` (e.g. `M_Metal_BaseColor.png`) |
| Map types | `BaseColor`, `Normal`, `MetallicSmoothness`, `Emissive` |
| Power of two | Required |

> Textures are **not validated in MVP**. Materials in the FBX reference names only; texture files are handled by Unity materials at import time.

---

## Triangle Count Limits

| Part Category | Max Triangles |
|---|---|
| LeftArm | 15 000 |
| RightArm | 15 000 |
| Head | 12 000 |
| Torso | 25 000 |
| Legs | 20 000 |
| Accessory | 8 000 |

Limits are defined in `part_registry.json` and enforced by both local preflight and CI.

---

## Transform Requirements

- All meshes must have **applied** transforms (location 0, rotation 0, scale 1) in their local space before binding to bone.
- Root object transform must be identity.
- No negative scales.
