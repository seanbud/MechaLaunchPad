# 01. Artist Workflow and App Goals

## The Core Vision
MechaLaunchPad is designed to bridge the gap between 3D Artists (using tools like Blender, Maya, or ZBrush) and version-controlled game engines (like Unity). 

Before this tool, artists either had to learn the dense technicalities of `git` CLI, branching strategies, and remote pipelines, or rely on a technical artist to ferry their files into the game. MechaLaunchPad removes this friction. It provides a simple, standalone desktop GUI where an artist can select their 3D `.fbx` part, click a button, and trust that the asset is safely versioned, validated, and processed by the CI/CD pipeline.

## The Intended User Experience

The application is split into three main tabs that dictate the workflow natively:

### 1. Validate (The Ingestion Point)
- The artist selects the specific mechanical part category they have been working on (e.g., `RightArm`).
- They select the raw `.fbx` export file from their desktop.
- **Goal:** The application instantly performs local pre-flight checks (currently mocked) to ensure the asset meets internal standards (e.g., triangle limits, naming conventions) before wasting time uploading to a server.
- **State Change:** If the file passes, the app unlocks the *Preview* and *Publish* workflows.

### 2. Preview (The Validation Point)
- The artist can visually inspect the asset they just selected against a mocked 3D environment or UI placeholder. 
- **Goal:** Provide confidence that the correct file was selected and it looks right in context before committing it to the repository.

### 3. Publish & CI Tracking (The Submission Point)
- The artist adds a brief plain-text description of what changed (e.g., "Adjusted shoulder joint topology") and clicks `Publish`.
- **The Magic:** Behind the scenes, the app automatically clones the remote repository, creates a new structurally sound branch (e.g., `submit/RightArm/v001`), stages the FBX, commits, and pushes to GitLab. The artist never types a single git command.
- **CI Status UI:** The artist is then routed to the CI feed. A new `CIJobCard` appears for their specific part submission.
- **Self-Healing Polling:** The app automatically spawns a background thread that pings the GitLab API. The UI card visually updates from ⏳ Pending to 🔄 Running to ✅ Success (or ❌ Error). 
- **Goal:** The artist can literally leave this window open on a second monitor while they go back to modeling, immediately tracking if their part successfully made it through the automated engine tests or if it was rejected for a technical reason.
