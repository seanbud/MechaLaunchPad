# 05 — MechaLaunchPad UI Spec (PySide6)

## Window Layout

```
┌──────────────────────────────────────────────────────┐
│  MechaLaunchPad                            [—][□][×] │
├──────────────────────────────────────────────────────┤
│  [Export Template] [Import/Validate] [Preview]       │
│  [Publish]         [CI Status]                       │
├──────────────────────────────────────────────────────┤
│                                                      │
│                   Tab Content Area                   │
│                                                      │
│                                                      │
├──────────────────────────────────────────────────────┤
│  Status Bar: "Ready" | logged in as artist@studio    │
└──────────────────────────────────────────────────────┘
```

- Fixed tab bar across the top.
- Status bar at the bottom showing connection state and user identity.
- Minimum window size: 900 × 650 px.

---

## Tab Definitions

### 1. Export Template

**Purpose**: Generate a template FBX for a chosen part category.

```
┌─────────────────────────────────────────┐
│  Part Category:  [ LeftArm       ▼ ]   │
│                                         │
│  Output Directory:  [____________] [📁] │
│                                         │
│  [ Export Template ]                    │
│                                         │
│  Log:                                   │
│  ┌─────────────────────────────────┐    │
│  │ (output messages appear here)   │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**State machine**:
- `IDLE` → user selects category → `READY`
- `READY` → click Export → `EXPORTING` (spinner)
- `EXPORTING` → success → `DONE` (show file path) | error → `ERROR` (show message)

---

### 2. Import / Validate

**Purpose**: Import an authored FBX and run local preflight checks.

```
┌────────────────────────────────────────────────────┐
│  Asset File:  [________________________] [📁]      │
│  Detected Part: LeftArm (auto)                     │
│                                                    │
│  [ Run Preflight ]                                 │
│                                                    │
│  Results:                                          │
│  ┌──────────────────────────────────────────┐      │
│  │ ✅ NAMING_VALID        File name OK     │      │
│  │ ✅ BONE_SET_VALID      All meshes on    │      │
│  │                        allowed bones    │      │
│  │ ❌ MAT_NAME_MISMATCH   "M_Metall" not  │      │
│  │                        in approved set  │      │
│  │ ✅ TRI_COUNT_OK        12,340 / 15,000  │      │
│  └──────────────────────────────────────────┘      │
│                                                    │
│  Summary: 1 error, 0 warnings — fix before publish │
└────────────────────────────────────────────────────┘
```

**Widgets**:
- `QTreeWidget` or `QListWidget` with icons for pass/fail per rule.
- Clicking a row expands detail text.

**State machine**:
- `IDLE` → file selected → `FILE_LOADED`
- `FILE_LOADED` → click Run → `VALIDATING`
- `VALIDATING` → done → `RESULTS_SHOWN` (pass/fail per rule)

---

### 3. Preview

**Purpose**: Show a stitched full mech rendered image.

```
┌────────────────────────────────────────────────────┐
│  ┌────────────────────────────────┐  Part Selector │
│  │                                │  ┌───────────┐ │
│  │                                │  │ LeftArm ▼ │ │
│  │      [Rendered Mech Image]     │  │ Head    ▼ │ │
│  │                                │  │ Torso   ▼ │ │
│  │                                │  │ Legs    ▼ │ │
│  │                                │  └───────────┘ │
│  │                                │                │
│  └────────────────────────────────┘  Accessories   │
│                                      ☐ Heavy Gun   │
│                                      ☐ Jet Pack    │
│  [ Re-render ]                                     │
└────────────────────────────────────────────────────┘
```

**MVP**: A static rendered image from Blender headless. Re-render button triggers a new render.

**Future**: Embedded OpenGL viewport with orbit controls.

---

### 4. Publish

**Purpose**: Commit and push the validated asset to GitLab.

```
┌─────────────────────────────────────────┐
│  Asset: LeftArm_v001.fbx                │
│  Part:  LeftArm                         │
│  Version: [ v001 ]  (auto-incremented)  │
│                                         │
│  Commit Message:                        │
│  ┌─────────────────────────────────┐    │
│  │ Initial left arm submission     │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Preflight: ✅ All checks passed        │
│                                         │
│  [ Publish ]  (disabled if errors)      │
│                                         │
│  Progress:                              │
│  ┌─────────────────────────────────┐    │
│  │ Committing... Pushing...        │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**State machine**:
- `IDLE` (no asset loaded)
- `READY` (asset loaded + preflight passed)
- `PUBLISHING` (git add/commit/push in progress)
- `PUBLISHED` (success — show commit hash, pipeline link)
- `ERROR` (push failed — show message)

---

### 5. CI Status

**Purpose**: Monitor GitLab pipeline results.

```
┌────────────────────────────────────────────────────┐
│  Latest Pipelines                      [ Refresh ] │
│  ┌──────────────────────────────────────────┐      │
│  │ #42  LeftArm v001  ✅ passed   2 min ago │      │
│  │ #41  LeftArm v001  ❌ failed   5 min ago │      │
│  └──────────────────────────────────────────┘      │
│                                                    │
│  Selected: #41                                     │
│  ┌──────────────────────────────────────────┐      │
│  │ Stage: validate    ❌ FAILED             │      │
│  │ Errors:                                  │      │
│  │   MAT_NAME_MISMATCH: "M_Metall"         │      │
│  │   not in approved material set.          │      │
│  │                                          │      │
│  │ Stage: unity_ingest  ⏭ SKIPPED           │      │
│  │ Stage: report        ⏭ SKIPPED           │      │
│  └──────────────────────────────────────────┘      │
│                                                    │
│  [ View Full Log ]  [ Download Artifacts ]         │
└────────────────────────────────────────────────────┘
```

**Key widgets**:
- `QListWidget` for pipeline list (sortable by date).
- Detail panel showing per-stage status.
- Buttons to open GitLab in browser or download artifacts.

---

## State Transitions (global)

```
Export Template ──► artist works in Blender ──► Import/Validate
                                                     │
                                              pass? ─┤
                                              no  ◄──┘ (fix & re-import)
                                              yes
                                               │
                                               ▼
                                            Preview
                                               │
                                               ▼
                                            Publish ──► CI Status
                                                          │
                                                     pass? ─┤
                                                     no  ◄──┘ (diagnose)
                                                     yes ──► done ✅
```

---

## Key PySide6 Components

| Widget | Qt Class | Notes |
|---|---|---|
| Tab bar | `QTabWidget` | 5 tabs |
| File picker | `QFileDialog` | Native dialog |
| Validation list | `QTreeWidget` | Icons + expandable detail |
| Preview image | `QLabel` with `QPixmap` | Scaled to fit |
| Log panel | `QPlainTextEdit` (read-only) | Monospace font |
| Progress | `QProgressBar` or spinner `QMovie` | Indeterminate for git ops |
| Status badge | Custom `QLabel` with coloured background | ✅ green / ❌ red / ⏳ yellow |
