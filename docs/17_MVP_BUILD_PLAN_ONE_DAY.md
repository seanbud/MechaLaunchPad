# 17 — MVP Build Plan (One Day)

## Goal

By end of day, have a working demo that shows the full pipeline loop: **export template → author in Blender → import & validate locally → preview → publish to GitLab → CI validates → status shown in app**.

---

## Time-Boxed Schedule

| Block | Time | Deliverable |
|---|---|---|
| **1. Scaffold** | 0:00 – 1:00 | Project structure, config files, dependencies |
| **2. Validation module** | 1:00 – 3:00 | All local preflight rules + CLI runner |
| **3. PySide6 shell** | 3:00 – 4:30 | Main window, 5 tabs (layout only) |
| **4. Template export** | 4:30 – 5:30 | Export Template tab wired to Blender headless |
| **5. Import + validate UI** | 5:30 – 6:30 | Import tab wired to validation module |
| **6. Git + publish** | 6:30 – 7:30 | GitPython commit/push, Publish tab |
| **7. CI pipeline** | 7:30 – 8:00 | `.gitlab-ci.yml` with validate stage + stub unity |
| **8. CI status tab** | 8:00 – 8:30 | Poll API, display pass/fail |
| **9. Preview (basic)** | 8:30 – 9:00 | Blender headless render of single part |
| **10. Polish + demo prep** | 9:00 – 10:00 | End-to-end test, fix bugs, prep demo script |

---

## What to Stub

| Component | Stub Strategy |
|---|---|
| **Unity ingest** | CI stage exists but runs a Python stub that creates placeholder outputs |
| **Thumbnail render** | Stubbed 1×1 PNG or use Blender render as stand-in |
| **Accessories** | Data model in `part_registry.json`; no UI toggle |
| **Multi-part preview** | Render only the submitted part (no stitching in MVP) |
| **`latest.json` updates** | Manual or skipped; tool always reads from file system |
| **OS keyring auth** | Use `.env` only |
| **Branch merge** | Manual merge in GitLab UI; no auto-merge |

---

## What Must Be Real

| Component | Why |
|---|---|
| **Validation rules** | Core value proposition — must actually catch errors |
| **FBX parsing** | Needs to read real FBX data (via Blender headless) |
| **PySide6 UI** | Must look like a real tool, not a terminal |
| **Git push** | Must actually push to GitLab and trigger CI |
| **CI validate stage** | Must actually run rules and produce `validation_report.json` |
| **CI status polling** | Must show real pipeline status from GitLab API |

---

## Interview Demo Script

### Setup (before demo)

1. GitLab repo created with `.gitlab-ci.yml` and CI runner active.
2. `.env` configured with PAT.
3. `BasicTemplate.blend` and pre-authored `LeftArm_v001.fbx` ready.
4. Blender installed on demo machine.

### Demo Flow (5–7 minutes)

1. **"Here's the problem"** (30 s)
   - "Artists submit mech parts — we need guardrails, automation, and feedback."

2. **Show the tool** (30 s)
   - Open MechaLaunchPad. Walk through the tabs.

3. **Export template** (1 min)
   - Select LeftArm → Export → show the generated FBX.
   - "This contains the full rig + animations. Artists only replace limb meshes."

4. **Show Blender authoring** (1 min)
   - Open pre-authored file. Point out: rigid parenting, approved materials, guide meshes locked.

5. **Import + validate — failure** (1 min)
  - Import a deliberately broken FBX (exceeds triangle limit).
  - Show the error: `TRI_COUNT` failure with fix hint.
  - "Publish button is disabled — can't ship broken assets."

6. **Import + validate — success** (30 s)
   - Import the correct FBX. All green. Publish enabled.

7. **Publish** (1 min)
   - Click Publish. Watch git push happen.
   - Switch to CI Status tab. Pipeline appears.
   - Wait ~30 s for validate stage to pass (or use a pre-recorded pipeline).

8. **CI results** (30 s)
   - Show green pipeline. Show validation report artifact.
   - "In production, this would also generate a Unity prefab and thumbnail."

9. **Architecture recap** (30 s)
   - "Local checks match CI rules — same codebase. CI is source of truth."
   - "Designed to scale: add Head, Torso, Legs — just add bone sets to config."

---

## Risk Mitigations

| Risk | Mitigation |
|---|---|
| Blender headless is slow | Pre-parse the demo FBX; cache results |
| GitLab CI runner not available | Record a video of CI running as backup |
| Network issues | Have `validation_report.json` artifacts pre-downloaded |
| FBX parsing edge cases | Test with the exact demo files beforehand |
