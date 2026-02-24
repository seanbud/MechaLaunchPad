# 02. Architecture and State

## Technical Stack
MechaLaunchPad is a standalone desktop application built using Python and the PySide6 (Qt) framework.

## Directory Structure
The application follows a standard MVC (Model-View-Controller) inspired design pattern:

```text
MechaLaunchPad/
├── app/
│   ├── ui/               # The "View" - PySide6 widgets, windows, and tabs
│   │   ├── main_window.py
│   │   ├── ci_tab.py
│   │   └── ...
│   ├── services/         # The "Controller" - Business logic, Git ops, API polling
│   │   ├── gitlab_service.py
│   │   └── state_manager.py
│   ├── core/             # The "Model" - Global config, resource tokens, styling
│   │   └── resources.py
│   └── __main__.py       # Application entry point
├── docs/                 # Developer documentation
└── scripts/              # Setup tools
```

## Persistent State Management (`StateManager`)
Real desktop apps expect history. If a user closes the launcher, they shouldn't lose track of their running CI pipelines or recent submissions.

We solve this using the `StateManager` singleton (`app/services/state_manager.py`).

- **How it works:** It maintains a local `session_state.json` file inside the `app/data/` directory.
- **What it tracks:**
    1. `validated_parts`: The history of which FBX categories the user has successfully run through the local "Validate" tab.
    2. `ci_tracking`: A list of all branch submissions (e.g., `submit/RightArm/v010`) that have been published to GitLab.
- **Hydration on Boot:** When `MainWindow` boots up (`app/ui/main_window.py`), it reads the state. If it finds historical CI jobs in the JSON list, it instantly regenerates a dedicated `CIJobCard` for each one and spawns background API workers to discover their final states.
