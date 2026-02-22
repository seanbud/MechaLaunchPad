# MechaLaunchPad

MechaLaunchPad is a local PySide6 desktop tool that demonstrates an **end-to-end modular content pipeline**. It allows artists to author mech parts in Blender against a canonical template rig, validate them locally, preview those parts interactively on a 3D animated robot, and then publish them to a CI/CD pipeline.

![App Screenshot Placeholder](docs/app-icon.png)

## Architecture Split

To keep the pipeline clean and flexible, the architecture is split into two repositories:

1. **The App Source (MechaLaunchPad)**: This GitHub repository. It contains the Python source code for the PySide6 application, the local validation rules, the headless Blender extraction scripts, and the interactive OpenGL preview logic.
2. **The Asset Pipeline (MechAssets)**: A target GitLab repository (to be configured). This is the destination for validated `.fbx` files. Pushing to this repository triggers automated GitLab CI/CD pipelines that ingest the models into Unity, bake prefabs, and generate thumbnails.

## Features (MVP Phase 1 Complete)

*   **Template Export**: Export a clean, versioned `BasicTemplate.blend` rig directly from the app to ensure your custom parts align perfectly.
*   **Local Validation**: Headless Blender processes run pre-flight checks on your authored FBX files, validating naming conventions, bone parenting hierarchies, and triangle counts against a defined `part_registry.json`.
*   **Interactive 3D Preview**: A custom-built PySide6 `QOpenGLWidget` allows you to assemble and preview your validated parts in real-time. It features:
    *   Interactive camera controls (Orbit, Pan, Zoom).
    *   Accurate coordinate space mapping (Blender Z-up to OpenGL Y-up).
    *   Real-time playback of the canonical Idle animation (30 FPS).
    *   Limb-swapping UI to toggle between default robot parts and your custom meshes.

## Setup & Running Locally

1.  **Requirements**: Ensure you have Python 3.11+ and Blender 4.5 installed.
2.  **Environment**: Create a virtual environment and install the dependencies:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Run**: Launch the application using the provided batch script:
    ```bash
    .\run_app.bat
    ```

## Development State

Currently, the local validation and interactive preview systems are fully functional. The next major phase of development will focus on the **Publishing Flow** (GitPython integration) to push validated assets from this app directly to the GitLab Asset Repo and poll the CI pipeline status. See `docs/00_OVERVIEW.md` for the full design documentation.
