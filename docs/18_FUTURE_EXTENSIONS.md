# 18 — Future Extensions

## Multi-Part Browser

- Gallery view of all submitted parts, filterable by category, author, version, and tags.
- Thumbnail grid powered by `latest.json` + CI-rendered previews.
- Drag-and-drop parts into the preview to compose a custom mech build.
- "Blessed" vs "in-review" badges.

---

## Perforce Integration (Optional)

- Add a Perforce backend alongside Git for studios that use P4.
- Abstract VCS operations behind a `VersionControl` interface:
  ```python
  class VersionControl(ABC):
      def checkout(self, path): ...
      def submit(self, files, message): ...
      def get_latest(self, path): ...
  ```
- Implement `GitBackend` and `P4Backend`.
- Select backend via config: `"vcs": "git"` or `"vcs": "perforce"`.

---

## Richer Validation

| Rule | Description |
|---|---|
| **Material validation** | Enforce approved material set (M_Metal, M_Plastic, etc.) and check for empty slots |
| **UV overlap detection** | Flag overlapping UVs that would bake incorrectly |
| **Texture size enforcement** | Reject textures > 2048 × 2048 or non-power-of-two |
| **Vertex colour check** | Warn if unexpected vertex colour channels exist |
| **LOD chain validation** | Ensure LOD0/LOD1/LOD2 exist and tri counts decrease |
| **Animation integrity** | Verify keyframe counts match template animations |
| **Mesh watertight check** | Warn if mesh has open edges (optional, cosmetic) |

---

## Notifications

- **Slack / Discord webhook** on CI completion (pass or fail).
- **Email summary** with validation report + thumbnail attachment.
- **In-app toast** when a monitored pipeline completes (background polling).

---

## Asset Registry / Database

Replace file-system-based `latest.json` with a lightweight database:

- **SQLite** for local tool state.
- **GitLab Package Registry** or a simple REST service for cross-team discovery.
- Schema: parts table, versions table, validation results table, accessory compatibility table.

---

## Interactive 3-D Preview

Replace Blender headless render with an embedded viewport:

- **Qt3D** or **pygfx** widget inside PySide6.
- Orbit, pan, zoom.
- Toggle wireframe / shaded / material preview.
- Play animations.
- Live accessory attach/detach.

---

## Additional Part Categories

Expand `part_registry.json`:

```json
{
  "LeftArm": { ... },
  "RightArm": { ... },
  "Head": { "bones": ["mixamorig:Head", "mixamorig:Neck", ...], "max_tris": 12000 },
  "Torso": { "bones": ["mixamorig:Spine", "mixamorig:Spine1", ...], "max_tris": 25000 },
  "Legs": { "bones": ["mixamorig:LeftUpLeg", "mixamorig:LeftLeg", ...], "max_tris": 20000 },
  "BackPack": { "bones": ["mixamorig:Spine2"], "max_tris": 8000 }
}
```

---

## Merge Request Workflow

Instead of direct push-to-branch:

1. Tool creates a Merge Request via GitLab API.
2. Automated approval by CI bot on pipeline success.
3. Manual approval gate for senior tech artists (configurable).
4. Auto-merge to `main` after approval.

---

## Variant / Skin System

- Support multiple visual variants per part (e.g. `LeftArm_Stealth_v001`, `LeftArm_Desert_v001`).
- Variants reuse the same bone set and sockets but swap material parameter values.
- Preview system allows variant switching.

---

## Batch Submission

- Import multiple parts at once.
- Run validation on all, show aggregate report.
- Publish all passing parts in a single commit.

---

## Analytics Dashboard

- Track submission frequency, validation failure rates by rule, time-to-fix.
- Identify common artist mistakes to improve documentation or templates.
- Display in a separate Admin tab or external dashboard (Grafana, etc.).

---

## CI Performance

- Cache Blender/Unity Docker images.
- Parallelize per-part validation if multiple parts are submitted.
- Use GitLab parent-child pipelines for multi-part submissions.
