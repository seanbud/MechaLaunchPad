# 00 — MechaLaunchPad Overview

## Pitch

MechaLaunchPad is a local PySide6 desktop tool that demonstrates an **end-to-end modular content pipeline**: artists pick a mech part category, author meshes in Blender against a canonical template rig, validate locally, then publish to GitLab where CI re-validates, imports into Unity, generates prefabs, and renders thumbnails — all with live status feedback inside the app. It proves pipeline guardrails, modular content workflows, and build-to-ship automation in one cohesive demo.

> [!NOTE]
> **Architecture Split**:
> - **The App (MechaLaunchPad)**: Hosted on **GitHub**. This is the source code for the tool itself.
> - **The Assets (MechAssets)**: Hosted on **GitLab**. This is where your validated FBX files are published to trigger the automated Unity ingestion pipeline.

---

## System Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    MechaLaunchPad (PySide6)                   │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ Template  │  │ Import / │  │ Preview  │  │  Publish /  │  │
│  │  Export   │  │ Validate │  │ Sandbox  │  │  CI Status  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬──────┘  │
└───────┼──────────────┼─────────────┼───────────────┼─────────┘
        │              │             │               │
        ▼              ▼             │               ▼
 ┌─────────────┐ ┌───────────┐      │       ┌──────────────┐
 │  Blender    │ │  Local    │      │       │   GitLab     │
 │  (Artist)   │ │  Preflight│      │       │   Repo +     │
 │             │ │  Checks   │      │       │   CI/CD      │
 └─────────────┘ └───────────┘      │       └──────┬───────┘
                                    │              │
                                    │    ┌─────────▼────────┐
                                    │    │  CI Pipeline      │
                                    │    │  validate →       │
                                    │    │  unity_ingest →   │
                                    │    │  report           │
                                    │    └─────────┬────────┘
                                    │              │
                                    │    ┌─────────▼────────┐
                                    └───▶│  Unity Project    │
                                         │  (prefabs,       │
                                         │   thumbnails)    │
                                         └──────────────────┘
```

---

## MVP vs Nice-to-Have

| Category | MVP (one-day build) | Nice-to-Have |
|---|---|---|
| **Part types** | LeftArm only | Head, Torso, Legs, etc. |
| **Template export** | Full suit FBX with canonical rig | Per-part optimised templates |
| **Local validation** | Naming, bone set, tri count | Materials, texture size, UV overlap |
| **Preview** | Embedded OpenGL viewport (Interactive) | High-fidelity Unity renders |
| **Publishing** | Commit + push via GitPython | Branch + MR workflow |
| **CI** | Validate stage + stubbed Unity stage | Full Unity batchmode import |
| **CI status** | Poll pipeline status & show pass/fail | Stream logs, deep-link to jobs |
| **Unity ingestion** | Stubbed (script exists, runs in CI) | Full prefab + thumbnail gen |
| **Accessories** | Data model defined, no UI toggle | Live slot preview |
| **Auth** | `.env` PAT | OS keyring / OAuth |
