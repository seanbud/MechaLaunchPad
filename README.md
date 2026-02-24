# MechaLaunchPad

PySide desktop app, providing an **end-to-end 3d content pipeline** for a modular robot mech game.

Artists use this to generate their template files, to upload and locally validate new assets, preview those parts interactively on a 3D animated robot, and then publish them to the Gitlab CI/CD pipeline.

The pipeline then generates a thumbnail, and pushes it to a Unity repo + bakes a prefab (WIP).

<img width="256" height="256" alt="app-icon" src="https://github.com/user-attachments/assets/bba14f66-430f-49e2-9cf5-a4aff4075853" />

<img width="333" height="400" alt="image" src="https://github.com/user-attachments/assets/7fd72ee7-0442-4328-8ade-131037fa3f30" />

## Architecture Split

To keep the pipeline clean and flexible, the architecture is split into two repositories:

1. **The App Source (MechaLaunchPad)**: This GitHub repository. It contains the Python source code for the PySide application, the local validation rules, the headless Blender extraction scripts, and the interactive OpenGL preview logic.
2. **The Asset Pipeline (MechAssets)**: A target GitLab repository. This is the destination for validated `.fbx` files. Pushing to this repository triggers automated GitLab CI/CD pipelines that ingest the models into Unity, bake prefabs, and generate thumbnails.

## Video Demo

https://github.com/user-attachments/assets/756d6783-948e-4f31-8448-ac84eee9f05b

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
