# 04. Future Architecture Extensions

While the application currently fulfills the MVP goal of safely bridging Artists to GitLab CI pipelines, the ultimate architecture demands end-to-end automation into the final game engine.

## The Roadmap

### 1. Robust Local Preflighting
Currently, the "Validate" tab performs mocked checks. Extension requires hard-coding `fbx` parsing logic (likely via Python bindings or headless Blender calls) to locally verify scale, normals, and triangle limits on the user's machine *before* permitting a network push.

### 2. Unity Headless Ingestion (The Server Side)
The current `.gitlab-ci.yml` has a mocked "deployment" step. The end vision requires a dedicated CI runner (or a webhook to a deployment server) that:
1. Pulls the accepted `submit/` branch.
2. Boots Unity in purely `-batchmode -nographics`.
3. Auto-imports the `.fbx`.
4. Executes an Editor script that converts the FBX into a configured Unity `Prefab` with proper collision layers, materials, and attachment points hooked up.
5. Puts that Prefab into an Addressables bundle or pushes it directly into the `main` game repository.

### 3. Reviewer Routing
Currently, all pipelines auto-merge or sit independently. Extension requires the `.gitlab-ci.yml` to trigger a Merge Request (MR) upon successful testing, assigning it automatically to a Lead Technical Artist for visual sign-off via a web viewer or Slack notification before integrating into `main`.
