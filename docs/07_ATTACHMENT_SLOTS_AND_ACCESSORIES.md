# 07 — Attachment Slots and Accessories

## Slot Naming Convention

Slots are represented as **Empty objects** (type `PLAIN_AXES`) in the Blender armature, parented to the relevant bone.

### Naming Pattern

```
SOCKET_<SIDE>_<PART>_<SLOT_TYPE>
```

| Token | Values | Notes |
|---|---|---|
| `SIDE` | `L`, `R`, `C` | Left, Right, Centre |
| `PART` | `ARM`, `SHOULDER`, `BACK`, `HIP`, `HEAD` | Body region |
| `SLOT_TYPE` | `WEAPON`, `SHIELD`, `UTILITY`, `MOUNT` | What can attach |

### Defined Slots (MVP)

| Slot Name | Parent Bone | Description |
|---|---|---|
| `SOCKET_L_ARM_WEAPON` | `mixamorig:LeftHand` | Left hand weapon |
| `SOCKET_R_ARM_WEAPON` | `mixamorig:RightHand` | Right hand weapon |
| `SOCKET_L_SHOULDER_MOUNT` | `mixamorig:LeftShoulder` | Left shoulder launcher |
| `SOCKET_R_SHOULDER_MOUNT` | `mixamorig:RightShoulder` | Right shoulder launcher |
| `SOCKET_C_BACK_MOUNT` | `mixamorig:Spine2` | Backpack / jet pack |
| `SOCKET_C_BACK_UTILITY` | `mixamorig:Spine1` | Utility (ammo box, etc.) |

---

## Accessory Categories

| Category | Slot Types | Examples |
|---|---|---|
| **Heavy Gun** | `WEAPON` | Gatling, rocket launcher |
| **Light Gun** | `WEAPON` | Pistol, SMG |
| **Blade Weapon** | `WEAPON` | Sword, axe, heat blade |
| **Jet Pack** | `MOUNT` (back) | Single/dual thruster pack |
| **Shield** | `SHIELD` | Riot shield, energy shield |

Accessories are submitted as FBX files following the same asset spec (materials, transforms, naming) but with `PartCategory = <AccessoryCategory>` (e.g. `HeavyGun_v001.fbx`).

---

## Transform Conventions

Each socket Empty defines the **attachment transform**:

| Property | Convention |
|---|---|
| **Origin** | Attachment point on the body |
| **+X** | Right (weapon barrel direction for arm weapons) |
| **+Y** | Up (away from body surface) |
| **-Z** | Forward (same as mech forward) |
| **Scale** | 1.0 (accessories are authored at world scale) |

The accessory FBX root is placed at origin. On attachment, the accessory's root transform is multiplied by the socket's world transform.

---

## Rules: Which Slots Exist on Which Parts

Slots are **defined on the armature** (not per-part), but validation enforces that a part's FBX must not delete or move slots associated with its bone set.

| Part Category | Must Preserve Slots |
|---|---|
| LeftArm | `SOCKET_L_ARM_WEAPON` |
| RightArm | `SOCKET_R_ARM_WEAPON` |
| Torso | `SOCKET_L_SHOULDER_MOUNT`, `SOCKET_R_SHOULDER_MOUNT`, `SOCKET_C_BACK_MOUNT`, `SOCKET_C_BACK_UTILITY` |
| Head | _(none defined in MVP)_ |
| Legs | _(none defined in MVP)_ |

### Validation Rule: `SOCKET_PRESERVED`

- The part's FBX must contain all sockets listed for that part category.
- Socket transforms must be within tolerance of the template (position ±0.01 m, rotation ±1°).
- Missing or moved sockets → validation failure.

---

## Preview Integration

In the preview render:
1. All sockets are shown as small marker cubes (colour-coded by type).
2. If the artist toggles an accessory category ON:
   - The tool looks up the latest blessed accessory FBX for that category.
   - It is imported and snapped to the matching socket.
3. Multiple accessories can be active simultaneously (e.g. Heavy Gun + Jet Pack).

---

## Metadata

Each accessory submission includes metadata specifying compatible slot types:

```json
{
  "part_category": "HeavyGun",
  "compatible_slots": ["WEAPON"],
  "held_hand": "R",
  "version": "v001"
}
```

This allows the UI to filter which accessories can go on which slots.
